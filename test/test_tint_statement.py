"""TINT target,level statement: brightness blend on the current text colour.

Distinct from the pre-existing TINT(x,y) pixel-read function (expr.py).
"""
from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stdout

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


def _interp(dialect: str = 'bbc') -> BASICInterpreter:
    return BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )


class TintStatementTests(unittest.TestCase):
    def test_parses_as_statement_not_function(self):
        i = _interp('bbc')
        cmd, rest = i._parse_command('TINT 0, 64')
        self.assertEqual(cmd, 'TINT')
        self.assertEqual(rest.strip(), '0, 64')

    def test_tint_function_form_still_parses_as_expression(self):
        # TINT(x,y) (pixel-read function) must not be swallowed by the
        # TINT statement's command regex.
        i = _interp('bbc')
        cmd, rest = i._parse_command('TINT(0,0)')
        self.assertEqual(cmd, '')

    def test_tint_statement_runs_without_error(self):
        i = _interp('bbc')
        i.set_program_line(10, 'MODE 2')
        i.set_program_line(20, 'COLOUR 5')
        i.set_program_line(30, 'TINT 0, 64')
        i.set_program_line(40, 'PRINT "ok"')
        i.set_program_line(50, 'END')
        buf = io.StringIO()
        with redirect_stdout(buf):
            i.run()
        self.assertEqual(i.error_line_num, 0)
        self.assertIn('ok', buf.getvalue())

    def test_tint_resets_on_new_colour(self):
        i = _interp('bbc')
        i.set_program_line(10, 'MODE 2')
        i.set_program_line(20, 'COLOUR 10')
        i.set_program_line(30, 'TINT 0, 192')
        i.set_program_line(40, 'COLOUR 10')
        i.set_program_line(50, 'END')
        with redirect_stdout(io.StringIO()):
            i.run()
        self.assertEqual(i.error_line_num, 0)
        self.assertEqual(i._bbc_tint_fg, 0)

    def test_tint_blend_is_idempotent_across_repeated_calls(self):
        """Repeated TINT on the same base colour must not compound brightness."""
        i = _interp('bbc')
        i.set_program_line(10, 'MODE 2')
        i.set_program_line(20, 'COLOUR 20')
        i.set_program_line(30, 'TINT 0, 64')
        i.set_program_line(40, 'TINT 0, 64')
        i.set_program_line(50, 'TINT 0, 64')
        i.set_program_line(60, 'END')
        with redirect_stdout(io.StringIO()):
            i.run()
        self.assertEqual(i.error_line_num, 0)
        # Base RGB (for blending) stays untouched by TINT itself.
        self.assertNotIn(20, i._bbc_custom_colours)

    def test_tint_invalid_target_errors(self):
        i = _interp('bbc')
        i.set_program_line(10, 'TINT 2, 64')
        i.set_program_line(20, 'END')
        buf = io.StringIO()
        with redirect_stdout(buf):
            i.run()
        self.assertNotEqual(i.error_line_num, 0)

    def test_mandelbrot_color_archimedes_runs_console(self):
        path = os.path.join(
            _ROOT, 'examples', 'graphics', 'mandelbrot',
            'mandelbrot_color_Archimedes.bas',
        )
        if not os.path.exists(path):
            self.skipTest('mandelbrot_color_Archimedes.bas missing')
        i = _interp('bbc')
        i.load(path, announce=False)
        buf = io.StringIO()
        with redirect_stdout(buf):
            i.run()
        self.assertEqual(i.error_line_num, 0)
        self.assertIn('Finished', buf.getvalue())


if __name__ == '__main__':
    unittest.main()
