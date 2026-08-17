"""Phase A VDU codes: 17, 20, 30, 8-11, 13, 7, 26."""
from __future__ import annotations

import os
import sys
import unittest
from io import StringIO
from contextlib import redirect_stdout

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]


class VduPhaseATests(unittest.TestCase):
    def make_interp(self) -> BASICInterpreter:
        return BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', optimization_level=0),
        )

    def run_lines(self, lines) -> BASICInterpreter:
        interp = self.make_interp()
        for num, stmt in lines:
            interp.program[num] = stmt
        with redirect_stdout(StringIO()):
            interp.run()
        return interp

    def test_vdu_17_sets_fg_like_colour(self):
        interp = self.run_lines([
            (10, 'VDU 17,1'),
            (20, 'END'),
        ])
        self.assertEqual(interp.text_fg_colour, 1)

    def test_vdu_17_bg_when_code_ge_128(self):
        interp = self.run_lines([
            (10, 'VDU 17,129'),
            (20, 'END'),
        ])
        self.assertEqual(interp.text_bg_colour, 1)

    def test_vdu_20_resets_text_colours(self):
        interp = self.run_lines([
            (10, 'VDU 17,3'),
            (20, 'VDU 17,130'),
            (30, 'VDU 20'),
            (40, 'END'),
        ])
        self.assertEqual(interp.text_fg_colour, 7)
        self.assertEqual(interp.text_bg_colour, 0)

    def test_vdu_30_homes_cursor(self):
        interp = self.run_lines([
            (10, 'VDU 31,5,4'),
            (20, 'VDU 30'),
            (30, 'END'),
        ])
        self.assertEqual(interp.text_col, 0)
        self.assertEqual(interp.text_row, 0)
        self.assertEqual(interp.print_column, 0)

    def test_vdu_8_9_10_11_13_cursor_moves(self):
        interp = self.run_lines([
            (10, 'VDU 31,5,5'),
            (20, 'VDU 8'),   # left
            (30, 'VDU 9'),   # right
            (40, 'VDU 9'),   # right
            (50, 'VDU 11'),  # up
            (60, 'VDU 10'),  # down
            (70, 'VDU 13'),  # CR
            (80, 'END'),
        ])
        # 5,5 -> 4,5 -> 5,5 -> 6,5 -> 6,4 -> 6,5 -> 0,5
        self.assertEqual(interp.text_col, 0)
        self.assertEqual(interp.text_row, 5)

    def test_vdu_7_bell_no_error(self):
        out = StringIO()
        interp = self.make_interp()
        interp.program[10] = 'VDU 7'
        interp.program[20] = 'END'
        with redirect_stdout(out):
            interp.run()
        # BEL may appear in stdout; must not raise
        self.assertIn('\a', out.getvalue() + '')

    def test_vdu_26_clears_viewport_state(self):
        interp = self.make_interp()
        interp._text_viewport = (0, 0, 10, 10)
        interp._graphics_viewport = (0, 0, 100, 100)
        interp.program[10] = 'VDU 26'
        interp.program[20] = 'END'
        with redirect_stdout(StringIO()):
            interp.run()
        self.assertIsNone(interp._text_viewport)
        self.assertIsNone(interp._graphics_viewport)

    def test_vdu_chain_20_26_30_no_error(self):
        """bbcowl-style VDU 20,26,12 style chain without runtime errors."""
        interp = self.run_lines([
            (10, 'VDU 20,26,30'),
            (20, 'END'),
        ])
        self.assertEqual(interp.text_fg_colour, 7)
        self.assertEqual(interp.text_col, 0)
        self.assertEqual(interp.text_row, 0)

    def test_bbc_heap_bang_and_query(self):
        interp = self.make_interp()
        addr = interp._bbc_alloc(40)
        interp.int_variables['p%%'] = addr
        interp._bbc_heap[addr][10:14] = (1234).to_bytes(4, 'little', signed=True)
        interp._bbc_heap[addr][28] = 24
        self.assertEqual(int(interp.eval_expr('p%%!10')), 1234)
        self.assertEqual(int(interp.eval_expr('p%%?28')), 24)
        self.assertEqual(int(interp.eval_expr('p%%?(20+8)')), 24)

    def test_vdu_bar_terminator_and_expression(self):
        """snowscene: VDU 23,23,1| and VDU 23,23,1.4^depth%|"""
        interp = self.make_interp()
        codes = interp._parse_vdu_operands('23,23,1|')
        self.assertEqual(codes[:3], [23, 23, 1])
        self.assertEqual(codes[3:12], [0] * 9)
        codes = interp._parse_vdu_operands('23,23,1.4^2|')
        self.assertEqual(codes[0], 23)
        self.assertEqual(codes[1], 23)
        self.assertEqual(codes[2], int(1.4 ** 2))
        with self.assertRaises(ValueError) as ctx:
            interp._parse_vdu_operands('23,notanumber')
        self.assertIn('bad operand', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
