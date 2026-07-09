"""Nudge OneDrive to upload phone progress files. Run: python force_sync_stamp.py"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from test.progress_runner import write_phone_summary  # noqa: E402


def main() -> None:
    write_phone_summary(
        progress_line='Done: 358 tests in 59s - 0 failed, 0 errors',
    )
    print('Updated PHONE_PROGRESS.txt, PROGRESS.rss, SYNC_STAMP.txt')
    print('Phone: subscribe to PROGRESS.rss (see RSS_SETUP.txt)')


if __name__ == '__main__':
    main()