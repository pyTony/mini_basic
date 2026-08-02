"""Dialect hint lines: REM and apostrophe (SAVE/EDIT line 0)."""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

_ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig
from mini_basic.dialect_hint import parse_comment_dialect_line, split_dialect_hints

pytestmark = [pytest.mark.phase0]


class DialectHintTests(unittest.TestCase):
    def test_apostrophe_dialect_line_parses(self):
        hint = parse_comment_dialect_line("' dialect: bbc")
        self.assertIsNotNone(hint)
        self.assertEqual(hint.dialect, 'bbc')
        self.assertEqual(hint.source, 'apostrophe')

    def test_split_strips_apostrophe_header(self):
        lines, hint = split_dialect_hints(["' dialect: bbc\n", "10 PRINT 1\n"])
        self.assertEqual(hint.dialect if hint else None, 'bbc')
        self.assertEqual(len(lines), 1)
        self.assertIn('PRINT', lines[0])

    def test_line_zero_apostrophe_dialect_on_run(self):
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

    @unittest.skip(reason="Hangs because display stays open")
    def test_line_zero_dialect_and_mode_enable_pygame_before_run(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='terminal'))
        interp.program = {
            0: "' dialect: bbc",
            10: 'MODE 2',
            20: 'GCOL 0, 1',
            30: 'END',
        }
        with redirect_stdout(io.StringIO()):
            interp._apply_dialect_hints_from_program(announce=False)
            interp._maybe_auto_enable_pygame_from_program(announce=False)
        self.assertEqual(interp.config.dialect, 'bbc')
        self.assertEqual(interp.config.display, 'pygame')

    @unittest.skip(reason="Hangs because display stays open")
    def test_gcol_enables_pygame_mid_run_when_only_mode_in_program(self):
        old_driver = os.environ.get('SDL_VIDEODRIVER')
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        interp = BASICInterpreter(
            InterpreterConfig(dialect='mini', display='terminal', hold_display_open=False),
        )
        interp.program = {
            10: 'MODE 2',
            20: 'GCOL 0, 1',
            30: 'END',
        }
        try:
            with redirect_stdout(io.StringIO()):
                interp.run()
            self.assertEqual(interp.config.display, 'pygame')
        finally:
            interp._shutdown_display()
            if old_driver is None:
                os.environ.pop('SDL_VIDEODRIVER', None)
            else:
                os.environ['SDL_VIDEODRIVER'] = old_driver
            

if __name__ == '__main__':
    unittest.main()
