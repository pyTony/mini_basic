"""Negative INKEY: BBC internal key numbers, TRUE (-1) only while that key is down."""
from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig
from mini_basic.runtime_parts.graphics import _BBC_NEGATIVE_INKEY_KEYS

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx, pytest.mark.timeout(15)]


def _interp(dialect: str) -> BASICInterpreter:
    return BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )


def _run(interp: BASICInterpreter, src: str) -> tuple[str, str]:
    for raw in src.strip().splitlines():
        num, _, text = raw.partition(' ')
        interp.set_program_line(int(num), text)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        interp.run()
    return out.getvalue(), err.getvalue()


class InkeyScanTests(unittest.TestCase):

    def test_idle_scan_is_false(self):
        for dialect in ('bbc', 'mini'):
            out, err = _run(
                _interp(dialect),
                '10 PRINT INKEY(-99);" ";INKEY-99\n'
                '20 IF INKEY-99 THEN PRINT "p" ELSE PRINT "n"\n',
            )
            self.assertEqual(out.split(), ['0', '0', 'n'], msg=(dialect, err))

    def test_pending_key_matches_only_its_scan_code(self):
        for dialect in ('bbc', 'mini'):
            interp = _interp(dialect)
            keys = iter(['a'])
            interp._inkey_value = lambda: next(keys, '')
            out, err = _run(
                interp,
                '10 PRINT INKEY(-66);" ";INKEY(-98);" ";INKEY(-66)\n',
            )
            # A = -66 (held for the frame, seen twice); Z = -98 not down.
            self.assertEqual(out.split(), ['-1', '0', '-1'], msg=(dialect, err))

    def test_space_escape_return_from_terminal(self):
        interp = _interp('bbc')
        for char, code in ((' ', -99), ('\x1b', -113), ('\r', -74)):
            interp._inkey_scan_held = None
            interp._inkey_value = lambda c=char: c
            self.assertEqual(interp._inkey_bbc_negative_scan(code), -1.0, msg=repr(char))

    def test_key_table_names_common_keys(self):
        self.assertEqual(_BBC_NEGATIVE_INKEY_KEYS[-99], ('K_SPACE',))
        self.assertEqual(_BBC_NEGATIVE_INKEY_KEYS[-122], ('K_RIGHT',))
        self.assertEqual(_BBC_NEGATIVE_INKEY_KEYS[-26], ('K_LEFT',))
        self.assertEqual(_BBC_NEGATIVE_INKEY_KEYS[-58], ('K_UP',))
        self.assertEqual(_BBC_NEGATIVE_INKEY_KEYS[-42], ('K_DOWN',))
        self.assertEqual(_BBC_NEGATIVE_INKEY_KEYS[-66], ('K_a',))
        self.assertEqual(_BBC_NEGATIVE_INKEY_KEYS[-98], ('K_z',))
        self.assertEqual(_BBC_NEGATIVE_INKEY_KEYS[-113], ('K_ESCAPE',))

    def test_pygame_window_reads_held_keys_and_mouse(self):
        class FakeKeys(dict):
            def __missing__(self, key):
                return False

        class FakePygame:
            K_SPACE, K_z, K_RIGHT = 32, 122, 1073741903

            class event:
                @staticmethod
                def pump():
                    pass

            class key:
                @staticmethod
                def get_pressed():
                    return FakeKeys({32: True})  # space held

            class mouse:
                @staticmethod
                def get_pressed():
                    return (True, False, False)  # left button

            @staticmethod
            def get_init():
                return True

        class FakeDisplay:
            _pygame = FakePygame

        interp = _interp('bbc')
        interp._display = FakeDisplay()
        interp._display_enabled = lambda: True
        self.assertEqual(
            [interp._inkey_bbc_negative_scan(n) for n in (-99, -98, -122, -10, -12)],
            [-1.0, 0.0, 0.0, -1.0, 0.0],
        )

    def test_platform_id_unchanged(self):
        self.assertEqual(_interp('bbc')._inkey_bbc_negative_scan(-256), 115.0)


if __name__ == '__main__':
    unittest.main()
