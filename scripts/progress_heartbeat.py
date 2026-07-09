"""One-shot: write PHONE_PROGRESS / SYNC_STAMP then exit (no process left open).

Scheduled every minute via register_progress_task.ps1
Manual: python progress_heartbeat.py
"""
from __future__ import annotations

import os
import sys

# Heartbeat must never open SDL/pygame windows if any import chain touches display code.
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from test.progress_runner import write_phone_summary  # noqa: E402


def main() -> int:
    write_phone_summary(heartbeat=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())