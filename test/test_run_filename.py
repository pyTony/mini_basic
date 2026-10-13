"""RUN "file.bas" / RUN <linenum>: GW-BASIC/MSX/Amstrad-style RUN extensions.

mini_basic's REPL tab-completion already advertised ``RUN path.bas`` as
valid syntax, but the RUN statement handler never implemented it: it either
silently discarded the filename and restarted the current program, or (after
a later fix for dropped trailing text) rejected it outright with "RUN takes
no argument". This makes RUN "file" actually load the file and run it, and
RUN <linenum> jump straight to that line — both doing a full reset first
(variables, arrays, FOR/GOSUB stacks), same semantics as CHAIN without its
optional variable-preserving ALL flag.

This is also the key difference from GOTO <linenum>, which jumps to the
same place but preserves all program state (variables, FOR/GOSUB stacks).

RUN with other trailing text that isn't a valid filename or line-number
expression (e.g. a bare undeclared identifier) keeps erroring instead of
silently restarting.
"""
from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig, _execute_repl_line

pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]


class RunFilenameTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.path = os.path.join(self._tmpdir.name, 'target.bas')
        with open(self.path, 'w') as f:
            f.write('10 PRINT "TARGET RAN"\n20 END\n')

    def test_run_linenum_jumps_with_fresh_state(self) -> None:
        """RUN 20 starts fresh (vars cleared) at line 20, skipping earlier lines."""
        interp = BASICInterpreter(InterpreterConfig(display='none'))
        interp.program[10] = 'PRINT "hei"'
        interp.program[20] = 'PRINT "moi"'
        out = io.StringIO()
        with redirect_stdout(out):
            _execute_repl_line(interp, 'RUN 20')
        self.assertEqual(out.getvalue(), 'moi\n')

    def test_run_linenum_not_found_errors(self) -> None:
        interp = BASICInterpreter(InterpreterConfig(display='none'))
        interp.program[10] = 'PRINT "hei"'
        out = io.StringIO()
        with redirect_stdout(out):
            _execute_repl_line(interp, 'RUN 99')
        self.assertIn('Line not found', out.getvalue())

    def test_run_linenum_clears_variables_goto_does_not(self) -> None:
        """The core GOTO vs RUN distinction: RUN wipes vars, GOTO keeps them."""
        for keyword, expect_cleared in (('GOTO', False), ('RUN', True)):
            interp = BASICInterpreter(InterpreterConfig(display='none'))
            interp.program[10] = 'X = 42'
            interp.program[20] = 'PRINT X'
            interp.run()  # sets X = 42, prints it
            out = io.StringIO()
            with redirect_stdout(out):
                _execute_repl_line(interp, f'{keyword} 20')
            printed = out.getvalue().strip()
            if expect_cleared:
                self.assertEqual(printed, '0', msg=f'{keyword}: {printed!r}')
            else:
                self.assertEqual(printed, '42', msg=f'{keyword}: {printed!r}')

    def test_run_linenum_clears_gosub_and_for_stacks(self) -> None:
        """RUN from inside a GOSUB/FOR must drop the stacks, unlike GOTO."""
        interp = BASICInterpreter(InterpreterConfig(display='none'))
        interp.program[10] = 'GOSUB 100'
        interp.program[20] = 'END'
        interp.program[100] = 'RUN 20'
        out = io.StringIO()
        with redirect_stdout(out):
            interp.run()
        # If the GOSUB stack survived, a stray RETURN-like unwind or a stack
        # error would show up; a clean, silent END means the stack was wiped.
        self.assertEqual(out.getvalue(), '')
        self.assertEqual(len(interp.gosub_stack), 0)

    def test_run_filename_loads_and_runs(self) -> None:
        interp = BASICInterpreter(InterpreterConfig(display='none'))
        interp.program[10] = f'RUN "{self.path}"'
        out = io.StringIO()
        with redirect_stdout(out):
            interp.run()
        self.assertIn('TARGET RAN', out.getvalue())

    def test_run_filename_from_immediate_mode(self) -> None:
        """RUN "file" typed directly at the REPL prompt (not a program line)."""
        interp = BASICInterpreter(InterpreterConfig(display='none'))
        out = io.StringIO()
        with redirect_stdout(out):
            _execute_repl_line(interp, f'RUN "{self.path}"')
        self.assertIn('TARGET RAN', out.getvalue())

    def test_run_filename_from_program_line_transfers(self) -> None:
        interp = BASICInterpreter(InterpreterConfig(display='none'))
        interp.program[10] = 'PRINT "BEFORE"'
        interp.program[20] = f'RUN "{self.path}"'
        interp.program[30] = 'PRINT "UNREACHABLE"'
        out = io.StringIO()
        with redirect_stdout(out):
            interp.run()
        text = out.getvalue()
        self.assertIn('BEFORE', text)
        self.assertIn('TARGET RAN', text)
        self.assertNotIn('UNREACHABLE', text)

    def test_run_filename_not_found_errors(self) -> None:
        interp = BASICInterpreter(InterpreterConfig(display='none'))
        interp.program[10] = 'RUN "/no/such/file_xyz.bas"'
        out = io.StringIO()
        with redirect_stdout(out):
            interp.run()
        self.assertIn('RUN error', out.getvalue())
        self.assertIn('file not found', out.getvalue())

    def test_run_with_bad_identifier_still_errors(self) -> None:
        """RUN GARBAGE (not a string, not a line number) must still error."""
        interp = BASICInterpreter(InterpreterConfig(display='none'))
        interp.program[10] = 'RUN GARBAGE'
        interp.program[20] = 'PRINT "HELLO"'
        out = io.StringIO()
        with redirect_stdout(out):
            interp.run()
        text = out.getvalue()
        self.assertIn('RUN takes no argument', text)
        self.assertEqual(text.count('HELLO'), 1, msg=text)

    def test_bare_run_still_works_without_error(self) -> None:
        """Ensure the new filename/linenum branches didn't break plain RUN."""
        interp = BASICInterpreter(InterpreterConfig(display='none'))
        interp.program[10] = 'PRINT "RAN"'
        interp.program[20] = 'END'
        out = io.StringIO()
        with redirect_stdout(out):
            interp.run()
        text = out.getvalue()
        self.assertNotIn('RUN takes no argument', text)
        self.assertEqual(text.strip(), 'RAN')


if __name__ == '__main__':
    unittest.main()
