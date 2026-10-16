"""PRINT array subscript expansion — regression for former known gap."""
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


def _run(lines: list[str], dialect: str = 'mini') -> str:
    cfg = InterpreterConfig(display='none', display_locked=True, dialect=dialect)
    interp = BASICInterpreter(cfg)
    buf = io.StringIO()
    with redirect_stdout(buf):
        for raw in lines:
            num_s, stmt = raw.split(' ', 1)
            interp.set_program_line(int(num_s), stmt)
        interp.run()
    return buf.getvalue()


class PrintArraySubscriptTests(unittest.TestCase):
    def test_print_numeric_1d(self):
        out = _run(['10 DIM A(5)', '20 A(0)=42', '30 PRINT A(0)', '40 END'])
        self.assertEqual(out.strip(), '42')

    def test_print_numeric_1d_trailing_semicolon(self):
        out = _run(['10 DIM A(5)', '20 A(0)=42', '30 PRINT A(0);', '40 END'])
        self.assertEqual(out, '42')

    def test_print_numeric_2d(self):
        out = _run(['10 DIM A(2,2)', '20 A(1,1)=7', '30 PRINT A(1,1)', '40 END'])
        self.assertEqual(out.strip(), '7')

    def test_print_string_array(self):
        out = _run(['10 DIM A$(5)', '20 A$(0)="hi"', '30 PRINT A$(0)', '40 END'])
        self.assertEqual(out.strip(), 'hi')

    def test_print_int_array(self):
        out = _run(['10 DIM A%(5)', '20 A%(0)=3', '30 PRINT A%(0)', '40 END'])
        self.assertEqual(out.strip(), '3')

    def test_print_with_index_expr(self):
        out = _run(
            [
                '10 DIM A(5)',
                '20 FOR I=0 TO 2',
                '30 A(I)=I*10',
                '40 NEXT I',
                '50 PRINT A(1)',
                '60 END',
            ]
        )
        self.assertEqual(out.strip(), '10')

    def test_print_juxtaposed_with_literals(self):
        out = _run(
            ['10 DIM A(5)', '20 A(0)=1', '30 PRINT "x";A(0);"y"', '40 END']
        )
        self.assertIn('x1y', out)

    def test_print_array_in_expression(self):
        out = _run(['10 DIM A(5)', '20 A(0)=5', '30 PRINT A(0)+1', '40 END'])
        self.assertEqual(out.strip(), '6')

    def test_print_after_tab(self):
        out = _run(['10 DIM A(5)', '20 A(0)=5', '30 PRINT TAB(5);A(0)', '40 END'])
        self.assertTrue(out.rstrip('\n').endswith('5'))


if __name__ == '__main__':
    unittest.main()
