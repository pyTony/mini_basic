"""One-shot status poller / light heartbeat (no process left open).

Policy (see AGENT_POLICY.txt §3):
  - Agents update *source* .txt files (CURRENT_TASK, FEATURES_DONE, …).
  - This script polls those files and rebuilds status.html **only when they
    change** (or when a rare agent-staleness check needs a warning).
  - Does **not** wipe the dashboard with a lightweight empty heartbeat payload.

Scheduled via register_progress_task.ps1 (default: every 5 minutes).
Manual:
  python scripts/progress_heartbeat.py
  python scripts/progress_heartbeat.py --force
  python scripts/progress_heartbeat.py --stale-check
"""
from __future__ import annotations

import argparse
import gc
import os
import sys

# Heartbeat must never open SDL/pygame windows if any import chain touches display.
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Poll status source .txt → status.html')
    parser.add_argument(
        '--force',
        action='store_true',
        help='Rebuild status.html even if source fingerprints are unchanged',
    )
    parser.add_argument(
        '--stale-check',
        action='store_true',
        help='Force agent-file staleness check this run',
    )
    parser.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        help='No stdout (for pythonw scheduled task)',
    )
    args = parser.parse_args(argv)

    gc.collect()
    try:
        from mini_basic.display import ensure_no_pygame_leftovers

        ensure_no_pygame_leftovers()
    except Exception:
        pass

    from utils.status_sources import heartbeat_poll

    result = heartbeat_poll(
        force_update=args.force,
        force_stale_check=args.stale_check,
    )
    if not args.quiet:
        print(result.get('message') or result)

    gc.collect()
    try:
        from mini_basic.display import ensure_no_pygame_leftovers

        ensure_no_pygame_leftovers()
    except Exception:
        pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
