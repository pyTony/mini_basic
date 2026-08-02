"""Pygame INPUT must not drop keyboard events before read_line sees them."""
from __future__ import annotations

import os
import sys
import unittest
from unittest import mock

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic.display import PygameDisplay


class _FakeEvent:
    def __init__(self, type_id: int, **attrs):
        self.type = type_id
        for key, value in attrs.items():
            setattr(self, key, value)


class PygameInputEventTests(unittest.TestCase):
    def test_poll_preserves_keyboard_events(self) -> None:
        display = PygameDisplay(caption='test', scale=1)
        posted = []

        class FakePygame:
            QUIT = 1
            KEYDOWN = 2
            K_ESCAPE = 27

            @staticmethod
            def event_pump():
                return None

            class event:
                @staticmethod
                def pump():
                    return None

                @staticmethod
                def get():
                    return [_FakeEvent(2, key=ord('y'), unicode='y')]

                @staticmethod
                def post(evt):
                    posted.append(evt)

        display._pygame = FakePygame()
        display._open = True
        with mock.patch.dict(os.environ, {'SDL_VIDEODRIVER': 'windib'}), mock.patch.object(
            display, '_update_mouse_state',
        ):
            self.assertTrue(display.poll())
        self.assertEqual(len(posted), 1)
        self.assertEqual(posted[0].unicode, 'y')

    def test_pump_events_does_not_drain_queue(self) -> None:
        display = PygameDisplay(caption='test', scale=1)
        drained = []

        class FakePygame:
            @staticmethod
            def get_init():
                return True

            class event:
                @staticmethod
                def pump():
                    return None

                @staticmethod
                def get():
                    drained.append(True)
                    return []

        display._pygame = FakePygame()
        display._open = True
        display.pump_events()
        self.assertEqual(drained, [])


if __name__ == '__main__':
    unittest.main()
