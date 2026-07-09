"""Agent-only automated snippet checks for corpus programs.

This does NOT replace user verification. Users run the real program with
mini_basic.py (see run_program.py) and confirm behaviour with varied inputs.

Usage (agent / CI):
  python verify_program.py animal.txt
  python verify_program.py --update-agent-files

User verification:
  python run_program.py animal.txt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from utils.user_approval import (  # noqa: E402
    PROGRAM_CHECKERS,
    load_user_approval_labels,
    run_agent_approval_checks,
    write_agent_results,
)


def _current_program_from_task() -> str:
    task_path = _ROOT / 'CURRENT_TASK.txt'
    if not task_path.is_file():
        return ''
    for raw in task_path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '.txt' in line.lower():
            part = line.split('—', 1)[0].split('-', 1)[0].strip()
            if part.lower().endswith('.txt'):
                return part
    return ''


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Agent automated snippet checks (not user verification)',
    )
    parser.add_argument(
        'program',
        nargs='?',
        help='Program name e.g. animal.txt (default: CURRENT_TASK.txt)',
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List programs that have automated verification',
    )
    parser.add_argument(
        '--update-agent-files',
        action='store_true',
        help='Also refresh USER_APPROVAL_AGENT.txt and USER_VERIFY_SNIPPETS.txt',
    )
    args = parser.parse_args()

    if args.list:
        pending, approved = load_user_approval_labels()
        print('Programs in USER_APPROVAL.txt:')
        for label in pending:
            mark = 'checker' if label in PROGRAM_CHECKERS else 'pending checker'
            print(f'  [ ] {label} ({mark})')
        for label in approved:
            print(f'  [x] {label}')
        print('\nAgent: python verify_program.py <name>')
        print('User:  python run_program.py <name>')
        return 0

    program = (args.program or _current_program_from_task()).strip()
    if not program:
        print('? Specify program: python verify_program.py animal.txt')
        return 1

    checker = PROGRAM_CHECKERS.get(program)
    if checker is None:
        print(f'? No verifier for {program!r} yet')
        print('  python verify_program.py --list')
        return 1

    print(f'Agent snippet check: {program}')
    print('(User runs the real program: python run_program.py', program + ')')
    print()

    ok, summary, snippets = checker()
    for name, snippet_ok, detail in snippets:
        mark = 'OK' if snippet_ok else 'FAIL'
        print(f'  {mark} {name}: {detail}')
    print()
    print(f'AGENT {"OK" if ok else "FAIL"}: {summary}')

    if args.update_agent_files:
        program_lines, snippet_lines = run_agent_approval_checks([program])
        write_agent_results(program_lines, snippet_lines)
        print('Updated USER_APPROVAL_AGENT.txt and USER_VERIFY_SNIPPETS.txt')

    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())