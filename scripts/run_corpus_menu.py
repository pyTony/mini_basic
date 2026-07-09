#!/usr/bin/env python3
"""Interactive menu to run BBCSDL corpus programs that work in mini_basic."""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

_ROOT = Path(__file__).resolve().parents[1]
_CORPUS_LIST = _ROOT / 'CORPUS_RUNNABLE.txt'
_CORPUS_ROOT = _ROOT / 'test' / 'corpus' / 'bbcsdl'

_CATEGORY_ORDER = (
    'games',
    'graphics',
    'general',
    'sounds',
    'tools',
    'samples',
)


@dataclass(frozen=True)
class CorpusEntry:
    name: str
    folder: str
    blurb: str
    is_new: bool

    @property
    def path(self) -> Path:
        return _CORPUS_ROOT / self.folder / self.name

    @property
    def title(self) -> str:
        text = self.name
        if self.is_new:
            text = f'{text} [NEW]'
        return text

    @property
    def description(self) -> str:
        if self.blurb and self.blurb != self.folder:
            return self.blurb
        return self.folder.capitalize()


def _parse_corpus_list(text: str) -> Tuple[List[CorpusEntry], List[str]]:
    entries: List[CorpusEntry] = []
    skipped: List[str] = []
    section = ''
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        upper = line.upper()
        if upper.startswith('NEW '):
            section = 'new'
            continue
        if upper.startswith('ALL '):
            section = 'all'
            continue
        if upper.startswith('NOT '):
            section = 'not'
            continue
        parts = line.split(' ', 1)
        name = parts[0]
        if not name.lower().endswith('.txt'):
            continue
        rest = parts[1] if len(parts) > 1 else ''
        bits = rest.split(' ', 1)
        folder = bits[0] if bits else ''
        blurb = bits[1] if len(bits) > 1 else folder
        if section == 'not':
            skipped.append(f'{name} ({folder})')
            continue
        entries.append(
            CorpusEntry(
                name=name,
                folder=folder,
                blurb=blurb,
                is_new=section == 'new',
            )
        )
    # ALL section duplicates NEW entries; keep best blurb and NEW flag.
    seen: Dict[str, CorpusEntry] = {}
    for entry in entries:
        prev = seen.get(entry.name)
        if prev is None:
            seen[entry.name] = entry
            continue
        blurb = entry.blurb if len(entry.blurb) > len(prev.blurb) else prev.blurb
        seen[entry.name] = CorpusEntry(
            name=entry.name,
            folder=entry.folder,
            blurb=blurb,
            is_new=prev.is_new or entry.is_new,
        )
    ordered = sorted(
        seen.values(),
        key=lambda item: (
            _CATEGORY_ORDER.index(item.folder)
            if item.folder in _CATEGORY_ORDER
            else 99,
            item.name.lower(),
        ),
    )
    return ordered, skipped


def _load_entries() -> Tuple[List[CorpusEntry], List[str]]:
    if not _CORPUS_LIST.is_file():
        raise SystemExit(f'Missing {_CORPUS_LIST.name}')
    return _parse_corpus_list(_CORPUS_LIST.read_text(encoding='utf-8'))


def _grouped(entries: Sequence[CorpusEntry]) -> List[Tuple[str, List[CorpusEntry]]]:
    groups: Dict[str, List[CorpusEntry]] = {}
    for entry in entries:
        groups.setdefault(entry.folder, []).append(entry)
    return [
        (folder, groups[folder])
        for folder in _CATEGORY_ORDER
        if folder in groups
    ]


def _menu_items(entries: Sequence[CorpusEntry]) -> List[Optional[CorpusEntry]]:
    items: List[Optional[CorpusEntry]] = []
    for _, group in _grouped(entries):
        items.extend(group)
    return items


def _print_menu(entries: Sequence[CorpusEntry], skipped: Sequence[str]) -> None:
    print()
    print('mini_basic — runnable BBCSDL programs')
    print('=' * 40)
    index = 1
    for folder, group in _grouped(entries):
        title = folder.capitalize()
        print(f'\n{title}')
        print('-' * len(title))
        for entry in group:
            print(f'  {index:2}. {entry.title}')
            print(f'      {entry.description}')
            index += 1
    print('\n  0. Quit')
    if skipped:
        print('\nNot in menu (need network):', ', '.join(skipped))
    print('\nGraphics demos loop until you close the window or press Ctrl+C.')
    print('Run with: --pygame --dialect bbc --hold')


def _run_entry(entry: CorpusEntry) -> int:
    if not entry.path.is_file():
        print(f'File not found: {entry.path}')
        return 1
    cmd = [
        sys.executable,
        '-m',
        'mini_basic',
        '--pygame',
        '--dialect',
        'bbc',
        '--hold',
        str(entry.path),
    ]
    print()
    print(f'Running: {entry.title}')
    print(f'         {entry.description}')
    print(entry.path.relative_to(_ROOT))
    print(' '.join(cmd))
    print()
    return subprocess.call(cmd, cwd=str(_ROOT))


def _pick(items: Sequence[Optional[CorpusEntry]], choice: str) -> Optional[CorpusEntry]:
    if choice in ('0', 'q', 'quit', 'exit'):
        return None
    try:
        num = int(choice)
    except ValueError:
        return ...
    if num < 1 or num > len(items):
        return ...
    return items[num - 1]


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    entries, skipped = _load_entries()
    missing = [entry for entry in entries if not entry.path.is_file()]
    if missing:
        names = ', '.join(entry.name for entry in missing)
        print(f'Warning: corpus files missing: {names}', file=sys.stderr)

    if args:
        token = args[0]
        if token.isdigit():
            items = _menu_items(entries)
            picked = _pick(items, token)
            if picked is ...:
                print('Invalid number.')
                return 1
            if picked is None:
                return 0
            return _run_entry(picked)
        path = Path(token)
        if not path.is_file():
            path = _CORPUS_ROOT / token
        for entry in entries:
            if entry.path == path.resolve():
                return _run_entry(entry)
        print(f'Not in runnable list: {token}')
        return 1

    items = _menu_items(entries)
    while True:
        _print_menu(entries, skipped)
        try:
            choice = input('\nChoice: ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        picked = _pick(items, choice)
        if picked is ...:
            print('Enter a number from the menu, or 0 to quit.')
            continue
        if picked is None:
            return 0
        code = _run_entry(picked)
        if code != 0:
            print(f'Program exited with code {code}')
        try:
            input('\nPress Enter for menu...')
        except (EOFError, KeyboardInterrupt):
            print()
            return 0


if __name__ == '__main__':
    raise SystemExit(main())