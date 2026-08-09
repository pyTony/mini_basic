"""Dialect hint lines: portable numbered REM + legacy apostrophe/line 0."""
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

_ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig
from mini_basic.dialect_hint import (
    first_free_hint_line_number,
    format_save_dialect_hint,
    parse_comment_dialect_line,
    split_dialect_hints,
)

pytestmark = [pytest.mark.phase0]


class DialectHintTests(unittest.TestCase):
    def test_apostrophe_dialect_line_parses(self):
        hint = parse_comment_dialect_line("' dialect: bbc")
        self.assertIsNotNone(hint)
        self.assertEqual(hint.dialect, 'bbc')
        self.assertEqual(hint.source, 'apostrophe')

    def test_numbered_rem_dialect_parses(self):
        hint = parse_comment_dialect_line("1 REM dialect: bbc")
        self.assertIsNotNone(hint)
        self.assertEqual(hint.dialect, 'bbc')
        self.assertEqual(hint.source, 'rem')

    def test_split_strips_apostrophe_header(self):
        lines, hint = split_dialect_hints(["' dialect: bbc\n", "10 PRINT 1\n"])
        self.assertEqual(hint.dialect if hint else None, 'bbc')
        self.assertEqual(len(lines), 1)
        self.assertIn('PRINT', lines[0])

    def test_split_strips_numbered_rem_header(self):
        lines, hint = split_dialect_hints(["1 REM dialect: bbc\n", "10 PRINT 1\n"])
        self.assertEqual(hint.dialect if hint else None, 'bbc')
        self.assertEqual(len(lines), 1)
        self.assertIn('10', lines[0])

    def test_format_save_hint_uses_rem_line_one(self):
        self.assertEqual(
            format_save_dialect_hint('bbc', program_line_numbers={10, 20}),
            '1 REM dialect: bbc',
        )
        self.assertEqual(
            format_save_dialect_hint('bbc', program_line_numbers={1, 10}),
            '2 REM dialect: bbc',
        )
        self.assertIsNone(format_save_dialect_hint('mini', program_line_numbers={10}))
        self.assertEqual(
            format_save_dialect_hint('bbc', numbered=False),
            'REM dialect: bbc',
        )
        self.assertEqual(first_free_hint_line_number({0, 2}), 1)

    def test_save_emits_numbered_rem_not_apostrophe(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.program = {10: 'PRINT 1', 20: 'END'}
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.bas', delete=False, encoding='utf-8',
        ) as handle:
            path = handle.name
        try:
            os.unlink(path)
            with redirect_stdout(io.StringIO()):
                interp.save(path)
            text = open(path, encoding='utf-8').read()
            self.assertTrue(text.startswith('1 REM dialect: bbc\n'), text[:80])
            self.assertNotIn("' dialect:", text)
            self.assertNotRegex(text, r'(?m)^0\s')
        finally:
            if os.path.isfile(path):
                os.unlink(path)

    def test_line_one_rem_dialect_on_run(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none'))
        interp.program = {
            1: 'REM dialect: bbc',
            10: 'PRINT "ok"',
            20: 'END',
        }
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        self.assertEqual(interp.config.dialect, 'bbc')
        self.assertEqual(buf.getvalue().strip(), 'ok')

    def test_legacy_line_zero_apostrophe_still_applies(self):
        """Old examples used line 0 + apostrophe; still recognized in-program."""
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none'))
        interp.program = {
            0: "' dialect: bbc",
            10: 'PRINT "ok"',
            20: 'END',
        }
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        self.assertEqual(interp.config.dialect, 'bbc')
        self.assertEqual(buf.getvalue().strip(), 'ok')

    def test_line_zero_dialect_and_mode_enable_pygame_before_run(self):
        # Hermetic env: user/shell MINIBASIC_NO_GRAPHICS must not block auto-enable.
        env = {
            'SDL_VIDEODRIVER': 'dummy',
            'MINIBASIC_NO_GRAPHICS': '',
            'MINIBASIC_DISPLAY': '',
        }
        with patch.dict(os.environ, env, clear=False):
            for key in ('MINIBASIC_NO_GRAPHICS', 'MINIBASIC_DISPLAY'):
                if not os.environ.get(key):
                    os.environ.pop(key, None)
            with patch(
                'mini_basic.util.session.session_supports_gui',
                return_value=True,
            ), patch(
                'mini_basic.display.pygame_available',
                return_value=True,
            ):
                interp = BASICInterpreter(
                    InterpreterConfig(
                        dialect='mini',
                        display='terminal',
                        hold_display_open=False,
                    ),
                )
                interp.program = {
                    1: 'REM dialect: bbc',
                    10: 'MODE 2',
                    20: 'GCOL 0, 1',
                    30: 'END',
                }
                try:
                    with redirect_stdout(io.StringIO()):
                        interp._apply_dialect_hints_from_program(announce=False)
                        interp._maybe_auto_enable_pygame_from_program(announce=False)
                    self.assertEqual(interp.config.dialect, 'bbc')
                    self.assertEqual(interp.config.display, 'pygame')
                finally:
                    interp._shutdown_display(hold=False)

    def test_gcol_enables_pygame_mid_run_when_only_mode_in_program(self):
        env = {
            'SDL_VIDEODRIVER': 'dummy',
            'MINIBASIC_NO_GRAPHICS': '',
            'MINIBASIC_DISPLAY': '',
        }
        with patch.dict(os.environ, env, clear=False):
            for key in ('MINIBASIC_NO_GRAPHICS', 'MINIBASIC_DISPLAY'):
                if not os.environ.get(key):
                    os.environ.pop(key, None)
            with patch(
                'mini_basic.util.session.session_supports_gui',
                return_value=True,
            ), patch(
                'mini_basic.display.pygame_available',
                return_value=True,
            ):
                interp = BASICInterpreter(
                    InterpreterConfig(
                        dialect='mini',
                        display='terminal',
                        hold_display_open=False,
                    ),
                )
                interp.program = {
                    10: 'MODE 2',
                    20: 'GCOL 0, 1',
                    30: 'END',
                }
                try:
                    with redirect_stdout(io.StringIO()):
                        with patch.object(
                            interp, '_shutdown_display', lambda *a, **k: None,
                        ):
                            interp.run()
                    self.assertEqual(interp.config.display, 'pygame')
                finally:
                    try:
                        interp._shutdown_display(hold=False)
                    except Exception:
                        pass


if __name__ == '__main__':
    unittest.main()
