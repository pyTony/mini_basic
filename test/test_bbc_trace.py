"""BBC TRACE ON/OFF/n/PROC/STEP/TO and LVAR."""
from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from mini_basic import BASICInterpreter, InterpreterConfig

import pytest

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


def _interp() -> BASICInterpreter:
    return BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', display_locked=True)
    )


class BbcTraceTests(unittest.TestCase):
    def _run(self, interp: BASICInterpreter) -> tuple[str, str]:
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            interp.run()
        return out.getvalue(), err.getvalue()

    def test_trace_n_skips_lines_at_or_above_limit(self) -> None:
        interp = _interp()
        interp.set_program_line(10, 'TRACE 20')
        interp.set_program_line(15, 'PRINT "a"')
        interp.set_program_line(20, 'PRINT "b"')
        interp.set_program_line(30, 'END')
        out, err = self._run(interp)
        self.assertIn('a', out)
        self.assertIn('b', out)
        self.assertIn('[15]', err)
        self.assertNotIn('[20]', err)
        self.assertNotIn('[30]', err)
        self.assertNotIn('[15]', out)

    def test_trace_proc_emits_proc_and_fn_names(self) -> None:
        interp = _interp()
        interp.set_program_line(10, 'TRACE PROC')
        interp.set_program_line(20, 'DEF FNinc(x)=x+1')
        interp.set_program_line(30, 'DEF PROCping')
        interp.set_program_line(40, 'ENDPROC')
        interp.set_program_line(50, 'PRINT FNinc(1)')
        interp.set_program_line(60, 'PROCping')
        interp.set_program_line(70, 'END')
        out, err = self._run(interp)
        self.assertIn('2', out)
        self.assertIn('FNinc', err)
        self.assertIn('PROCping', err)
        self.assertNotIn('[50]', err)

    def test_trace_to_file_not_stderr(self) -> None:
        interp = _interp()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'path.log')
            interp.set_program_line(10, f'TRACE TO "{path}"')
            interp.set_program_line(20, 'PRINT "ok"')
            interp.set_program_line(30, 'END')
            out, err = self._run(interp)
            self.assertIn('ok', out)
            self.assertNotIn('[20]', out)
            self.assertNotIn('[20]', err)
            with open(path, encoding='utf-8') as handle:
                logged = handle.read()
            self.assertIn('[20]', logged)
            self.assertIn('[30]', logged)
            interp.execute_immediate('TRACE CLOSE')

    def test_trace_step_does_not_block_when_stdin_is_not_a_tty(self) -> None:
        interp = _interp()
        interp.set_program_line(10, 'TRACE STEP')
        interp.set_program_line(20, 'PRINT "go"')
        interp.set_program_line(30, 'END')
        out, err = self._run(interp)
        self.assertIn('go', out)
        self.assertIn('[20]', err)

    def test_trace_step_escape_stops_via_hook(self) -> None:
        interp = _interp()
        interp._trace_step_hook = lambda: 'stop'
        interp.set_program_line(10, 'TRACE STEP')
        interp.set_program_line(20, 'PRINT "first"')
        interp.set_program_line(30, 'PRINT "second"')
        interp.set_program_line(40, 'END')
        out, err = self._run(interp)
        self.assertIn('Break in 20', out)
        self.assertNotIn('second', out)
        self.assertTrue(interp.stopped)

    def test_lvar_lists_scalars_arrays_and_defs(self) -> None:
        interp = _interp()
        interp.set_program_line(10, 'A% = 3')
        interp.set_program_line(20, 'N$ = "hi"')
        interp.set_program_line(30, 'DIM W(4)')
        interp.set_program_line(40, 'DEF FNid(x)=x')
        interp.set_program_line(50, 'DEF PROCnoop')
        interp.set_program_line(60, 'ENDPROC')
        interp.set_program_line(70, 'LVAR')
        interp.set_program_line(80, 'END')
        out, err = self._run(interp)
        self.assertIn('A% = 3', out)
        self.assertIn('N$ = "hi"', out)
        self.assertIn('W(4)', out)
        self.assertIn('FNid', out)
        self.assertIn('PROCnoop', out)
        self.assertNotIn('A% = 3', err)

    def test_stop_inside_proc_returns_to_immediate_mode(self) -> None:
        interp = _interp()
        interp.set_program_line(10, 'X = 1')
        interp.set_program_line(20, 'DEF PROCbrk')
        interp.set_program_line(30, 'STOP')
        interp.set_program_line(40, 'ENDPROC')
        interp.set_program_line(50, 'PROCbrk')
        interp.set_program_line(60, 'X = 2')
        interp.set_program_line(70, 'END')
        out, _err = self._run(interp)
        self.assertIn('Break in 30', out)
        self.assertTrue(interp.stopped)
        self.assertEqual(interp.variables.get('X'), 1.0)

    def test_lvar_immediate_after_stop(self) -> None:
        interp = _interp()
        interp.set_program_line(10, 'X = 9')
        interp.set_program_line(20, 'STOP')
        interp.set_program_line(30, 'END')
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            interp.run()
        self.assertTrue(interp.stopped)
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            interp.execute_immediate('LVAR')
        self.assertIn('X = 9', out.getvalue())
        self.assertTrue(interp.can_execute_immediate('PRINT X'))


if __name__ == '__main__':
    unittest.main()
