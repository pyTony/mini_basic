"""BBC BASIC V: INPUT with a prompt but no variable just prints the prompt.

Real Acorn BBC BASIC V treats ``INPUT "text"`` (no variable to assign) as a
no-op read: it prints the string and continues immediately, with no wait
for input. mini_basic previously raised ``? INPUT error`` for this form.

This is BBC-specific: general BASIC practice (MS/MITS-style dialects) is to
syntax-error on INPUT with no variable, so mini_basic keeps erroring there,
just with a clearer "missing variable" message.
"""
from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]


class InputPromptOnlyTests(unittest.TestCase):
    def test_prompt_only_input_just_prints(self) -> None:
        """INPUT "PAUSE" : PRINT "STARTED" -> PAUSESTARTED, no read, no error."""
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.program[10] = 'INPUT "PAUSE" : PRINT "STARTED"'
        out = io.StringIO()
        with redirect_stdout(out), patch('builtins.input', side_effect=AssertionError(
            'builtins.input must not be called for a prompt-only INPUT'
        )):
            interp.run()
        self.assertEqual(out.getvalue().strip(), 'PAUSESTARTED')

    def test_prompt_only_input_with_concat_expression(self) -> None:
        """A non-lvalue expression operand (not just a bare literal) also prints only."""
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.program[10] = 'INPUT "hi" + "!"'
        interp.program[20] = 'PRINT "!"'
        out = io.StringIO()
        with redirect_stdout(out), patch('builtins.input', side_effect=AssertionError(
            'builtins.input must not be called when the operand is not an lvalue'
        )):
            interp.run()
        self.assertEqual(out.getvalue().strip(), 'hi!!')

    def test_bare_input_with_nothing_still_errors(self) -> None:
        """INPUT with no prompt and no variable at all remains a syntax error."""
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.program[10] = 'INPUT'
        out = io.StringIO()
        with redirect_stdout(out):
            interp.run()
        self.assertIn('INPUT error', out.getvalue())

    def test_prompt_only_input_errors_outside_bbc_dialect(self) -> None:
        """Only the bbc dialect gets the print-only relaxation; others still error."""
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none'))
        interp.program[10] = 'INPUT "PAUSE" : PRINT ",STARTED"'
        out = io.StringIO()
        with redirect_stdout(out), patch('builtins.input', side_effect=AssertionError(
            'builtins.input must not be called on a syntax error'
        )):
            interp.run()
        self.assertIn('INPUT error', out.getvalue())
        self.assertIn('missing variable', out.getvalue())

    def test_normal_input_with_variable_still_reads(self) -> None:
        """Ensure the prompt-only relaxation doesn't break INPUT "prompt", var."""
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.program[10] = 'INPUT "Name? ", N$'
        interp.program[20] = 'PRINT "["; N$; "]"'
        out = io.StringIO()
        with redirect_stdout(out), patch('builtins.input', side_effect=['Alice']):
            interp.run()
        self.assertEqual(out.getvalue().strip(), 'Name? [Alice]')

    def test_empty_prompt_after_print_comma_starts_next_line(self) -> None:
        """BBCSDL: a trailing PRINT comma ends the line; only ; suppresses it."""
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.program[10] = 'PRINT "Name:",: INPUT "", NAME$'
        interp.program[20] = 'PRINT "Hi "; NAME$'
        out = io.StringIO()
        with redirect_stdout(out), patch('builtins.input', return_value='Tony') as mocked:
            interp.run()
        self.assertEqual(mocked.call_args.args[0], '? ')
        self.assertEqual(out.getvalue(), 'Name:\nHi Tony\n')

    def test_empty_semicolon_prompt_after_trailing_semicolon_stays_on_same_line(self) -> None:
        """Same bug via the semicolon form: PRINT "hi, ";: INPUT ""; X$."""
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.program[10] = 'PRINT "hi, ";: INPUT ""; NAME$: PRINT "HERE"'
        out = io.StringIO()
        with redirect_stdout(out), patch('builtins.input', return_value='Tony'):
            interp.run()
        self.assertEqual(out.getvalue(), 'hi, HERE\n')

    def test_prompt_with_real_text_continues_current_line(self) -> None:
        """BBC INPUT prints its prompt at the current cursor position."""
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.program[10] = 'PRINT "x";: INPUT "Name? ", N$'
        out = io.StringIO()
        with redirect_stdout(out), patch('builtins.input', return_value='Alice'):
            interp.run()
        self.assertEqual(out.getvalue(), 'xName? ')


if __name__ == '__main__':
    unittest.main()
