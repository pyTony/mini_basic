#!/usr/bin/env python3
"""Run through the v1.0 "demo reel" — a curated set of confirmed-working
examples/ programs chosen to show off graphics, performance, structs and
classic algorithms in one sitting.

Usage (from the project root):

    python scripts/demo_reel.py              # run all 8, in order
    python scripts/demo_reel.py --list        # show the reel without running it
    python scripts/demo_reel.py wheel fern    # run just these entries

Pygame entries use a window (close it, or press the program's usual exit
key, to move to the next one). Console entries (Mandel_ANSI) just print
and return.
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
        'disco', 'examples/graphics/disco.bbc', 'bbc', True,
        'Colour lightshow: grid redraw + palette cycling.',
    ),
    ReelEntry(
        'illusion', 'examples/graphics/illusion.bbc', 'bbc', True,
        'Cafe-wall optical illusion: a dead-straight grid of tan/grey bands '
        "looks bent because of small alternating corner wedges at each "
        'intersection (checkerboard-parity PLOT 113 marks) — same trick as '
        'the real cafe-wall effect, nothing in the grid itself is skewed.',
    ),
    ReelEntry(
        'wheel', 'examples/graphics/wheel.bbc', 'bbc', True,
        'Spinning colour-ring: CASE/WHEN dispatch, CIRCLE discs, *REFRESH.',
    ),
    ReelEntry(
        'fern', 'examples/graphics/fern.bbc', 'bbc', True,
        'Barnsley fern fractal drawn with chained DRAW/affine steps.',
    ),
    ReelEntry(
        'mandel_ansi', 'examples/graphics/mandelbrot/Mandel_ANSI.BAS', 'mini', False,
        'Mandelbrot set in ANSI colour, console only — renders in well '
        'under a second, the interpreter perf highlight.',
    ),
    ReelEntry(
        'bounce', 'examples/graphics/bounce.bbc', 'bbc', True,
        'Bouncing balls: nested structs Pos{x,y}, whole-struct array copy, '
        '+= on struct members.',
    ),
    ReelEntry(
        'hanoi', 'examples/games/hanoi.bbc', 'bbc', True,
        'Towers of Hanoi, solved and animated recursively. Interactive: '
        'enter a disc count (1-13), then press SPACE to start.',
    ),
    ReelEntry(
        'soccerball', 'examples/graphics/soccerball.bas', 'bbc', True,
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
    return subprocess.call(argv, cwd=_ROOT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run the mini_basic v1.0 demo reel')
    parser.add_argument('keys', nargs='*', help='only run these entries (by key), in reel order')
    parser.add_argument('--list', action='store_true', help='print the reel and exit')
    args = parser.parse_args(argv)

    wanted = set(args.keys)
    entries = [e for e in REEL if not wanted or e.key in wanted]

    if args.list or not entries:
        print('Demo reel:')
        for e in REEL:
            kind = 'pygame' if e.pygame else 'console'
            print(f'  {e.key:12s} [{kind:7s}] {e.blurb}')
        if args.list:
            return 0
        print(f'\nUnknown key(s): {", ".join(sorted(wanted - {e.key for e in REEL}))}')
        return 1

    for entry in entries:
        rc = _run_entry(entry)
        ok = rc == 0 or (not entry.pygame and rc == _EXIT_HOLD_CONSOLE)
        if not ok:
            print(f'! {entry.key} exited with code {rc}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
