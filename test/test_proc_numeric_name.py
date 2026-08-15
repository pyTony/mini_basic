"""Numeric PROC/FN names (BBCSDL world.bbc PROC4) use PROC_FN_NAME_PATTERN."""
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
from mini_basic.expr.patterns import RE_PROC_CALL, RE_PROC_CALL_REST

pytestmark = [pytest.mark.phase0]


class ProcNumericNameTests(unittest.TestCase):
    def test_patterns_match_proc4(self):
        m = RE_PROC_CALL.match('PROC4(1,2)')
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), '4')
        self.assertEqual(m.group(2), '1,2')
        m2 = RE_PROC_CALL_REST.match('4(1,2)')
        self.assertIsNotNone(m2)
        self.assertEqual(m2.group(1), '4')

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

    def test_proc4_runs(self):
        i = self._bbc()
        lines = [
            (10, 'N%=0'),
            (20, 'PROC4(3)'),
            (30, 'PRINT N%'),
            (40, 'END'),
            (100, 'DEF PROC4(X%)'),
            (110, 'N%=X%*2'),
            (120, 'ENDPROC'),
        ]
        for ln, st in lines:
            i.set_program_line(ln, st)
        buf = io.StringIO()
        with redirect_stdout(buf):
            i.run()
        self.assertEqual(buf.getvalue().strip(), '6')

    def test_list_glues_numeric_proc_name(self):
        i = self._bbc()
        i.set_program_line(970, 'DEF PROC 4(F%, A%)')
        listed = i.format_list_line(i.program[970])
        self.assertIn('PROC4', listed.replace(' ', ''))
        self.assertNotIn('PROC 4', listed)

    def test_fn_f4_float_bits(self):
        i = self._bbc()
        for ln, st in [
            (10, 'PRINT FN_f4(1.0)'),
            (20, 'END'),
        ]:
            i.set_program_line(ln, st)
        buf = io.StringIO()
        with redirect_stdout(buf):
            i.run()
        self.assertEqual(buf.getvalue().strip(), '1065353216')

    def test_fn_atan2_on_error_local_return(self):
        """world.bbc: DEF FNatan2(y,x) : ON ERROR LOCAL = SGN(y)*PI/2"""
        i = self._bbc()
        for ln, st in [
            (10, 'PRINT FNatan2(1, 0)'),
            (20, 'END'),
            (100, 'DEF FNatan2(Y, X) : ON ERROR LOCAL = SGN(Y)*PI/2'),
            (110, 'IF X>0 THEN = ATN(Y/X) ELSE IF Y>0 THEN = ATN(Y/X)+PI ELSE = ATN(Y/X)-PI'),
        ]:
            i.set_program_line(ln, st)
        buf = io.StringIO()
        with redirect_stdout(buf):
            i.run()
        out = buf.getvalue()
        self.assertNotIn('jump outside body', out)
        val = float(out.strip().split()[0])
        self.assertAlmostEqual(val, 1.57079632679, places=4)

    def test_return_params_copy_back_and_register(self):
        i = self._bbc()
        for ln, st in [
            (10, 'U=0: V=0'),
            (20, 'PROC vertex(1, 2, 3, U, V)'),
            (30, 'PRINT U; ","; V'),
            (40, 'END'),
            (100, 'DEF PROC vertex(X, Y, Z, RETURN U, RETURN V)'),
            (110, 'U=X+Y'),
            (120, 'V=Z'),
            (130, 'ENDPROC'),
        ]:
            i.set_program_line(ln, st)
        i._prepare_run()
        self.assertIn('vertex', i.user_procedures)
        self.assertEqual(i.user_procedures['vertex'].return_params, ('U', 'V'))
        buf = io.StringIO()
        with redirect_stdout(buf):
            i.run()
        self.assertEqual(buf.getvalue().strip(), '3,3')

    def test_prepare_run_keeps_proc4_after_def_fn(self):
        """DEF FN must not shift PROC line indexes during _prepare_run (world.bbc)."""
        i = self._bbc()
        for ln, st in [
            (10, 'PROC4(3)'),
            (20, 'PRINT N%'),
            (30, 'END'),
            (100, 'DEF FNatan2(Y,X)=Y+X'),
            (200, 'DEF PROC4(A%)'),
            (210, 'N%=A%'),
            (220, 'ENDPROC'),
        ]:
            i.set_program_line(ln, st)
        i._prepare_run()
        self.assertIn('4', i.user_procedures)
        self.assertEqual(i._find_matching_endproc(200, sorted(i.program)), 220)

    def test_proc4_not_swallowed_by_prior_if_then(self):
        """Structured IF inside an earlier PROC must not hide later DEF PROC4."""
        i = self._bbc()
        for ln, st in [
            (10, 'N%=0'),
            (20, 'PROC4(7)'),
            (30, 'PRINT N%'),
            (40, 'END'),
            (100, 'DEF PROCouter'),
            (110, 'IF X THEN'),
            (120, 'Y=1'),
            (130, 'ENDIF'),
            (140, 'ENDPROC'),
            (200, 'DEF PROC4(A%)'),
            (210, 'N%=A%'),
            (220, 'ENDPROC'),
        ]:
            i.set_program_line(ln, st)
        i._prepare_run()
        self.assertIn('4', i.user_procedures)
        buf = io.StringIO()
        with redirect_stdout(buf):
            i.run()
        self.assertEqual(buf.getvalue().strip(), '7')

    def test_spaced_def_proc4_runs(self):
        i = self._bbc()
        for ln, st in [
            (10, 'N%=0'),
            (20, 'PROC 4(3)'),
            (30, 'PRINT N%'),
            (40, 'END'),
            (100, 'DEF PROC 4(X%)'),
            (110, 'N%=X%*2'),
            (120, 'ENDPROC'),
        ]:
            i.set_program_line(ln, st)
        buf = io.StringIO()
        with redirect_stdout(buf):
            i.run()
        self.assertEqual(buf.getvalue().strip(), '6')

    def test_defproc4_glued_header(self):
        i = self._bbc()
        lines = [
            (10, 'PROC4'),
            (20, 'PRINT "ok"'),
            (30, 'END'),
            (100, 'DEFPROC4'),
            (110, 'ENDPROC'),
        ]
        for ln, st in lines:
            i.set_program_line(ln, st)
        buf = io.StringIO()
        with redirect_stdout(buf):
            i.run()
        self.assertEqual(buf.getvalue().strip(), 'ok')


if __name__ == '__main__':
    unittest.main()
