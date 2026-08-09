"""Colour&() is a byte array name, not the COLOUR statement (piechart)."""
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

pytestmark = [pytest.mark.phase0]


def _interp(dialect: str = 'bbc') -> BASICInterpreter:
    return BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )


class ColourArrayNameTests(unittest.TestCase):
    def test_colour_amp_not_colour_statement_bbc_and_mini(self):
        for dialect in ('bbc', 'mini'):
            i = _interp(dialect)
            for src in (
                'Colour&() = 1, 2, 3',
                'COLOUR&() = 1, 2, 3',
                'colour&() = 1, 2, 3',
            ):
                cmd, rest = i._parse_command(src)
                self.assertEqual(cmd, '', msg=f'{dialect} {src!r}')
                self.assertIn('&()', rest.replace(' ', ''))
            cmd, rest = i._parse_command('COLOUR 15')
            self.assertEqual(cmd, 'COLOUR')
            self.assertEqual(rest.strip(), '15')

    def test_whole_array_compound_with_sum_in_rhs(self):
        i = _interp('bbc')
        lhs, op, rhs = i._parse_assignment_statement(
            'Value() *= 2 * PI / SUM(Value())'
        )
        self.assertEqual(lhs, 'Value()')
        self.assertEqual(op, '*=')
        self.assertIn('SUM(Value())', rhs)

        i.set_program_line(10, 'DIM Value(2)')
        i.set_program_line(20, 'Value() = 3.45, 4.56, 5.67')
        i.set_program_line(30, 'Value() *= 2 * PI / SUM(Value())')
        i.set_program_line(40, 'PRINT Value(0)')
        i.set_program_line(50, 'END')
        buf = io.StringIO()
        with redirect_stdout(buf):
            i.run()
        self.assertEqual(i.error_line_num, 0)
        self.assertNotIn('?', buf.getvalue())
        # Scaled so SUM is 2*PI ≈ 6.28; first slice ~1.59
        self.assertAlmostEqual(float(buf.getvalue().strip()), 1.589, places=2)

    def test_colour_byte_array_assign_runs(self):
        i = _interp('bbc')
        i.set_program_line(10, 'DIM Colour&(2)')
        i.set_program_line(20, 'Colour&() = 1, 2, 3')
        i.set_program_line(30, 'PRINT Colour&(0), Colour&(2)')
        i.set_program_line(40, 'END')
        buf = io.StringIO()
        with redirect_stdout(buf):
            i.run()
        self.assertEqual(i.error_line_num, 0)
        self.assertIn('1', buf.getvalue())
        self.assertIn('3', buf.getvalue())


if __name__ == '__main__':
    unittest.main()
