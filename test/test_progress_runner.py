"""Status / idle logic for progress_runner."""
from __future__ import annotations

import os
import unittest

from test import progress_runner as pr


class ProgressRunnerStatusTests(unittest.TestCase):
    def test_work_not_complete_when_todos_remain(self) -> None:
        original = pr._load_features_done_lines
        try:
            pr._load_features_done_lines = lambda: ['-- animal.txt fix']
            self.assertFalse(pr._work_complete())
        finally:
            pr._load_features_done_lines = original

    def test_work_not_complete_when_last_test_incomplete(self) -> None:
        log_path = pr._LOG_PATH
        if not os.path.isfile(log_path):
            self.skipTest('no test log')
        with open(log_path, encoding='utf-8') as handle:
            content = handle.read()
        if 'Finished ' not in content:
            self.assertFalse(pr._work_complete())

    def test_last_work_stamp_prefers_work_log(self) -> None:
        original = pr._WORK_LOG_PATH
        path = os.path.join(pr._ROOT_DIR, 'WORK_LOG.txt')
        self.assertTrue(os.path.isfile(path))
        stamp = pr._last_work_log_stamp()
        self.assertIsNotNone(stamp)
        self.assertEqual(pr._last_work_stamp(), stamp)

    def test_heartbeat_status_is_compact(self) -> None:
        lines = pr._minimal_status_lines(
            sync_id=1,
            heartbeat_id=99,
            stamp='2026-06-23 12:00:00',
            heartbeat=True,
            test_line=None,
            progress_line=None,
        )
        text = '\n'.join(lines)
        self.assertIn('alive check #99', text)
        self.assertNotIn('heartbeat every 60 sec', text)
        self.assertNotIn('done DEFINT', text)
        self.assertNotIn('programs to try', text)
        self.assertIn('TODO', text)
        self.assertIn('work log newest first', text)

    def test_work_log_recent_is_newest_first(self) -> None:
        recent = pr._load_work_log_recent(3)
        self.assertGreaterEqual(len(recent), 2)
        self.assertTrue(recent[0].startswith('2026-'))
        self.assertGreater(recent[0], recent[-1])

    def test_status_html_dashboard_sections(self) -> None:
        html = pr._build_status_html(
            [],
            sync_id=1,
            heartbeat_id=42,
            stamp='2026-06-23 12:00:00',
            heartbeat=True,
        )
        self.assertIn('mini_basic Progress Dashboard', html)
        self.assertIn('Currently Working On', html)
        self.assertIn('Confirmed Working', html)
        self.assertIn('Pending / Not Yet Confirmed', html)
        self.assertIn('Recent Work Log', html)
        self.assertIn('heartbeat #42', html)
        self.assertNotIn('setInterval', html)

    def test_work_log_registers_to_status_html(self) -> None:
        """USER/work events in WORK_LOG.txt must appear in Recent Work Log."""
        marker = 'status-html-register-test-marker-7f3a'
        pr.log_work_event(marker, kind='INFO')
        kwargs = pr._status_update_kwargs(
            sync_id=1,
            heartbeat_id=1,
            stamp='2026-07-02 12:00:00',
            heartbeat=False,
        )
        recent = kwargs.get('recent_log') or []
        self.assertTrue(
            any(marker in entry for entry in recent),
            f'{marker!r} missing from recent_log: {recent[:3]}',
        )


if __name__ == '__main__':
    unittest.main()