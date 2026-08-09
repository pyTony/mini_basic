"""Phase 1 entry-time line canonicalize (dual-normalize with runtime unglue)."""
from __future__ import annotations

import os
import sys
import unittest

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0]


class EntryCanonicalizeTests(unittest.TestCase):
    def _bbc(self) -> BASICInterpreter:
        return BASICInterpreter(
            InterpreterConfig(
                dialect='bbc',
                display='none',
                display_locked=True,
                hold_display_open=False,
                optimization_level=2,
            )
        )

    def test_idempotent(self):
        i = self._bbc()
        samples = [
            'PRINTTAB(0);"x"',
            'FORI%=1TO10STEP2',
            'A=TAN10+ABS-3',
            'D%=INKEY1',
            'DEFPROC4',
            'MODE5',
            'PRINT "Original"',
            "REM TAN10 stays comment",
            "A$ = \"TAN10\"",
        ]
        for s in samples:
            once = i.canonicalize_program_line(s)
            twice = i.canonicalize_program_line(once)
            self.assertEqual(once, twice, msg=repr(s))

    def test_set_program_line_stores_printtab_split(self):
        i = self._bbc()
        i.set_program_line(10, 'PRINTTAB(5);"hi"')
        self.assertIn('PRINT TAB', i.program[10].upper())
        self.assertNotIn('PRINTTAB', i.program[10].upper().replace('PRINT TAB', ''))

    def test_set_program_line_monadic_glue(self):
        i = self._bbc()
        i.set_program_line(10, 'X=TAN10')
        self.assertIn('TAN(10)', i.program[10])
        i.set_program_line(20, 'Y=ABS-3')
        self.assertIn('ABS(-3)', i.program[20])

    def test_rem_not_unglued(self):
        i = self._bbc()
        i.set_program_line(10, 'REM TAN10 is note')
        self.assertIn('TAN10', i.program[10])
        self.assertNotIn('TAN(10)', i.program[10])

    def test_string_literal_not_unglued(self):
        i = self._bbc()
        i.set_program_line(10, 'A$="TAN10"')
        self.assertIn('"TAN10"', i.program[10])

    def test_load_path_uses_set_program_line(self):
        """LOAD goes through set_program_line → canonicalize."""
        import tempfile

        i = self._bbc()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 't.bas')
            with open(path, 'w', encoding='utf-8') as f:
                f.write('10 PRINTTAB(0);"z"\n20 END\n')
            i.working_dir = tmp
            self.assertTrue(i.load('t.bas', announce=False))
            self.assertIn('PRINT TAB', i.program[10].upper())

    def test_phase2_monadic_fast_reject(self):
        """Already-parenthesized monadic forms skip full unglue work."""
        i = self._bbc()
        self.assertFalse(i._expr_may_need_monadic_unglue('TAN(10)+ABS(-3)'))
        self.assertFalse(i._expr_may_need_monadic_unglue('I% < MAXITER%'))
        self.assertTrue(i._expr_may_need_monadic_unglue('TAN10'))
        self.assertTrue(i._expr_may_need_monadic_unglue('NOT0'))
        # Direct eval still works (safety net when glue remains).
        import math
        self.assertAlmostEqual(float(i._eval_numeric('TAN10')), math.tan(10.0), places=5)


if __name__ == '__main__':
    unittest.main()
