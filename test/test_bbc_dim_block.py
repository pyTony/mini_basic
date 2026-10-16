"""BBC DIM p n memory blocks with ? and ! indirection (examples/graphics/flood.bbc)."""
from __future__ import annotations

import os
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]


class BbcDimBlockTests(unittest.TestCase):
    def run_lines(self, lines, dialect='bbc'):
        interp = BASICInterpreter(
            InterpreterConfig(dialect=dialect, display='none', optimization_level=0),
        )
        for num, stmt in enumerate(lines, start=1):
            interp.program[num * 10] = stmt
        out = StringIO()
        with redirect_stdout(out):
            interp.run()
        return interp, out.getvalue()

    def test_dim_plain_var_block_bytes(self):
        interp, out = self.run_lines([
            'DIM p 8',
            '?p=65 : p?1=66 : p?8=67',
            'PRINT ?p;" ";p?1;" ";p?8;" ";?(p+1)',
        ])
        self.assertIn('65 66 67 66', out)
        self.assertNotIn('?', out)
        self.assertEqual(len(interp._bbc_heap[int(interp.eval_expr('p'))]), 9)

    def test_dim_int_var_block_words(self):
        _, out = self.run_lines([
            'DIM q% 7',
            'q%!4=123456 : i%=4',
            'PRINT q%!4;" ";q%?i%',
        ])
        self.assertIn('123456 64', out)

    def test_mini_postfix_store_keeps_question_print(self):
        _, out = self.run_lines([
            'DIM p 3',
            'p?2=9',
            'PRINT p?2',
            '? "hi"',
        ], dialect='mini')
        self.assertIn('9', out)
        self.assertIn('hi', out)
        self.assertNotIn('?', out)

    def test_array_dim_unchanged(self):
        _, out = self.run_lines(['DIM a(3)', 'a(3)=5', 'PRINT a(3)'])
        self.assertIn('5', out)


if __name__ == '__main__':
    unittest.main()
