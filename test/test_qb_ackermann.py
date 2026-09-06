"""QBasic-ish Ackermann listing: tail ' comments, TIMER, END FUNCTION."""
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


def _run(lines, dialect='mini'):
    interp = BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )
    buf = io.StringIO()
    with redirect_stdout(buf):
        for i, line in enumerate(lines, 1):
            interp.set_program_line(i * 10, line)
        interp.run()
    return buf.getvalue(), interp


class QBasicAckermannListingTests(unittest.TestCase):
    def test_tail_apostrophe_comment_on_assignment(self):
        out, interp = _run([
            "T1 = TIMER ' Start the benchmark clock",
            'PRINT T1',
            'END',
        ])
        self.assertNotIn('unterminated', out.lower())
        self.assertNotIn('?', out)
        self.assertGreaterEqual(float(interp.variables.get('T1', 0)), 0.0)

    def test_print_apostrophe_newline_unchanged(self):
        out, _ = _run([
            'PRINT "A\'B"',
            'END',
        ])
        self.assertIn("A'B", out)

    def test_ackermann_1_1(self):
        out, _ = _run([
            'M=1: N=1',
            'PRINT FNACK(M, N)',
            'END',
            'DEF FNACK(M, N)',
            'IF M = 0 THEN FNACK = N + 1: EXIT FUNCTION',
            'IF N = 0 THEN FNACK = FNACK(M - 1, 1): EXIT FUNCTION',
            'FNACK = FNACK(M - 1, FNACK(M, N - 1))',
            'END FUNCTION',
        ])
        self.assertNotIn('?', out)
        self.assertIn('3', out.strip().splitlines()[-1])

    def test_ackermann_2_2(self):
        out, _ = _run([
            'PRINT FNACK(2, 2)',
            'END',
            'DEF FNACK(M, N)',
            'IF M = 0 THEN FNACK = N + 1: EXIT FUNCTION',
            'IF N = 0 THEN FNACK = FNACK(M - 1, 1): EXIT FUNCTION',
            'FNACK = FNACK(M - 1, FNACK(M, N - 1))',
            'END FUNCTION',
        ])
        self.assertNotIn('?', out)
        self.assertIn('7', out.strip().splitlines()[-1])


if __name__ == '__main__':
    unittest.main()
