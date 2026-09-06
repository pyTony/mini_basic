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

    def test_saved_ackermann_bas_tail_comments(self):
        path = os.path.join(_ROOT, 'basics', 'ackermann.bas')
        if not os.path.isfile(path):
            self.skipTest('basics/ackermann.bas missing')
        interp = BASICInterpreter(
            InterpreterConfig(dialect='mini', display='none', display_locked=True)
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.load(path, announce=False)
            interp.set_program_line(30, 'M=1')
            interp.set_program_line(40, 'N=1')
            interp.run()
        out = buf.getvalue()
        self.assertNotIn('unterminated', out.lower())
        self.assertNotIn('needs =return', out)
        self.assertIn('3', out)

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

    def test_ackermann_3_4(self):
        out, interp = _run([
            'PRINT FNACK(3, 4)',
            'END',
            'DEF FNACK(M, N)',
            'IF M = 0 THEN FNACK = N + 1: EXIT FUNCTION',
            'IF N = 0 THEN FNACK = FNACK(M - 1, 1): EXIT FUNCTION',
            'FNACK = FNACK(M - 1, FNACK(M, N - 1))',
            'END FUNCTION',
        ])
        self.assertNotIn('?', out)
        self.assertEqual(out.strip().splitlines()[-1].strip(), '125')
        self.assertTrue(interp._fn_memoable.get('ACK', False))

    def test_ackermann_4_1(self):
        out, _ = _run([
            'PRINT FNACK(4, 1)',
            'END',
            'DEF FNACK(M, N)',
            'IF M = 0 THEN FNACK = N + 1: EXIT FUNCTION',
            'IF N = 0 THEN FNACK = FNACK(M - 1, 1): EXIT FUNCTION',
            'FNACK = FNACK(M - 1, FNACK(M, N - 1))',
            'END FUNCTION',
        ])
        self.assertNotIn('?', out)
        self.assertEqual(out.strip().splitlines()[-1].strip(), '65533')

    def test_impure_global_not_memoized(self):
        out, interp = _run([
            'G=1',
            'PRINT FNx',
            'G=2',
            'PRINT FNx',
            'END',
            'DEF FNx()=G',
        ])
        self.assertNotIn('?', out)
        lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
        self.assertEqual(lines[-2:], ['1', '2'])
        self.assertFalse(any(interp._fn_memoable.get(k) for k in ('X', 'x')))

    def test_only_recursive_fn_is_memoized(self):
        out, interp = _run([
            'PRINT FNdouble(3); FNfact(5)',
            'END',
            'DEF FNdouble(N)=2*N',
            'DEF FNfact(N)',
            'IF N<=1 THEN FNfact=1: EXIT FUNCTION',
            'FNfact = N * FNfact(N-1)',
            'END FUNCTION',
        ])
        self.assertNotIn('?', out)
        self.assertIn('6', out)
        self.assertIn('120', out)
        keys = {str(k).upper(): v for k, v in interp._fn_memoable.items()}
        self.assertFalse(keys.get('DOUBLE', False))
        self.assertTrue(keys.get('FACT', False))

    def test_fn_name_assign_then_structured_if_cap(self):
        """QBasic FNname= plus IF/ENDIF must not jump to END DEF."""
        out20, _ = _run([
            'PRINT FNCALC(20)',
            'END',
            'DEF FNCALC(X)',
            'FNCALC = X * 2',
            'IF FNCALC > 100 THEN',
            'FNCALC = 100',
            'ENDIF',
            'END DEF',
        ])
        self.assertNotIn('?', out20)
        self.assertNotIn('jump outside', out20.lower())
        self.assertEqual(out20.strip().splitlines()[-1].strip(), '40')

        out60, _ = _run([
            'PRINT FNCALC(60)',
            'END',
            'DEF FNCALC(X)',
            'FNCALC = X * 2',
            'IF FNCALC > 100 THEN',
            'FNCALC = 100',
            'ENDIF',
            'END DEF',
        ])
        self.assertNotIn('?', out60)
        self.assertEqual(out60.strip().splitlines()[-1].strip(), '100')


if __name__ == '__main__':
    unittest.main()
