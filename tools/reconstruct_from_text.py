#!/usr/bin/env python3
"""
Reconstruct a project tree from multipart text archive(s).

Usage:
    python tools/reconstruct_from_text.py mini_basic_text_dist_part*.txt -o my_tree
    python tools/reconstruct_from_text.py dist/mini_basic_text_dev_part*.txt -o my_dev --verify

    # or with output directory
    python tools/reconstruct_from_text.py *.txt --output my_mini_basic/

The format it understands (real markers start at column 0 with no leading spaces):
    ===== BEGIN FILE: some/relative/path.py =====
    <exact file content here, including indentation>
    ===== END FILE =====

    Special handling: If a source file contains lines that look exactly like markers,
    they are escaped in the archive text as "ARCHIVE-MARKER-ESCAPED: ===== ..."
    and automatically restored on reconstruction. This prevents truncation.

Modular runtime check (--verify): ensures mini_basic/runtime.py plus
mini_basic/runtime_parts/* are present and importable.
"""

import sys
import re
import argparse
import glob as _glob
import subprocess
from pathlib import Path


BEGIN_RE = re.compile(r'^=====+\s*BEGIN FILE:\s*(.+?)\s*={5,}\s*$', re.IGNORECASE)
END_RE   = re.compile(r'^=====+\s*END FILE\s*={5,}\s*$', re.IGNORECASE)

MARKER_ESCAPE_PREFIX = "ARCHIVE-MARKER-ESCAPED: "

def _unescape_content(content: str) -> str:
    """Restore lines that were escaped because they matched marker patterns."""
    lines = []
    for line in content.splitlines(keepends=True):
        if line.startswith(MARKER_ESCAPE_PREFIX):
            lines.append(line[len(MARKER_ESCAPE_PREFIX):])
        else:
            lines.append(line)
    return ''.join(lines)


def parse_text_archive(text: str):
    """Yield (rel_path, content) pairs."""
    lines = text.splitlines(keepends=True)
    i = 0
    current_path = None
    current_lines = []

    while i < len(lines):
        line = lines[i]
        # Use raw line (no .strip()) so that indented examples in docs/docstrings
        # do not accidentally create fake files like "path/to/file.py".
        # Real markers written by create_text_archive.py start at column 0.
        m = BEGIN_RE.match(line)
        if m:
            if current_path is not None:
                # previous file was not closed properly
                yield current_path, ''.join(current_lines)
            current_path = m.group(1).strip()
            current_lines = []
            i += 1
            continue

        if END_RE.match(line.strip()):
            if current_path is not None:
                raw_content = ''.join(current_lines)
                content = _unescape_content(raw_content)
                content = content.rstrip('\n') + '\n' if content else ''
                yield current_path, content
            current_path = None
            current_lines = []
            i += 1
            continue

        if current_path is not None:
            current_lines.append(line)
        i += 1

    # handle last unclosed file (rare)
    if current_path is not None and current_lines:
        raw_content = ''.join(current_lines)
        yield current_path, _unescape_content(raw_content)


REQUIRED_MODULAR = [
    "mini_basic/runtime.py",
    "mini_basic/runtime_parts/__init__.py",
    "mini_basic/runtime_parts/core.py",
    "mini_basic/runtime_parts/execution.py",
    "mini_basic/runtime_parts/expr.py",
    "mini_basic/__init__.py",
    "mini_basic/__main__.py",
    "mini_basic.py",
]


def reconstruct(files, output_dir: Path, dry_run=False):
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []

    for txt_path in files:
        print(f"Reading {txt_path} ...")
        text = Path(txt_path).read_text(encoding='utf-8', errors='replace')
        for rel, content in parse_text_archive(text):
            target = output_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if dry_run:
                print(f"  [dry] would write {rel} ({len(content)} bytes)")
            else:
                target.write_text(content, encoding='utf-8')
                written.append(rel)
                print(f"  wrote {rel}")

    print(f"\nReconstructed {len(written)} files into {output_dir}")
    return written


def verify_modular_tree(output_dir: Path, *, smoke_import: bool = True) -> int:
    """Return 0 if modular runtime looks complete; 1 on failure."""
    missing = []
    for rel in REQUIRED_MODULAR:
        if not (output_dir / rel).is_file():
            missing.append(rel)
    if missing:
        print("VERIFY FAIL: missing modular runtime files:")
        for m in missing:
            print(f"  - {m}")
        return 1

    parts = output_dir / "mini_basic" / "runtime_parts"
    mixin_py = list(parts.glob("*.py")) if parts.is_dir() else []
    print(f"VERIFY OK: modular runtime present ({len(mixin_py)} runtime_parts modules)")

    if smoke_import:
        code = (
            "from mini_basic import BASICInterpreter, main; "
            "BASICInterpreter(); print('import-ok')"
        )
        try:
            proc = subprocess.run(
                [sys.executable, "-c", code],
                cwd=str(output_dir),
                capture_output=True,
                text=True,
                timeout=60,
            )
        except Exception as exc:
            print(f"VERIFY WARN: import smoke could not run: {exc}")
            return 0
        if proc.returncode != 0 or "import-ok" not in (proc.stdout or ""):
            print("VERIFY FAIL: Python import smoke failed")
            if proc.stdout:
                print(proc.stdout)
            if proc.stderr:
                print(proc.stderr)
            return 1
        print("VERIFY OK: import smoke")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Rebuild project from text archive parts.")
    parser.add_argument(
        "parts",
        nargs="+",
        help="Text part files (mini_basic_text_cli|dist|dev_part*.txt)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="reconstructed_mini_basic",
        help="Output directory (default: reconstructed_mini_basic)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only show what would be done")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="After write, check modular runtime_parts and import BASICInterpreter",
    )
    parser.add_argument(
        "--no-import-smoke",
        action="store_true",
        help="With --verify, only check files on disk (skip Python import)",
    )
    args = parser.parse_args()

    part_files = []
    for p in args.parts:
        matches = _glob.glob(p)
        for m in matches:
            mp = Path(m)
            if mp.is_file():
                part_files.append(mp)

    if not part_files:
        print("No input files found.")
        sys.exit(1)

    # Stable order: part01 before part02
    part_files = sorted(set(part_files), key=lambda p: p.name.lower())

    out_dir = Path(args.output)
    reconstruct(part_files, out_dir, dry_run=args.dry_run)

    if args.verify and not args.dry_run:
        rc = verify_modular_tree(out_dir, smoke_import=not args.no_import_smoke)
        sys.exit(rc)


if __name__ == "__main__":
    main()
