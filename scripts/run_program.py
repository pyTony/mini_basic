"""Print how to run a corpus program for real user verification.

verify_program.py is agent-only (automated snippet checks). You approve a
program by running it interactively or visually, trying varied inputs.

Usage (from mini_basic folder):
  python run_program.py animal.txt
  python run_program.py --list
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from utils.program_run_guide import PROGRAM_USER_RUN, run_guide_for  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description='How to run a corpus program for user verification',
    )
    parser.add_argument('program', nargs='?', help='e.g. animal.txt')
    parser.add_argument('--list', action='store_true', help='List programs with run guides')
    args = parser.parse_args()

    if args.list:
        print('Programs with run guides:')
        for name in sorted(PROGRAM_USER_RUN):
            print(f'  {name}')
        print('\nRun: python run_program.py <name>')
        return 0

    program = (args.program or '').strip()
    if not program:
        print('? Specify program: python run_program.py animal.txt')
        return 1

    guide = run_guide_for(program)
    if guide is None:
        print(f'? No run guide for {program!r} yet')
        print('  python run_program.py --list')
        return 1

    print(f'Run {program} yourself (not verify_program.py — that is agent-only):')
    print()
    print(f'  cd {_ROOT}')
    print(f'  {guide["command"]}')
    print()
    print(f'Type: {guide["kind"]}')
    print()
    print('Try:')
    for note in guide['try_notes']:
        print(f'  • {note}')
    print()
    print('When output/behaviour looks correct across several tries, reply OK in chat.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())