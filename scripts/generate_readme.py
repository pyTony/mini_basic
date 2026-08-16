#!/usr/bin/env python3
"""Scan the mini_basic tree and regenerate README.md file inventory."""

from __future__ import annotations

import argparse
import ast
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

MARKER = '<!-- AUTO-GENERATED FILE INVENTORY -->'
DEFAULT_ROOT = Path(__file__).resolve().parents[1]

SKIP_DIR_NAMES = {
    '__pycache__',
    '.git',
    '.pytest_cache',
    '.mypy_cache',
    'node_modules',
}

SKIP_FILE_NAMES = {
    '.heartbeat_counter',
    '.sync_counter',
}

SKIP_EXTENSIONS = {
    '.pyc',
    '.pyo',
    '.pyd',
}

# Exact relative-path roles (POSIX-style keys).
EXACT_ROLES: dict[str, str] = {
    'mini_basic.py': 'CLI entry shim; delegates to mini_basic package',
    'display.py': 'Pygame text/graphics display backend for RUN',
    'bbc_graphics.py': 'BBC BASIC graphics primitives (PLOT, DRAW, GCOL, …)',
    'bbc_modes.py': 'BBC screen MODE definitions and palette tables',
    'using_formatter.py': 'Legacy shim re-exporting PRINT USING formatter',
    'mini_basic/runtime.py': 'Core BASIC interpreter, statement execution, REPL, CLI',
    'mini_basic/__init__.py': 'Public package exports (BASICInterpreter, main, config)',
    'mini_basic/__main__.py': 'python -m mini_basic entry point',
    'mini_basic/config.py': 'InterpreterConfig and system-variable specification',
    'mini_basic/constants.py': 'Builtin tables, dialect keywords, CLI exit words',
    'mini_basic/types.py': 'VarKind, exceptions, control-flow frame dataclasses',
    'mini_basic/dialect_hint.py': 'Shebang / comment dialect hint parsing',
    'mini_basic/bbcsdl_scan.py': 'BBCSDL corpus feature scanner for progress reports',
    'mini_basic/bbc_detokenize.py': 'BBC tokenised program detokeniser for LIST/SAVE',
    'mini_basic/expr/patterns.py': 'Regex patterns for expressions and builtin calls',
    'mini_basic/expr/compile.py': 'CompiledExpr cache (Python compile for arithmetic)',
    'mini_basic/format/using.py': 'MBASIC PRINT USING formatter',
    'mini_basic/format/save_case.py': 'SAVE/LIST case and keyword normalisation',
    'mini_basic/util/process.py': 'hard_exit() for clean Ctrl+C shutdown on Windows',
    'mini_basic/util/float_info.py': 'Float formatting helpers for PRINT',
    'mini_basic/repl/completion.py': 'Tab completion for LOAD/SAVE/RUN/CD filenames',
    'mini_basic/repl/help_topics.py': 'HELP topic text by dialect',
    'mini_basic/repl/help_browser.py': 'Browser-based HELP viewer',
    'mini_basic/repl/windows_input.py': 'Windows console line editing (arrows, history)',
    'ELIZA.BAS': 'Vintage ELIZA chatbot (mits dialect anchor program)',
    'BETH.BAS': 'Structured BETH demo (bbc dialect anchor program)',
    'mandelbrot_color_only.bas': 'Mandelbrot set demo (mini dialect graphics)',
    'run_mandelbrot_color_only.py': 'Runner for mandelbrot_color_only.bas',
    'run_pygame_demo.py': 'Launch pygame display demos from the shell',
    'run_corpus_menu.py': 'Interactive menu to run BBCSDL corpus programs',
    'eliza_beth.py': 'Demo launcher for ELIZA and BETH chat scripts',
    'chat_eliza.py': 'Scripted ELIZA session driver',
    'chat_beth.py': 'Scripted BETH session driver',
    'chat_grok_therapy.py': 'Grok-driven ELIZA-style therapy session',
    'chat_grok_beth_therapy.py': 'Grok-driven BETH-style therapy session',
    'generate_readme.py': 'Regenerates README.md file inventory (run after tree changes)',
    'README.md': 'Project readme (intro manual; file inventory auto-generated below marker)',
    'progress_heartbeat.py': 'Background heartbeat writer for progress/status files',
    'serve_progress_web.py': 'Local web server for progress HTML/RSS feeds',
    'force_sync_stamp.py': 'Touch SYNC_STAMP.txt (optional local stamp file)',
    'requirements-display.txt': 'Optional deps for pygame display (pip install -r)',
    'requirements-repl.txt': 'Optional deps for readline tab completion',
    'test/test_mini_basic.py': 'Main unit/regression test suite',
    'test/__main__.py': 'python -m test test runner with progress logging',
    'test/progress_runner.py': 'Corpus progress runner and feature matrix',
    'examples/README.txt': 'Index of dialect example programs',
}

PREFIX_ROLES: list[tuple[str, str]] = [
    ('mini_basic/expr/', 'Expression parsing/compilation subpackage'),
    ('mini_basic/format/', 'Program formatting (SAVE case, PRINT USING)'),
    ('mini_basic/util/', 'Small shared utilities'),
    ('mini_basic/repl/', 'REPL helpers (completion, help, Windows input)'),
    ('test/corpus/bbcsdl/games/', 'BBCSDL corpus: game program'),
    ('test/corpus/bbcsdl/graphics/', 'BBCSDL corpus: graphics demo (portable)'),
    ('test/corpus/bbcsdl/general/', 'BBCSDL corpus: general demo (portable)'),
    ('test/corpus/bbcsdl/samples/', 'BBCSDL corpus: sample fixture'),
    ('test/corpus/bbcsdl/', 'BBCSDL corpus program (portable subset)'),
    ('test/corpus/', 'Regression corpus program'),
    ('test/_probe_', 'Ad-hoc debugging probe script (not part of test suite)'),
    ('test/manual/', 'Manual/benchmark test harness'),
    ('test/', 'Unit or integration test module'),
    ('examples/mits/', 'mits dialect example program'),
    ('examples/bbc/', 'bbc dialect example program'),
    ('examples/mini/', 'mini dialect example program'),
    ('examples/', 'Example BASIC program or notes'),
    ('backup/snapshot/', 'Frozen backup copy of earlier interpreter sources'),
    ('backup/', 'Backup archive and notes'),
]

EXTENSION_ROLES: dict[str, str] = {
    '.py': 'Python module or script',
    '.bas': 'BASIC source program',
    '.txt': 'Documentation or status notes',
    '.md': 'Markdown documentation',
    '.html': 'HTML documentation or status page',
    '.rss': 'RSS progress feed',
    '.json': 'JSON data (progress history, config)',
    '.cmd': 'Windows batch launcher',
    '.ps1': 'PowerShell launcher/script',
    '.log': 'Test or run log output',
}


@dataclass
class FileInfo:
    rel_path: str
    lines: int
    size: int
    role: str
    category: str


def posix_relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def should_skip(path: Path) -> bool:
    if path.name in SKIP_FILE_NAMES:
        return True
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True
    for part in path.parts:
        if part in SKIP_DIR_NAMES:
            return True
    return False


def count_lines(path: Path) -> int:
    try:
        with path.open('r', encoding='utf-8', errors='replace') as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def module_docstring_role(path: Path) -> str | None:
    if path.suffix != '.py':
        return None
    try:
        source = path.read_text(encoding='utf-8', errors='replace')
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return None
    doc = ast.get_docstring(tree, clean=True)
    if not doc:
        return None
    first = doc.splitlines()[0].strip()
    return first if first else None


def infer_category(rel_path: str) -> str:
    if rel_path.startswith('mini_basic/'):
        return 'Core package'
    if rel_path.startswith('test/corpus/'):
        parts = rel_path.split('/')
        if len(parts) >= 4:
            folder = parts[3]
            # File directly under corpus/<suite>/ → group by suite only.
            if '.' in folder:
                return f'Corpus ({parts[2]})'
            return f'Corpus ({parts[2]}/{folder})'
        return 'Corpus'
    if rel_path.startswith('test/'):
        return 'Tests'
    if rel_path.startswith('examples/'):
        return 'Examples'
    if rel_path.startswith('backup/'):
        return 'Backup'
    if rel_path.endswith(('.ps1', '.cmd')) or 'web' in rel_path.lower() or rel_path.startswith(
        ('serve_', 'start_web', 'register_progress', 'progress_', 'STATUS', 'PROGRESS', 'PHONE_', 'RSS_', 'WEB_', 'MOBILE_', 'FOLLOW_', 'SYNC_', 'status.html', 'FEATURES_DONE', 'CORPUS_RUNNABLE', 'CURRENT_TASK')
    ):
        return 'Progress & publishing'
    if rel_path.endswith('.bas') or rel_path.endswith('.BAS'):
        return 'BASIC programs'
    if rel_path in {'display.py', 'bbc_graphics.py', 'bbc_modes.py', 'run_pygame_demo.py'}:
        return 'Display & graphics'
    if rel_path.startswith('chat_') or rel_path in {'eliza_beth.py'}:
        return 'Chat demos'
    return 'Project root'


def infer_role(rel_path: str, path: Path) -> str:
    if rel_path in EXACT_ROLES:
        return EXACT_ROLES[rel_path]

    for prefix, role in PREFIX_ROLES:
        if rel_path.startswith(prefix):
            if rel_path.startswith('test/corpus/') and path.suffix.lower() in {'.txt', '.bas'}:
                return role
            if prefix.startswith('test/') and path.name.startswith('test_'):
                name = path.stem.replace('test_', '').replace('_', ' ')
                return f'Tests: {name}'
            return role

    doc_role = module_docstring_role(path)
    if doc_role:
        return doc_role

    ext = path.suffix.lower()
    if ext in EXTENSION_ROLES:
        return EXTENSION_ROLES[ext]

    return 'Project file'


def scan_tree(root: Path) -> list[FileInfo]:
    files: list[FileInfo] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            name for name in dirnames
            if name not in SKIP_DIR_NAMES
        )
        for name in sorted(filenames):
            path = Path(dirpath) / name
            if should_skip(path):
                continue
            rel = posix_relpath(path, root)
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            files.append(
                FileInfo(
                    rel_path=rel,
                    lines=count_lines(path),
                    size=size,
                    role=infer_role(rel, path),
                    category=infer_category(rel),
                )
            )
    return files


def human_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f'{num_bytes} B'
    if num_bytes < 1024 * 1024:
        return f'{num_bytes / 1024:.1f} KB'
    return f'{num_bytes / (1024 * 1024):.1f} MB'


def load_intro(readme_path: Path) -> str:
    if not readme_path.is_file():
        return DEFAULT_INTRO
    text = readme_path.read_text(encoding='utf-8')
    if MARKER in text:
        return text.split(MARKER, 1)[0].rstrip() + '\n\n'
    if '## File inventory' in text:
        return text.split('## File inventory', 1)[0].rstrip() + '\n\n'
    return text.rstrip() + '\n\n'


def render_inventory(files: list[FileInfo], generated_at: str) -> str:
    total_files = len(files)
    total_lines = sum(item.lines for item in files)
    total_size = sum(item.size for item in files)

    by_category: dict[str, list[FileInfo]] = defaultdict(list)
    for item in files:
        by_category[item.category].append(item)

    category_order = [
        'Core package',
        'Display & graphics',
        'BASIC programs',
        'Examples',
        'Tests',
        'Corpus (bbcsdl/games)',
        'Corpus (bbcsdl/general)',
        'Corpus (bbcsdl/graphics)',
        'Corpus (bbcsdl/samples)',
        'Corpus (agon)',
        'Corpus (msbasic)',
        'Corpus (bbcsdl)',
        'Corpus',
        'Chat demos',
        'Progress & publishing',
        'Backup',
        'Project root',
    ]

    lines: list[str] = [
        MARKER,
        '',
        '## File inventory',
        '',
        f'*Generated {generated_at} by `python generate_readme.py` — do not edit this section by hand.*',
        '',
        '| Metric | Value |',
        '|--------|------:|',
        f'| Files scanned | {total_files:,} |',
        f'| Total lines | {total_lines:,} |',
        f'| Total size | {human_size(total_size)} |',
        '',
        '### Summary by area',
        '',
        '| Area | Files | Lines | Size |',
        '|------|------:|------:|-----:|',
    ]

    ordered_categories = [cat for cat in category_order if cat in by_category]
    for cat in sorted(by_category):
        if cat not in ordered_categories:
            ordered_categories.append(cat)

    for category in ordered_categories:
        items = by_category[category]
        cat_lines = sum(item.lines for item in items)
        cat_size = sum(item.size for item in items)
        lines.append(
            f'| {category} | {len(items)} | {cat_lines:,} | {human_size(cat_size)} |'
        )

    for category in ordered_categories:
        items = sorted(by_category[category], key=lambda item: item.rel_path)
        lines.extend([
            '',
            f'### {category}',
            '',
            '| File | Lines | Size | Role |',
            '|------|------:|-----:|------|',
        ])
        for item in items:
            role = item.role.replace('|', '\\|')
            lines.append(
                f'| `{item.rel_path}` | {item.lines:,} | {human_size(item.size)} | {role} |'
            )

    lines.append('')
    return '\n'.join(lines)


DEFAULT_INTRO = """# mini-BASIC

A small BASIC interpreter in Python with three dialect profiles.

**Naming:** `mini_basic` in code and commands; **mini-BASIC** in titles and prose; **BASIC** for the language itself.

## Quick start

```bash
cd mini_basic
python mini_basic.py
python mini_basic.py --dialect bbc BETH.BAS
python -m test
python generate_readme.py   # refresh file inventory below
```

"""


def write_readme(root: Path, dry_run: bool = False) -> str:
    readme_path = root / 'README.md'
    files = scan_tree(root)
    generated_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    intro = load_intro(readme_path)
    body = intro + render_inventory(files, generated_at)
    if not dry_run:
        readme_path.write_text(body, encoding='utf-8', newline='\n')
    return body


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--root',
        type=Path,
        default=DEFAULT_ROOT,
        help='Project root to scan (default: directory containing this script)',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print generated README to stdout instead of writing README.md',
    )
    args = parser.parse_args()
    root = args.root.resolve()
    output = write_readme(root, dry_run=args.dry_run)
    if args.dry_run:
        print(output)
    else:
        print(f'Wrote {root / "README.md"} ({len(output):,} chars, inventory updated)')


if __name__ == '__main__':
    main()