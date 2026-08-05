#!/usr/bin/env python3
"""
Create LLM-friendly multipart text archive(s) from the mini_basic project tree.

Modes:
  --mode cli    Command-line only, no pixel graphics (smallest). Full
                interpreter + CLI samples; omits bbc_font/bbc_graphics,
                pygame demos, games trees, and requirements-display.txt.
                Display backends: terminal (default) and none only.
                  mini_basic/ (runtime + runtime_parts, without pixel gfx),
                  basics/, examples/{mini,mits,museum,bbc}/, documentation/,
                  mini_basic.py / mb.py / README* / FEATURES* / HOWTO /
                  requirements-repl.txt / install.ps1 / CLI_ONLY.txt
  --mode dist   Full curated distribution: everything in cli plus the full
                examples/ tree and requirements-display.txt (pygame optional).
  --mode dev    Everything from dist, plus development-only material:
                  docs/, lib/, scripts/, test/, tools/, utils/, …
                (backup/ is always excluded.)
  --mode both   Write dist + dev archives.
  --mode all    Write cli + dist + dev archives.

Caches (__pycache__, .pytest_cache), junk files, and the tool's own prior
output (old *.txt parts, old minimal zips) are excluded in every mode.

Helper tools (create/reconstruct/install) are always bundled so a
reconstructed tree can re-archive and reinstall itself. Dev-only helpers
(split mixins, dev_install) ship with dist/dev; cli keeps a minimal tool set.

Produces files like:
  dist/mini_basic_text_cli_part01.txt
  dist/mini_basic_text_dist_part01.txt
  dist/mini_basic_text_dev_part01.txt

Each part contains multiple files wrapped with clear markers.
Lines containing marker patterns are escaped to prevent truncation on roundtrip.
All output is pure text. Safe to paste into LLMs.

Usage:
    python tools/create_text_archive.py --mode cli       # command-line only
    python tools/create_text_archive.py                 # dist mode (default)
    python tools/create_text_archive.py --mode dev
    python tools/create_text_archive.py --mode both
    python tools/create_text_archive.py --mode all
    python tools/create_text_archive.py --mode dist --max-chars 150000 --outdir dist
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

# Marker escaping to safely embed files that contain marker-like lines
MARKER_ESCAPE_PREFIX = "ARCHIVE-MARKER-ESCAPED: "


def _escape_content(content: str) -> str:
    """Prefix lines that would match our BEGIN/END markers so they are treated as content."""
    escaped_lines = []
    for line in content.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("=====") and (
            "BEGIN FILE:" in stripped or stripped == "===== END FILE ====="
        ):
            escaped_lines.append(MARKER_ESCAPE_PREFIX + line)
        else:
            escaped_lines.append(line)
    return "".join(escaped_lines)


INCLUDED_FILE_EXTS = {
    ".py",
    ".bas",
    ".bbc",
    ".txt",
    ".md",
    ".toml",
    ".ps1",
    ".cmd",
}

# Helper tools always needed to use an archive (every mode)
EXTRA_TOOLS_CORE = [
    "tools/create_text_archive.py",
    "tools/reconstruct_from_text.py",
    "tools/install.ps1",
]

# Additional helpers for full dist / dev trees
EXTRA_TOOLS_FULL = [
    "tools/reconstruct_runtime_version.py",
    "tools/smart_patch.py",
    "tools/split_runtime_mixins.py",
    "tools/dev_install.ps1",
]

# Paths archived at the tree root even when the live source lives under tools/.
# Reconstruct puts install.ps1 next to archive/ so end-users can run .\install.ps1.
ROOT_SHIPPED_FROM_TOOLS: Dict[str, str] = {
    "install.ps1": "tools/install.ps1",
    "dev_install.ps1": "tools/dev_install.ps1",
}

# Full curated distribution directories.
DIST_DIR_PREFIXES = (
    "mini_basic/",
    "basics/",
    "examples/",
    "documentation/",
)

# CLI-only: interpreter + text samples (no games/graphics/physics/sounds trees).
CLI_DIR_PREFIXES = (
    "mini_basic/",
    "basics/",
    "examples/mini/",
    "examples/mits/",
    "examples/museum/",
    "examples/bbc/",
    "documentation/",
)

# Pixel-graphics stack and demos omitted from CLI trees (terminal/none only).
# display.py stays (TerminalDisplay + NullDisplay); pygame path needs these files.
# features/ is matrix tooling (and hard-imports graphics.py) — not needed to run BASIC.
CLI_EXCLUDED_PATHS = {
    "mini_basic/bbc_font.py",
    "mini_basic/bbc_graphics.py",
    "examples/mini/bbc_graphics_demo.bas",
    "examples/mini/sprites_demo.bas",
    "documentation/feature_matrices/03_graphics.txt",
    "requirements-display.txt",
}

CLI_EXCLUDED_PREFIXES = (
    "mini_basic/features/",
)

# Root-level files for full dist.
DIST_ROOT_FILES = {
    "mini_basic.py",
    "mb.py",
    "HOWTO.md",
    "requirements-display.txt",
    "requirements-repl.txt",
    "install.ps1",
    "dev_install.ps1",
}

# CLI root files: no pygame requirements, no dev_install.
CLI_ROOT_FILES = {
    "mini_basic.py",
    "mb.py",
    "HOWTO.md",
    "requirements-repl.txt",
    "install.ps1",
}

DIST_ROOT_NAME_PREFIXES = ("readme", "features")

# Obsolete monorepo dumps / incomplete stubs (filename only). Never ship these.
# Modular implementation lives under mini_basic/runtime_parts/ — keep those.
OBSOLETE_RUNTIME_BASENAMES = {
    "runtime_from_git_head.py",
    "runtime_trace.py",
    "runtime_modular_skeleton.py",
    "runtime_monolith.py",
    "runtime_old.py",
    "runtime_core.py",
    "runtime_execution.py",
    "runtime_parsing.py",
    "runtime_formatting.py",
    "runtime_graphics.py",
    "runtime_dialect.py",
    "runtime_util.py",
}

# Order preference: facade + mixins first, then package, then samples/docs
PRIORITY = [
    "mini_basic/runtime.py",
    "mini_basic/runtime_parts/",
    "mini_basic/",
    "install.ps1",
    "dev_install.ps1",
    "basics/",
    "examples/",
    "mini_basic.py",
    "mb.py",
    "README",
    "HOWTO",
    "FEATURES",
    "requirements",
    "documentation/",
    "tools/",
]


def _norm(rel_path: str) -> str:
    return rel_path.replace("\\", "/")


def is_obsolete_runtime_artifact(rel_path: str) -> bool:
    """True for discarded monorepo/stub dumps — not for runtime_parts/ or tools."""
    rel = _norm(rel_path)
    lower = rel.lower()
    name = Path(rel).name.lower()

    # Keep the modular mixin package and its docs.
    if lower.startswith("mini_basic/runtime_parts/") or "/runtime_parts/" in lower:
        return False
    if name in ("runtime.py", "runtime_modularization_status.md", "runtime_version_history.md"):
        return False

    # Keep tools that mention "runtime" in the filename (split_runtime_mixins, etc.).
    if lower.startswith("tools/"):
        return False

    if name in OBSOLETE_RUNTIME_BASENAMES:
        return True
    # Any leftover package-root monorepo dump: mini_basic/runtime_*.py except runtime.py
    if lower.startswith("mini_basic/") and name.startswith("runtime_") and name.endswith(".py"):
        return True
    return False


def extra_tools_for_mode(mode: str) -> List[str]:
    if mode == "cli":
        return list(EXTRA_TOOLS_CORE)
    return list(EXTRA_TOOLS_CORE) + list(EXTRA_TOOLS_FULL)


def is_dist_eligible(rel_path: str) -> bool:
    """True if this path belongs in the curated (full) distribution set."""
    rel = _norm(rel_path)
    if "/" not in rel:
        name_lower = rel.lower()
        if rel in DIST_ROOT_FILES:
            return True
        if name_lower.startswith(DIST_ROOT_NAME_PREFIXES):
            return True
        return False
    return rel.startswith(DIST_DIR_PREFIXES)


def is_cli_eligible(rel_path: str) -> bool:
    """True if this path belongs in the command-line-only distribution set.

    Omits the pixel-graphics stack (bbc_font, bbc_graphics, features/graphics)
    and graphics demos. Terminal / --display none work; pygame does not.
    """
    rel = _norm(rel_path)
    lower = rel.lower()
    name = Path(rel).name.lower()

    if lower in {p.lower() for p in CLI_EXCLUDED_PATHS}:
        return False
    if any(lower.startswith(p) for p in CLI_EXCLUDED_PREFIXES):
        return False
    # Explicit excludes for CLI (pygame / media demos stay out)
    if name == "requirements-display.txt":
        return False
    if name == "dev_install.ps1":
        return False
    if name in ("bbc_font.py", "bbc_graphics.py"):
        return False
    if lower.startswith("examples/") and not any(
        lower.startswith(p) for p in CLI_DIR_PREFIXES if p.startswith("examples/")
    ):
        # examples/README.txt is useful for orientation
        if lower == "examples/readme.txt":
            return True
        return False
    # Skip graphics demo basenames even under examples/mini/
    if name in ("bbc_graphics_demo.bas", "sprites_demo.bas"):
        return False
    if name == "03_graphics.txt" and "feature_matrices" in lower:
        return False

    if "/" not in rel:
        if rel in CLI_ROOT_FILES:
            return True
        if name.startswith(DIST_ROOT_NAME_PREFIXES):
            return True
        return False
    return any(lower.startswith(p) for p in CLI_DIR_PREFIXES)


def should_include(rel_path: str, mode: str) -> bool:
    """mode is 'cli', 'dist', or 'dev'."""
    rel = _norm(rel_path)
    p = Path(rel)
    lower_rel = rel.lower()
    name = p.name.lower()

    # Never re-ingest our own generated output (previous text archives, dist/ dir
    # contents). Without this, a directory walk would happily scoop up old
    # mini_basic_text_*_partNN.txt files as "source" and nest them in new archives.
    if lower_rel == "dist" or lower_rel.startswith("dist/") or "/dist/" in lower_rel:
        return False
    if lower_rel == "backup" or lower_rel.startswith("backup/") or "/backup/" in lower_rel:
        # Runtime debugging diffs/history — reconstructable from source, not worth
        # carrying in either archive.
        return False
    if name.startswith("mini_basic_text_") and "part" in name and name.endswith(".txt"):
        return False
    if name.startswith("mini_basic_minimal_") and name.endswith(".zip"):
        return False

    # Caches and junk, excluded in every mode
    if "__pycache__" in lower_rel or ".pytest_cache" in lower_rel:
        return False
    if any(bad in name for bad in [".pyc", ".pyo", ".pyd", ".bak", "~", ".tmp", ".swp", ".swo", ".orig"]):
        return False
    if p.suffix.lower() not in INCLUDED_FILE_EXTS:
        return False
    if is_obsolete_runtime_artifact(rel):
        return False
    if "archimedes live" in name:
        return False
    if name.startswith(".") and name != ".gitignore":
        return False

    tools = set(extra_tools_for_mode(mode))
    if rel in tools:
        return True

    if mode == "cli":
        return is_cli_eligible(rel)
    if mode == "dist":
        return is_dist_eligible(rel)
    # dev mode: dist content plus everything else that passed the filters above
    return True


def collect_files(source_dir: Path, mode: str) -> List[Tuple[str, object]]:
    """Collect files from a directory in a sensible order for the given mode.

    Each entry is (rel_path, Path | str). str is inlined content (e.g. CLI marker).
    """
    files: List[Tuple[str, object]] = []
    for dirpath, _, filenames in os.walk(source_dir):
        for fn in filenames:
            full = Path(dirpath) / fn
            rel = _norm(str(full.relative_to(source_dir)))
            if should_include(rel, mode):
                files.append((rel, full))

    # Make sure helper tools are present even if the walk somehow missed them
    have = {rel for rel, _ in files}
    for tool in extra_tools_for_mode(mode):
        if tool not in have:
            tool_path = source_dir / tool
            if tool_path.exists() and should_include(tool, mode):
                files.append((tool, tool_path))
                have.add(tool)

    # Ship installers at tree root for drop-in install UX (also keep tools/ copies).
    for root_name, src_rel in ROOT_SHIPPED_FROM_TOOLS.items():
        if mode == "cli" and root_name == "dev_install.ps1":
            continue
        src = source_dir / src_rel
        if src.exists() and root_name not in have:
            if mode in ("cli", "dist", "dev"):
                files.append((root_name, src))
                have.add(root_name)

    def sort_key(item: Tuple[str, object]):
        rel = item[0]
        for i, pref in enumerate(PRIORITY):
            if rel.startswith(pref) or rel == pref.rstrip("/"):
                return (i, rel)
        return (99, rel)

    files.sort(key=sort_key)

    # Synthetic marker for CLI trees (no Path on disk required).
    if mode == "cli":
        marker = (
            "mini_basic CLI-only distribution (no pixel graphics)\n"
            "====================================================\n"
            "\n"
            "This tree omits:\n"
            "  - mini_basic/bbc_font.py, bbc_graphics.py (pygame/MOS font stack)\n"
            "  - mini_basic/features/ (matrix tooling)\n"
            "  - games/graphics demos and requirements-display.txt\n"
            "\n"
            "Supported display backends: terminal (default), none\n"
            "Not available: --display pygame  (use the full dist package)\n"
            "\n"
            "Examples:\n"
            "  python -m mini_basic --display none basics/fact.bas\n"
            "  python -m mini_basic examples/mini/hello_args.bas\n"
            "\n"
            "Built with: python tools/create_text_archive.py --mode cli\n"
        )
        files.insert(0, ("CLI_ONLY.txt", marker))

    return files


def make_parts(
    file_list: Sequence[Tuple[str, object]], max_chars: int = 160000
) -> List[List[Tuple[str, str]]]:
    """Split into parts of roughly max_chars."""
    parts: List[List[Tuple[str, str]]] = []
    current: List[Tuple[str, str]] = []
    current_size = 0

    for item in file_list:
        if isinstance(item[1], (str, bytes)):
            content = item[1] if isinstance(item[1], str) else item[1].decode("utf-8", "replace")
            size = len(content)
        else:
            content = item[1].read_text(encoding="utf-8", errors="replace")
            size = len(content)

        header_size = len(f"===== BEGIN FILE: {item[0]} =====\n\n===== END FILE =====\n") + 20

        if current and current_size + size + header_size > max_chars:
            parts.append(current)
            current = []
            current_size = 0

        current.append((item[0], content))
        current_size += size + header_size

    if current:
        parts.append(current)
    return parts


def write_part(part_num: int, mode: str, file_entries: Iterable[Tuple[str, str]], out_path: Path) -> int:
    mode_note = {
        "cli": "CLI-only (no pygame demos/assets; --display none|terminal)",
        "dist": "Full curated distribution (examples + optional pygame)",
        "dev": "Full development tree (tests, scripts, tools)",
    }.get(mode, mode)
    header = f"""# mini_basic {mode} text archive - Part {part_num:02d}
# Generated: {datetime.now().isoformat()}
# Kind: {mode_note}
# Modular runtime: mini_basic/runtime.py (facade) + mini_basic/runtime_parts/* (mixins)
# To reconstruct: python tools/reconstruct_from_text.py this_file.txt [other parts...]
# Or: .\\install.ps1  (-ArchiveKind cli|dist|auto) / .\\dev_install.ps1  (dev)
# Parts under archive/ or dist/
#
# Each file is wrapped with markers like:
# ===== BEGIN FILE: relative/path.py =====   (example)
# <exact content>
# ===== END FILE =====   (example)
#
# IMPORTANT: Copy the content BETWEEN the markers exactly, including all spaces and indentation.
# Lines that would match markers inside files are automatically escaped as
# "ARCHIVE-MARKER-ESCAPED: ===== ..." and restored on reconstruction.

"""
    lines = [header]

    for rel, content in file_entries:
        lines.append(f"===== BEGIN FILE: {rel} =====")
        escaped = _escape_content(content)
        lines.append(escaped.rstrip("\n"))
        lines.append("===== END FILE =====")
        lines.append("")

    text = "\n".join(lines).rstrip() + "\n"
    out_path.write_text(text, encoding="utf-8")
    return len(text)


def build_archive(root: Path, dist: Path, mode: str, max_chars: int) -> List[Path]:
    print(f"\n=== Building '{mode}' archive ===")
    file_list = collect_files(root, mode)
    print(f"  Collected {len(file_list)} files")

    # Sanity: modular runtime must be present for a usable tree
    rels = {rel for rel, _ in file_list}
    required = {
        "mini_basic/runtime.py",
        "mini_basic/runtime_parts/__init__.py",
        "mini_basic/runtime_parts/core.py",
        "mini_basic/__init__.py",
        "mini_basic.py",
    }
    missing = sorted(required - rels)
    if missing:
        print("  ERROR: modular runtime incomplete in archive set:", file=sys.stderr)
        for m in missing:
            print(f"    missing {m}", file=sys.stderr)
        raise SystemExit(2)

    parts = make_parts(file_list, max_chars=max_chars)
    print(f"  Splitting into {len(parts)} part(s) (target ~{max_chars // 1024} KB each)...")

    created: List[Path] = []
    total_bytes = 0
    for i, part in enumerate(parts, 1):
        out = dist / f"mini_basic_text_{mode}_part{i:02d}.txt"
        size = write_part(i, mode, part, out)
        total_bytes += size
        created.append(out)
        print(f"  Wrote {out.name}  ({size / 1024:.1f} KB, {len(part)} files)")

    mixin_count = sum(1 for r in rels if r.startswith("mini_basic/runtime_parts/") and r.endswith(".py"))
    print(
        f"  Total: {len(created)} file(s), {total_bytes / 1024:.1f} KB, "
        f"{len(file_list)} source files ({mixin_count} runtime_parts modules)"
    )
    return created


def modes_from_arg(mode_arg: str) -> List[str]:
    if mode_arg == "both":
        return ["dist", "dev"]
    if mode_arg == "all":
        return ["cli", "dist", "dev"]
    return [mode_arg]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--mode",
        choices=["cli", "dist", "dev", "both", "all"],
        default="dist",
        help=(
            "cli: command-line only (smallest). "
            "dist: full curated release. "
            "dev: full development tree. "
            "both: dist+dev. "
            "all: cli+dist+dev. "
            "Default: dist"
        ),
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=int(os.environ.get("TEXT_ARCHIVE_MAX_CHARS", 155000)),
    )
    parser.add_argument("--outdir", default="dist")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    dist = root / args.outdir
    dist.mkdir(exist_ok=True)

    # Remove stale parts for the modes we are rebuilding so reconstruct
    # never mixes old monorepo-era parts with the new modular set.
    modes = modes_from_arg(args.mode)
    for mode in modes:
        for stale in dist.glob(f"mini_basic_text_{mode}_part*.txt"):
            stale.unlink()
            print(f"Removed stale {stale.name}")

    all_created: List[Path] = []
    for mode in modes:
        created = build_archive(root, dist, mode, args.max_chars)
        all_created.extend(created)

    print("\nDone. Text archives created in", dist)
    print("To reconstruct a tree later:")
    print(
        "  python tools/reconstruct_from_text.py "
        "dist/mini_basic_text_cli_part*.txt -o my_cli --verify"
    )
    print(
        "  python tools/reconstruct_from_text.py "
        "dist/mini_basic_text_dist_part*.txt -o my_tree --verify"
    )
    print("  # or: .\\install.ps1 -ArchiveKind cli|dist|auto")
    print("  # or: .\\dev_install.ps1  (dev parts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
