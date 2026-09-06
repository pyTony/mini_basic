"""TIMING ON/OFF reports wall time for RUN on stderr, not PRINT."""
from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


def _interp():
    return BASICInterpreter(
        InterpreterConfig(dialect='mini', display='none', display_locked=True)
    )


class TimingOnOffTests(unittest.TestCase):
    def test_timing_on_prints_time_on_stderr_after_run(self):
        interp = _interp()
        interp.set_program_line(10, 'PRINT 1')
        interp.set_program_line(20, 'END')
        interp.execute_immediate('TIMING ON')
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            interp.run()
        self.assertIn('1', out.getvalue())
        self.assertNotIn('Time:', out.getvalue())
        self.assertRegex(err.getvalue(), r'Time:\s+\d+\.\d{3} s')

    def test_timing_off_is_silent(self):
        interp = _interp()
        interp.set_program_line(10, 'PRINT 1')
        interp.set_program_line(20, 'END')
        interp.execute_immediate('TIMING ON')
        interp.execute_immediate('TIMING OFF')
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            interp.run()
        self.assertIn('1', out.getvalue())
        self.assertNotIn('Time:', out.getvalue())
        self.assertNotIn('Time:', err.getvalue())

    def test_timing_survives_new_and_does_not_use_program_timer_vars(self):
        interp = _interp()
        interp.execute_immediate('TIMING ON')
        interp.new(announce=False)
        interp.set_program_line(10, 'PRINT 2')
        interp.set_program_line(20, 'END')
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            interp.run()
        self.assertIn('2', out.getvalue())
        self.assertRegex(err.getvalue(), r'Time:\s+\d+\.\d{3} s')
        self.assertNotIn('T1', out.getvalue())


if __name__ == '__main__':
    unittest.main()
