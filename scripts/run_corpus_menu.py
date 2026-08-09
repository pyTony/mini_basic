#!/usr/bin/env python3
"""Interactive menu to run BBCSDL corpus programs that work in mini_basic.

Reads CORPUS_RUNNABLE.txt. Optional status tags after the folder name:

  [ok]    known good / audit OK
  [defer] known gap (sound, interactive MODE7, …)
  [slow]  correct but slow draw
  [new]   recently changed — re-check recommended

Example line::

  saucer.txt graphics [ok] [slow] Flying saucer — shape OK, draw slow
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

_ROOT = Path(__file__).resolve().parents[1]
_CORPUS_LIST = _ROOT / 'CORPUS_RUNNABLE.txt'
_CORPUS_ROOT = _ROOT / 'test' / 'corpus' / 'bbcsdl'
_AUDIT = _ROOT / 'CORPUS_AUDIT.txt'

_CATEGORY_ORDER = (
    'games',
    'graphics',
    'general',
    'samples',
)

_STATUS_TAGS = frozenset({'ok', 'defer', 'slow', 'new', 'fail'})


@dataclass(frozen=True)
class CorpusEntry:
    name: str
    folder: str
    blurb: str
    tags: frozenset[str] = field(default_factory=frozenset)

    @property
    def path(self) -> Path:
        return _CORPUS_ROOT / self.folder / self.name

    @property
    def is_new(self) -> bool:
        return 'new' in self.tags

    @property
    def title(self) -> str:
        badges: List[str] = []
        if 'ok' in self.tags:
            badges.append('OK')
        if 'defer' in self.tags:
            badges.append('DEFER')
        if 'fail' in self.tags:
            badges.append('FAIL')
        if 'slow' in self.tags:
            badges.append('SLOW')
        if 'new' in self.tags:
            badges.append('NEW')
        if badges:
            return f'{self.name} [{", ".join(badges)}]'
        return self.name

    @property
    def description(self) -> str:
        if self.blurb and self.blurb != self.folder:
            return self.blurb
        return self.folder.capitalize()


def _parse_rest(rest: str) -> Tuple[str, frozenset[str], str]:
    """Split ``folder [tags…] description`` after the filename."""
    rest = rest.strip()
    if not rest:
        return '', frozenset(), ''
    parts = rest.split()
    folder = parts[0]
    tags: Set[str] = set()
    i = 1
    while i < len(parts):
        m = re.fullmatch(r'\[([A-Za-z0-9_]+)\]', parts[i])
        if not m:
            break
        tag = m.group(1).lower()
        if tag in _STATUS_TAGS:
            tags.add(tag)
        i += 1
    blurb = ' '.join(parts[i:]) if i < len(parts) else folder
    return folder, frozenset(tags), blurb


def _audit_fail_names() -> Set[str]:
    """Names listed under FAIL in CORPUS_AUDIT.txt (if present)."""
    if not _AUDIT.is_file():
        return set()
    fails: Set[str] = set()
    in_fail = False
    for raw in _AUDIT.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        upper = line.upper()
        if upper.startswith('FAIL'):
            in_fail = True
            continue
        if upper.startswith('OK'):
            in_fail = False
            continue
        if in_fail:
            name = line.split()[0]
            if name.lower().endswith('.txt'):
                fails.add(name)
    return fails


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
        parts = line.split(None, 1)
        name = parts[0]
        if not name.lower().endswith('.txt'):
            continue
        rest = parts[1] if len(parts) > 1 else ''
        folder, tags, blurb = _parse_rest(rest)
        if section == 'new':
            tags = frozenset(set(tags) | {'new'})
        if section == 'not':
            skipped.append(f'{name} ({folder or "?"})')
            continue
        entries.append(
            CorpusEntry(
                name=name,
                folder=folder,
                blurb=blurb,
                tags=tags,
            )
        )
    # ALL may repeat NEW lines; merge tags and prefer longer blurb.
    seen: Dict[str, CorpusEntry] = {}
    for entry in entries:
        prev = seen.get(entry.name)
        if prev is None:
            seen[entry.name] = entry
            continue
        blurb = entry.blurb if len(entry.blurb) > len(prev.blurb) else prev.blurb
        tags = frozenset(set(prev.tags) | set(entry.tags))
        folder = entry.folder or prev.folder
        seen[entry.name] = CorpusEntry(
            name=entry.name,
            folder=folder,
            blurb=blurb,
            tags=tags,
        )
    # Overlay audit FAIL if not already tagged defer/fail.
    for name in _audit_fail_names():
        ent = seen.get(name)
        if ent is None:
            continue
        if 'ok' in ent.tags and 'defer' not in ent.tags:
            # Prefer explicit CORPUS_RUNNABLE tags over stale audit.
            continue
        if 'defer' not in ent.tags and 'fail' not in ent.tags:
            seen[name] = CorpusEntry(
                name=ent.name,
                folder=ent.folder,
                blurb=ent.blurb,
                tags=frozenset(set(ent.tags) | {'fail'}),
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
    print('Tags: [OK] good  [DEFER]/[FAIL] known issues  [SLOW] slow draw  [NEW] re-check')
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
        print('\nNot in menu (need network / out of scope):', ', '.join(skipped))
    print('\nGraphics demos loop until you close the window or press Ctrl+C / ESC.')
    print('Run with: --pygame --dialect bbc --hold')
    print('Note: SOUND is silent (optional short wait). Music/tools/physics trees not in corpus.')


def _run_entry(entry: CorpusEntry) -> int:
    if not entry.path.is_file():
        print(f'File not found: {entry.path}')
        return 1
    if 'defer' in entry.tags or 'fail' in entry.tags:
        print()
        print(f'Note: {entry.name} is marked with issues — may not look/run fully.')
        print(f'      {entry.description}')
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
            if entry.path == path.resolve() or entry.name == token:
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
