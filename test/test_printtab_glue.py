"""PRINTTAB is BBC dialect; mini should hint --dialect bbc (not invent mini glue)."""
from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0]


class PrintTabGlueTests(unittest.TestCase):
    def test_printtab_runs_under_bbc(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True),
        )
        cmd, rest = interp._parse_command('PRINTTAB(0,22);')
        self.assertEqual(cmd, 'PRINT')
        self.assertTrue(rest.upper().lstrip().startswith('TAB'))
        buf = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(err):
            interp.set_program_line(10, 'PRINTTAB(0,0);"ok"')
            interp.set_program_line(20, 'END')
            interp.run()
        out = buf.getvalue() + err.getvalue()
        self.assertNotIn('Unknown', out)
        self.assertIn('ok', out)

    def test_printtab_in_mini_suggests_bbc_dialect(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='mini', display='none', display_locked=True),
        )
        msg = interp._unknown_statement_message('PRINTTAB(0,22);')
        self.assertIn('Unknown statement', msg)
        self.assertIn('--dialect bbc', msg)

    def test_printtab_run_error_mentions_bbc(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='mini', display='none', display_locked=True),
        )
        buf = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(err):
            interp.set_program_line(10, 'PRINTTAB(0,0);"hi"')
            interp.set_program_line(20, 'END')
            interp.run()
        out = buf.getvalue() + err.getvalue()
        self.assertIn('Unknown', out)
        self.assertIn('--dialect bbc', out)


if __name__ == '__main__':
    unittest.main()
