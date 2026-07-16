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

from test.progress_runner import update_project_status  # noqa: E402
from utils.status_updater import StatusUpdater  # noqa: E402


def main() -> int:
    import gc
    # Lightweight heartbeat for repeated agent work: minimal memory footprint
    gc.collect()
    # Pygame safety per AGENT_POLICY §8 — never leave windows in autonomous scheduled runs.
    try:
        from mini_basic.display import ensure_no_pygame_leftovers
        ensure_no_pygame_leftovers()
    except Exception:
        pass
    # Update status.html only (local dev tree + source/OneDrive for remote check)
    update_project_status(heartbeat=True)
    StatusUpdater().update(is_heartbeat=True)
    gc.collect()
    try:
        from mini_basic.display import ensure_no_pygame_leftovers
        ensure_no_pygame_leftovers()
    except Exception:
        pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())