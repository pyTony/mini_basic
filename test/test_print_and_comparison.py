"""PRINT a>0 AND b>0 printed 0 for true/true — regression.

``_eval_whole_arith`` normalized AND/OR/EOR to &/|/^ (bitwise) before
handing the expression to Python's ``eval``, but those operators bind
tighter than ``<``/``>``/``=`` in Python. ``A>0 AND B>0`` became the text
``A>0 & B>0``, which Python then parsed as the chained comparison
``A > (0 & B) > 0`` instead of two comparisons ANDed together — so
``PRINT 5>0 AND 5>0`` printed 0 instead of -1. ``IF``/assignment used a
different code path (``_eval_numeric``) that already special-cased
boolean syntax, so only ``PRINT``'s fast path was affected.
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


class PrintAndComparisonTests(unittest.TestCase):
    def test_print_and_both_true(self):
        for dialect in ('mini', 'bbc'):
            out = _run(
                ['10 A=5', '20 B=5', '30 PRINT A>0 AND B>0', '40 END'],
                dialect=dialect,
            )
            self.assertEqual(out.strip(), '-1', msg=dialect)

    def test_print_and_one_false(self):
        out = _run(['10 A=5', '20 B=-1', '30 PRINT A>0 AND B>0', '40 END'])
        self.assertEqual(out.strip(), '0')

    def test_print_or_one_true(self):
        out = _run(['10 A=5', '20 B=-1', '30 PRINT A>0 OR B>0', '40 END'])
        self.assertEqual(out.strip(), '-1')

    def test_print_and_matches_assignment_and_if(self):
        lines = [
            '10 A=5',
            '20 B=5',
            '30 PRINT A>0 AND B>0',
            '40 X=A>0 AND B>0',
            '50 PRINT X',
            '60 IF A>0 AND B>0 THEN PRINT -1 ELSE PRINT 0',
            '70 END',
        ]
        out = _run(lines)
        self.assertEqual(out.strip().splitlines(), ['-1', '-1', '-1'])

    def test_print_struct_member_and(self):
        lines = [
            '10 DIM M{W%, H%}',
            '20 M.W% = 10',
            '30 M.H% = 20',
            '40 PRINT M.W% > 0 AND M.H% > 0',
            '50 END',
        ]
        out = _run(lines, dialect='bbc')
        self.assertEqual(out.strip(), '-1')


if __name__ == '__main__':
    unittest.main()
