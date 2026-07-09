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
    args = parser.parse_args()

    if args.clear_crash:
        clear_crash_marker()
        return run_resource_verifier()

    if args.record_crash:
        bytes_requested = args.bytes if args.bytes > 0 else None
        verdict = record_allocation_failure(args.message, bytes_requested=bytes_requested)
        print(f'Recorded crash alert: level={verdict.level}')
        return 2

    return run_resource_verifier()


if __name__ == '__main__':
    raise SystemExit(main())