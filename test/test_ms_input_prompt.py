"""mits / commodore INPUT: a semicolon after the prompt string prints '? '.

MS BASIC: ``INPUT "COMMAND";A$`` shows ``COMMAND? ``; a comma after the
prompt suppresses the question mark; with no prompt it is just ``? ``.
(BBC BASIC is the reverse and stays unchanged: ';' prints the prompt only.)
"""
from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx, pytest.mark.timeout(15)]


def _prompt_text(dialect: str, input_stmt: str, typed: str = 'X\n') -> str:
    interp = BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )
    interp.set_program_line(10, input_stmt)
    out, err = io.StringIO(), io.StringIO()
    with mock.patch('sys.stdin', io.StringIO(typed)):
        with redirect_stdout(out), redirect_stderr(err):
            interp.run()
    return out.getvalue()


class MsInputPromptTests(unittest.TestCase):

    def test_semicolon_adds_question_mark_in_ms_dialects(self):
        for dialect in ('mits', 'commodore'):
            self.assertEqual(
                _prompt_text(dialect, 'INPUT "COMMAND";A$').replace('\n', '').strip(),
                'COMMAND?', msg=dialect)
            self.assertTrue(
                _prompt_text(dialect, 'INPUT "COURSE (0-9)";C1', '3\n').startswith('COURSE (0-9)? '),
                msg=dialect)

    def test_comma_suppresses_question_mark(self):
        for dialect in ('mits', 'commodore'):
            out = _prompt_text(dialect, 'INPUT "NAME ",A$')
            self.assertTrue(out.startswith('NAME '), msg=(dialect, out))
            self.assertNotIn('?', out, msg=dialect)

    def test_no_prompt_still_question_mark(self):
        for dialect in ('mits', 'commodore'):
            self.assertTrue(_prompt_text(dialect, 'INPUT A$').startswith('? '), msg=dialect)

    def test_prompt_expression_and_multiple_variables(self):
        for dialect in ('mits', 'commodore'):
            out = _prompt_text(dialect, 'INPUT "X,Y";A,B', '1,2\n')
            self.assertTrue(out.startswith('X,Y? '), msg=(dialect, out))

    def test_mini_and_bbc_keep_prompt_only(self):
        for dialect in ('mini', 'bbc'):
            out = _prompt_text(dialect, 'INPUT "COMMAND";A$')
            self.assertEqual(out.replace('\n', '').strip(), 'COMMAND', msg=dialect)


if __name__ == '__main__':
    unittest.main()
