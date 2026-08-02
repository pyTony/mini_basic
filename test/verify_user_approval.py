"""Refresh agent program + snippet verification files."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from utils.user_approval import (  # noqa: E402
    load_user_approval_labels,
    run_agent_approval_checks,
    write_agent_results,
)


def main() -> int:
    pending, approved = load_user_approval_labels()
    program_lines, snippet_lines = run_agent_approval_checks(pending + approved)
    write_agent_results(program_lines, snippet_lines)
    failed = sum(1 for line in program_lines if line.startswith('FAIL '))
    ok = sum(1 for line in program_lines if line.startswith('OK '))
    for line in program_lines:
        print(line)
    print('--- snippets ---')
    for line in snippet_lines:
        print(line)
    print(f'summary programs OK={ok} FAIL={failed}')
    print('User verify: python verify_program.py animal.txt')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())