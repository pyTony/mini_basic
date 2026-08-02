"""One-shot resource verifier for agents and scheduled checks.

Manual: python verify_resources.py
After OOM crash: python verify_resources.py --record-crash [--bytes N]
Exit codes: 0 ok, 1 warn/reduce, 2 critical/stop
"""
from __future__ import annotations

import argparse
import sys

from utils.agent_resource import (
    clear_crash_marker,
    record_allocation_failure,
    run_resource_verifier,
)


def main() -> int:
    parser = argparse.ArgumentParser(description='Check agent/process resource usage')
    parser.add_argument(
        '--record-crash',
        action='store_true',
        help='Record a recent allocation failure and force critical alerts (30 min)',
    )
    parser.add_argument(
        '--bytes',
        type=int,
        default=0,
        help='Bytes from failed allocation (e.g. 296812544)',
    )
    parser.add_argument(
        '--message',
        default='memory allocation failed',
        help='Crash message to store',
    )
    parser.add_argument(
        '--clear-crash',
        action='store_true',
        help='Clear crash marker after memory has recovered',
    )
    parser.add_argument(
        '--no-python-probe',
        action='store_true',
        help='Skip Grok/agent leftover Python process scan (AGENT_POLICY §5b)',
    )
    parser.add_argument(
        '--kill-orphans',
        action='store_true',
        help='Also kill clear orphan agent probes (see scripts/probe_agent_python.py)',
    )
    args = parser.parse_args()

    if args.clear_crash:
        clear_crash_marker()
        code = run_resource_verifier()
    elif args.record_crash:
        bytes_requested = args.bytes if args.bytes > 0 else None
        verdict = record_allocation_failure(args.message, bytes_requested=bytes_requested)
        print(f'Recorded crash alert: level={verdict.level}')
        code = 2
    else:
        code = run_resource_verifier()

    # §5b: always surface hung Grok/agent Python unless skipped.
    if not args.no_python_probe:
        try:
            import runpy
            from pathlib import Path

            probe_path = Path(__file__).resolve().parent / 'probe_agent_python.py'
            # run as __main__ would exit; load via runpy for attributes
            ns = runpy.run_path(str(probe_path), run_name='probe_agent_python_mod')
            scan = ns['scan']
            format_proc = ns['format_proc']
            agentish, killed = scan(kill_orphans=args.kill_orphans)
            orphans = [p for p in agentish if p.is_orphan_candidate]
            if not agentish:
                print('agent-python: none found')
            else:
                print(
                    f'agent-python: {len(agentish)} related '
                    f'({len(orphans)} orphan-candidates)'
                    + (f' killed={killed}' if killed else '')
                )
                for p in sorted(orphans, key=lambda x: -x.cpu_seconds)[:8]:
                    print(format_proc(p))
                if orphans and not args.kill_orphans:
                    print(
                        '  tip: python scripts/probe_agent_python.py --kill-orphans'
                    )
                if orphans and code == 0:
                    code = 1  # warn: leftovers present
        except Exception as exc:
            print(f'agent-python probe skipped: {exc}')

    return code


if __name__ == '__main__':
    raise SystemExit(main())