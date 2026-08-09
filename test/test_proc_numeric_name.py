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
