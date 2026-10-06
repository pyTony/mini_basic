#!/usr/bin/env python3
"""Run through the v1.0 "demo reel" — a curated set of confirmed-working
showcase/ programs chosen to show off graphics, performance, structs and
classic algorithms in one sitting.

Usage (from the project root):

    python showcase/demo_reel.py              # interactive menu (pick one, or run all)
    python showcase/demo_reel.py --all         # run all 8, in order, no menu
    python showcase/demo_reel.py --list        # print the reel (with blurbs) and exit
    python showcase/demo_reel.py wheel fern    # run just these entries, no menu

With no arguments and no terminal attached (e.g. piped/CI), falls back to
--all instead of waiting on a menu nobody can answer.

Pygame entries use a window (close it, or press the program's usual exit
key, to move to the next one).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]

# mini_basic.constants.EXIT_HOLD_CONSOLE: a non-interactive console run (no
# --pygame) exits with this on a normal finish, not an error.
_EXIT_HOLD_CONSOLE = 10


@dataclass(frozen=True)
class ReelEntry:
    key: str
    path: str
    dialect: str
    pygame: bool
    blurb: str


REEL: tuple[ReelEntry, ...] = (
    ReelEntry(
        'disco', 'showcase/disco.bbc', 'bbc', True,
        'Colour lightshow: grid redraw + palette cycling.',
    ),
    ReelEntry(
        'illusion', 'showcase/illusion.bbc', 'bbc', True,
        'Cafe-wall optical illusion: a dead-straight grid of tan/grey bands '
        "looks bent because of small alternating corner wedges at each "
        'intersection (checkerboard-parity PLOT 113 marks) — same trick as '
        'the real cafe-wall effect, nothing in the grid itself is skewed.',
    ),
    ReelEntry(
        'wheel', 'showcase/wheel.bbc', 'bbc', True,
        'Spinning colour-ring: CASE/WHEN dispatch, CIRCLE discs, *REFRESH.',
    ),
    ReelEntry(
        'fern', 'showcase/fern.bbc', 'bbc', True,
        'Barnsley fern fractal drawn with chained DRAW/affine steps.',
    ),
    ReelEntry(
        'mandelbrot', 'showcase/mandelbrot_archimedes_mode9.bas', 'bbc', True,
        'Full-screen MODE 9 Mandelbrot, solid-block colouring — the '
        'interpreter perf highlight (renders in a few seconds).',
    ),
    ReelEntry(
        'bounce', 'showcase/bounce.bbc', 'bbc', True,
        'Bouncing balls: nested structs Pos{x,y}, whole-struct array copy, '
        '+= on struct members.',
    ),
    ReelEntry(
        'hanoi', 'showcase/hanoi.bbc', 'bbc', True,
        'Towers of Hanoi, solved and animated recursively. Interactive: '
        'enter a disc count (1-13), then press SPACE to start.',
    ),
    ReelEntry(
        'soccerball', 'showcase/soccerball.bas', 'bbc', True,
        'Spinning 3D soccer ball: matrix rotation (B() . C()) redrawn every frame.',
    ),
)


def _run_entry(entry: ReelEntry) -> int:
    print(f'\n=== {entry.key}: {entry.blurb}')
    print(f'    {entry.path}')
    argv = [sys.executable, '-m', 'mini_basic', '--dialect', entry.dialect]
    if entry.pygame:
        argv.append('--pygame')
    argv.append(entry.path)
    rc = subprocess.call(argv, cwd=_ROOT)
    ok = rc == 0 or (not entry.pygame and rc == _EXIT_HOLD_CONSOLE)
    if not ok:
        print(f'! {entry.key} exited with code {rc}', file=sys.stderr)
    return rc


def _print_list() -> None:
    print('Demo reel:')
    for e in REEL:
        kind = 'pygame' if e.pygame else 'console'
        print(f'  {e.key:12s} [{kind:7s}] {e.blurb}')


def _interactive_menu() -> int:
    """Pick one entry at a time, see its blurb, run it, come back to the menu."""
    while True:
        print('\nmini_basic v1.0 demo reel — pick one to see what it shows off:\n')
        for i, e in enumerate(REEL, 1):
            print(f'  {i}. {e.key:12s} {e.blurb}')
        print('\n  a. run all, in order')
        print('  q. quit')
        try:
            choice = input('\n> ').strip().lower()
        except EOFError:
            print()
            return 0
        if choice in ('', 'q', 'quit'):
            return 0
        if choice in ('a', 'all'):
            for entry in REEL:
                _run_entry(entry)
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(REEL):
            _run_entry(REEL[int(choice) - 1])
            continue
        print(f'Unrecognised choice: {choice!r}')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run the mini_basic v1.0 demo reel')
    parser.add_argument('keys', nargs='*', help='only run these entries (by key), in reel order')
    parser.add_argument('--list', action='store_true', help='print the reel (with blurbs) and exit')
    parser.add_argument(
        '--all', action='store_true',
        help='run the whole reel in order, no menu',
    )
    args = parser.parse_args(argv)

    if args.list:
        _print_list()
        return 0

    wanted = set(args.keys)
    if wanted:
        entries = [e for e in REEL if e.key in wanted]
        unknown = wanted - {e.key for e in REEL}
        if unknown:
            _print_list()
            print(f'\nUnknown key(s): {", ".join(sorted(unknown))}')
            return 1
        for entry in entries:
            _run_entry(entry)
        return 0

    if args.all or not sys.stdin.isatty():
        for entry in REEL:
            _run_entry(entry)
        return 0

    return _interactive_menu()


if __name__ == '__main__':
    raise SystemExit(main())
