"""Regression tests for depth-aware parsing and statement splitting."""
from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0]


class ParsingHarness(unittest.TestCase):
    def make_interp(self, *, dialect: str = 'bbc') -> BASICInterpreter:
        return BASICInterpreter(InterpreterConfig(dialect=dialect, display='none'))

    def run_program(
        self,
        lines,
        *,
        inputs=None,
        dialect: str = 'bbc',
    ) -> str:
        interp = self.make_interp(dialect=dialect)
        for line_num, statement in lines:
            interp.program[line_num] = statement
        input_values = list(inputs) if inputs is not None else []
        with patch('builtins.input', side_effect=input_values):
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.run()
        return buf.getvalue().rstrip('\n')

    def assert_no_error(self, output: str) -> None:
        self.assertNotIn('? ', output)


class ParsingSplitUnitTests(ParsingHarness):
    def setUp(self) -> None:
        self.interp = self.make_interp()

    def test_split_at_depth_commas_in_strings(self) -> None:
        self.assertEqual(
            self.interp._split_at_depth('"Hello, world", 42', ','),
            ['"Hello, world"', '42'],
        )

    def test_split_at_depth_nested_parens(self) -> None:
        self.assertEqual(
            self.interp._split_at_depth('FNSUM(1+2, 3+4), 5', ','),
            ['FNSUM(1+2, 3+4)', '5'],
        )

    def test_split_at_depth_semicolons(self) -> None:
        self.assertEqual(
            self.interp._split_at_depth('A; B; C', ';', skip_empty=True),
            ['A', 'B', 'C'],
        )

    def test_split_at_depth_plus_concat(self) -> None:
        self.assertEqual(
            self.interp._split_at_depth('"A+B" + "C"', '+', skip_empty=True),
            ['"A+B"', '"C"'],
        )

    def test_split_first_at_depth_colon_in_string(self) -> None:
        self.assertEqual(
            self.interp._split_first_at_depth('WHEN "x:y": PRINT', ':'),
            ('WHEN "x:y"', 'PRINT'),
        )

    def test_split_colon_rem_keeps_trailing_statement_on_same_segment(self) -> None:
        self.assertEqual(
            self.interp._split_colon_statements(
                'PRINT "Hi" : REM comment : PRINT "There"',
            ),
            ['PRINT "Hi"', 'REM comment : PRINT "There"'],
        )

    def test_split_colon_whole_rem_line_returns_stripped(self) -> None:
        self.assertEqual(
            self.interp._split_colon_statements('REM dialect: bbc'),
            ['REM dialect: bbc'],
        )
        self.assertEqual(
            self.interp._split_colon_statements('REM This: is a REM'),
            ['REM This: is a REM'],
        )

    def test_split_colon_strings_with_colons(self) -> None:
        self.assertEqual(
            self.interp._split_colon_statements('PRINT "A:B:C" : PRINT "ok"'),
            ['PRINT "A:B:C"', 'PRINT "ok"'],
        )

    def test_split_input_vars_commas_in_prompt_segment(self) -> None:
        self.assertEqual(
            self.interp._split_input_vars('"Enter name, age: "; N$, A%'),
            ['"Enter name, age: "; N$', 'A%'],
        )

    def test_split_input_line_values_commas_in_quoted_field(self) -> None:
        self.assertEqual(
            self.interp._split_input_line_values('"Hello, world", 42'),
            ['"Hello, world"', '42'],
        )


class ParsingProgramTests(ParsingHarness):
    def test_print_commas_inside_strings(self) -> None:
        out = self.run_program([
            (10, 'PRINT "Hello, world", 42'),
            (20, 'PRINT "One, two, three"'),
            (30, 'END'),
        ])
        lines = out.splitlines()
        self.assertEqual(lines[0], 'Hello, world        42')
        self.assertEqual(lines[1], 'One, two, three')

    def test_fn_sum_commas_in_arguments(self) -> None:
        out = self.run_program([
            (10, 'DEF FNSUM(A,B)=A+B'),
            (20, 'PRINT FNSUM(1+2, 3+4)'),
            (30, 'PRINT FNSUM(FNSUM(1,2), 5)'),
            (40, 'END'),
        ])
        self.assertEqual(out.splitlines(), ['10', '8'])

    def test_print_colons_inside_strings(self) -> None:
        out = self.run_program([
            (10, 'PRINT "Time: " + TIME$'),
            (20, 'PRINT "A:B:C"'),
            (30, 'END'),
        ])
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith('Time: '))
        self.assertEqual(lines[1], 'A:B:C')

    def test_if_then_inline_colon_assignments(self) -> None:
        out = self.run_program([
            (10, 'LET X=1'),
            (20, 'IF X=1 THEN A=2 : B=3'),
            (30, 'PRINT A, B'),
            (40, 'END'),
        ])
        self.assertEqual(out.strip(), '2         3')

    def test_bbc_adjacent_string_juxtaposition(self) -> None:
        out = self.run_program([
            (10, 'PRINT "Hello" "World"'),
            (20, 'PRINT "Hello"\'"World"'),
            (30, 'PRINT "Hello"STR$(1)'),
            (40, 'END'),
        ])
        # BBC PRINT ': apostrophe is a newline separator (not string glue).
        self.assertEqual(out.splitlines(), ['HelloWorld', 'Hello', 'World', 'Hello1'])

    def test_nested_parentheses_expressions(self) -> None:
        out = self.run_program([
            (10, 'PRINT (1+2)*(3+4)'),
            (20, 'LET A=1'),
            (30, 'LET B=2'),
            (40, 'IF A=1 AND B=2 THEN PRINT "OK"'),
            (50, 'END'),
        ])
        self.assertEqual(out.splitlines(), ['21', 'OK'])

    def test_string_concat_plus_inside_literal(self) -> None:
        out = self.run_program([
            (10, 'A$ = "Hello" + "World"'),
            (20, 'B$ = "A+B" + "C"'),
            (30, 'PRINT A$, B$'),
            (40, 'END'),
        ])
        self.assertEqual(out, 'HelloWorldA+BC')

    def test_rem_line_with_colon_is_ignored(self) -> None:
        out = self.run_program([
            (10, 'REM This: is a REM'),
            (20, 'PRINT "After REM"'),
            (30, 'END'),
        ])
        self.assertEqual(out, 'After REM')

    def test_input_prompt_with_comma_and_multi_values(self) -> None:
        out = self.run_program([
            (10, 'INPUT "Enter name, age: "; N$, A%'),
            (20, 'PRINT N$; ","; STR$(A%)'),
            (30, 'END'),
        ], inputs=['John, 30'])
        self.assertEqual(out, 'Enter name, age: John,30')

    def test_data_strings_with_embedded_commas(self) -> None:
        out = self.run_program([
            (10, 'DATA "Hello, world", 42, "A,B,C"'),
            (20, 'READ A$, X, B$'),
            (30, 'PRINT A$, X, B$'),
            (40, 'END'),
        ])
        self.assertEqual(out, 'Hello, world        42        A,B,C')

    def test_on_goto_multiple_targets(self) -> None:
        out = self.run_program([
            (10, 'LET X=2'),
            (20, 'ON X GOTO 100, 200, 300'),
            (30, 'PRINT "skip"'),
            (100, 'PRINT "one"'),
            (110, 'END'),
            (200, 'PRINT "two"'),
            (210, 'END'),
            (300, 'PRINT "three"'),
        ])
        self.assertEqual(out, 'two')

    def test_print_using_comma_in_format(self) -> None:
        out = self.run_program([
            (10, 'A=1234.56'),
            (20, 'PRINT USING "###,###.##"; A'),
            (30, 'END'),
        ])
        self.assertEqual(out, '  1,234.56')

    def test_whole_array_fill_commas_with_parens(self) -> None:
        out = self.run_program([
            (10, 'DIM A(1,1)'),
            (20, 'A()=(1+1),(2+2),(3+3),(4+4)'),
            (30, 'PRINT A(0,0), A(1,1)'),
            (40, 'END'),
        ])
        self.assertEqual(out.strip(), '2         8')

    def test_if_then_multiple_inline_assignments(self) -> None:
        out = self.run_program([
            (10, 'LET X=1'),
            (20, 'IF X=1 THEN A=2 : B=3 : C=4'),
            (30, 'PRINT A, B, C'),
            (40, 'END'),
        ])
        self.assertEqual(out.strip(), '2         3         4')

    def test_nested_string_function_calls(self) -> None:
        out = self.run_program([
            (10, 'PRINT LEFT$(RIGHT$("ABCDE",3),1)'),
            (20, 'END'),
        ])
        self.assertEqual(out, 'C')

    def test_write_hash_file_with_commas_in_string(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                out = self.run_program([
                    (10, 'LET CH = OPENOUT("data.txt")'),
                    (20, 'WRITE#CH, "Hello, world", 123'),
                    (30, 'CLOSE#CH'),
                    (40, 'END'),
                ])
                self.assert_no_error(out)
                with open('data.txt', encoding='utf-8') as handle:
                    body = handle.read()
                self.assertIn('Hello, world', body)
                self.assertIn('123', body)
            finally:
                os.chdir(cwd)

    def test_vdu_multiple_codes_no_crash(self) -> None:
        out = self.run_program([
            (10, 'VDU 19,0,4,0,0,0'),
            (20, 'PRINT "ok"'),
            (30, 'END'),
        ])
        self.assert_no_error(out)
        self.assertEqual(out, 'ok')

    def test_rem_on_colon_segment_comments_rest_of_that_segment(self) -> None:
        """BBC: REM ends the current colon-separated statement, not later ones."""
        out = self.run_program([
            (10, 'PRINT "Hi" : REM comment : PRINT "There"'),
            (20, 'END'),
        ])
        self.assertEqual(out, 'Hi')

    def test_print_before_and_after_rem_on_separate_colon_segments(self) -> None:
        out = self.run_program([
            (10, 'PRINT "Hi" : REM comment'),
            (20, 'PRINT "There"'),
            (30, 'END'),
        ])
        self.assertEqual(out.splitlines(), ['Hi', 'There'])


if __name__ == '__main__':
    unittest.main()