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

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


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

    def test_case_sensitive_keywords_uppercase_only_all_dialects(self):
        """Any dialect with case on: uppercase keywords only."""
        for dialect in ('bbc', 'mini', 'mits', 'commodore', 'tiny'):
            i = BASICInterpreter(
                InterpreterConfig(
                    dialect=dialect,
                    display='none',
                    display_locked=True,
                    identifiers_case_sensitive=True,
                )
            )
            self.assertTrue(i._identifiers_case_sensitive())
            cmd, rest = i._parse_command('PRINT 1')
            self.assertEqual(cmd, 'PRINT', msg=dialect)
            self.assertEqual(rest.strip(), '1')
            for src in ('print 1', 'Print 1'):
                cmd, _ = i._parse_command(src)
                self.assertEqual(cmd, '', msg=f'{dialect} {src}')
            # bbc/mini share COLOUR; others may not execute it, but parse is shared
            if dialect in ('bbc', 'mini'):
                self.assertEqual(i._parse_command('COLOUR 15')[0], 'COLOUR')
                for src in ('Colour 15', 'colour 15', 'Colour&() = 1'):
                    self.assertEqual(i._parse_command(src)[0], '', msg=f'{dialect} {src}')

    def test_case_fold_allows_lower_keywords_all_dialects(self):
        for dialect in ('bbc', 'mini', 'mits'):
            i = BASICInterpreter(
                InterpreterConfig(
                    dialect=dialect,
                    display='none',
                    display_locked=True,
                    identifiers_case_sensitive=False,
                )
            )
            cmd, rest = i._parse_command('print 1')
            self.assertEqual(cmd, 'PRINT', msg=dialect)
            self.assertEqual(rest.strip(), '1')
            if dialect in ('bbc', 'mini'):
                cmd, rest = i._parse_command('colour 15')
                self.assertEqual(cmd, 'COLOUR', msg=dialect)
                # Type suffix still wins over statement
                self.assertEqual(i._parse_command('colour&() = 1, 2')[0], '')

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

    def test_piechart_compact_if_or_assign(self):
        """piechart: IF Y% = Cy% + Depth Colour&() OR= 8 (no THEN)."""
        i = _interp('bbc')
        rest = 'Y% = Cy% + Depth Colour&() OR= 8'
        cond, body = i._split_bbc_compact_if_then(rest)
        self.assertEqual(cond, 'Y% = Cy% + Depth')
        self.assertEqual(body, 'Colour&() OR= 8')
        lhs, op, rhs = i._parse_assignment_statement(body)
        self.assertEqual(lhs, 'Colour&()')
        self.assertEqual(op, 'OR=')
        self.assertEqual(rhs, '8')

        i.set_program_line(10, 'DIM Colour&(2)')
        i.set_program_line(20, 'Colour&() = 1, 2, 3')
        i.set_program_line(30, 'Y% = 5')
        i.set_program_line(40, 'Cy% = 0')
        i.set_program_line(50, 'Depth = 5')
        i.set_program_line(60, 'IF Y% = Cy% + Depth Colour&() OR= 8')
        i.set_program_line(70, 'PRINT Colour&(0), Colour&(1), Colour&(2)')
        i.set_program_line(80, 'END')
        buf = io.StringIO()
        with redirect_stdout(buf):
            i.run()
        self.assertEqual(i.error_line_num, 0)
        # 1|8=9, 2|8=10, 3|8=11
        self.assertIn('9', buf.getvalue())
        self.assertIn('10', buf.getvalue())
        self.assertIn('11', buf.getvalue())
        # aand=0 must not become AND=
        lhs, op, rhs = i._parse_assignment_statement('aand=0')
        self.assertEqual(lhs, 'aand')
        self.assertEqual(op, '=')
        self.assertEqual(rhs, '0')


if __name__ == '__main__':
    unittest.main()
