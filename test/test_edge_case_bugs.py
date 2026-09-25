"""Edge-case BASIC programs that used to crash, hang, or give wrong results."""
from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx, pytest.mark.timeout(15)]


def _run(src: str, dialect: str = 'mini') -> tuple[str, str]:
    """Run numbered program text; return (stdout, stderr)."""
    interp = BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )
    for raw in src.strip().splitlines():
        num, _, text = raw.strip().partition(' ')
        interp.set_program_line(int(num), text)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        interp.run()
    return out.getvalue(), err.getvalue()


class ChainedComparisonTests(unittest.TestCase):
    """BASIC evaluates A > B > C as (A > B) > C, not Python's chain."""

    def test_if_chained_comparison_does_not_crash(self):
        for dialect in ('mini', 'bbc', 'mits'):
            out, err = _run(
                '10 A=3:B=2:C=1\n'
                '20 IF A > B > C THEN PRINT "PY" ELSE PRINT "BASIC"\n',
                dialect,
            )
            self.assertEqual(out.strip(), 'BASIC', msg=(dialect, err))

    def test_chained_comparison_value(self):
        for dialect in ('mini', 'bbc', 'mits'):
            out, err = _run(
                '10 X = 3 > 2 > 1\n'
                '20 PRINT X\n'
                '30 PRINT 1 = 1 = 1\n'
                '40 PRINT 1 < 2 < 3\n',
                dialect,
            )
            self.assertEqual(out.split(), ['0', '0', '-1'], msg=(dialect, err))


class GosubInsideThenTests(unittest.TestCase):
    def test_return_continues_rest_of_then_clause(self):
        for dialect in ('mini', 'bbc', 'mits'):
            out, err = _run(
                '10 X = 1\n'
                '20 IF X = 1 THEN GOSUB 100 : PRINT "BACK"\n'
                '30 END\n'
                '100 PRINT "SUB"; : RETURN\n',
                dialect,
            )
            self.assertEqual(out.strip(), 'SUBBACK', msg=(dialect, err))

    def test_gosub_in_then_after_for_does_not_loop_forever(self):
        out, err = _run(
            '10 FOR I = 1 TO 3 : IF I > 1 THEN GOSUB 100 : PRINT "B";\n'
            '20 NEXT I\n'
            '30 END\n'
            '100 PRINT I; : RETURN\n'
        )
        self.assertEqual(out.strip(), '2B3B', msg=err)

    def test_gosub_in_else_clause(self):
        out, err = _run(
            '10 X = 0\n'
            '20 IF X = 1 THEN PRINT "Y" ELSE GOSUB 100 : PRINT "BACK"\n'
            '30 END\n'
            '100 PRINT "SUB"; : RETURN\n',
            'bbc',
        )
        self.assertEqual(out.strip(), 'SUBBACK', msg=err)


class ReturnDropsForFramesTests(unittest.TestCase):
    def test_return_from_inside_for_discards_sub_loop(self):
        out, err = _run(
            '10 FOR T = 1 TO 3 : GOSUB 100 : NEXT : PRINT "OK"; T\n'
            '20 END\n'
            '100 FOR I = 1 TO 3 : IF I = 2 THEN RETURN\n'
            '110 NEXT I : RETURN\n'
        )
        self.assertNotIn('RETURN without GOSUB', err)
        self.assertEqual(out.strip(), 'OK4', msg=err)


class FnAssignIsNotReturnTests(unittest.TestCase):
    """Assigning to the function name sets the result; it does not return."""

    def test_def_fn_default_then_conditional_recursive_assign(self):
        out, err = _run(
            '10 DEF FNF(N)\n'
            '20 FNF = 1\n'
            '30 IF N > 1 THEN FNF = N * FNF(N - 1)\n'
            '40 END DEF\n'
            '50 PRINT FNF(5)\n'
        )
        self.assertEqual(out.strip(), '120', msg=err)

    def test_conditional_assign_without_exit_falls_through(self):
        out, err = _run(
            '10 DEF FNG(N)\n'
            '20 IF N = 0 THEN FNG = 100\n'
            '30 IF N > 0 THEN FNG = FNG(N - 1) + 1\n'
            '40 END DEF\n'
            '50 PRINT FNG(0)\n'
            '60 PRINT FNG(3)\n'
        )
        self.assertEqual(out.split(), ['100', '103'], msg=err)

    def test_then_assign_followed_by_more_body_is_not_return(self):
        out, err = _run(
            '10 DEF FNH(N)\n'
            '20 IF N = 0 THEN FNH = 1\n'
            '30 IF N = 0 THEN FNH = 2\n'
            '40 IF N > 0 THEN FNH = FNH(N - 1) * 10\n'
            '50 END DEF\n'
            '60 PRINT FNH(0)\n'
            '70 PRINT FNH(2)\n'
        )
        self.assertEqual(out.split(), ['2', '200'], msg=err)

    def test_exit_function_still_returns_early(self):
        out, err = _run(
            '10 PRINT FNR(3)\n'
            '20 END\n'
            '60 DEF FNR(N)\n'
            '70 IF N = 0 THEN FNR = 0 : EXIT FUNCTION\n'
            '80 FNR = N + FNR(N - 1)\n'
            '90 END DEF\n'
        )
        self.assertEqual(out.strip(), '6', msg=err)


class MiniLowercaseKeywordTests(unittest.TestCase):
    """mini is not strict about keyword case; bbc keeps uppercase-only keywords."""

    def test_lowercase_for_next_print(self):
        out, err = _run('10 for i = 1 to 3 step 1 : print i; : next i\n')
        self.assertEqual(out.strip(), '123', msg=err)

    def test_lowercase_if_then_else_goto_gosub(self):
        out, err = _run(
            '10 x = 3 : if x > 2 then print "big" else print "small"\n'
            '20 if x = 3 and not x = 4 then gosub 100\n'
            '30 goto 50\n'
            '40 print "skipped"\n'
            '50 end\n'
            '100 print len("abc"); mid$("hello", 2, 3); x mod 2 : return\n'
        )
        self.assertEqual(out.split(), ['big', '3ell1'], msg=err)

    def test_lowercase_while_and_dim(self):
        out, err = _run(
            '10 dim a(3) : n = 0\n'
            '20 while n < 3 : n = n + 1 : a(n) = n * n : wend\n'
            '30 print a(3)\n'
        )
        self.assertEqual(out.strip(), '9', msg=err)

    def test_lowercase_identifiers_stay_case_sensitive(self):
        out, err = _run('10 a = 1 : A = 2 : print a; A\n')
        self.assertEqual(out.strip(), '12', msg=err)

    def test_strings_and_rem_are_not_folded(self):
        out, err = _run(
            '10 print "for to next" : rem print this\n'
            '20 read d$ : print d$\n'
            '30 data then else\n'
        )
        self.assertEqual(out.splitlines(), ['for to next', 'then else'], msg=err)

    def test_bbc_still_rejects_lowercase_keywords(self):
        out, err = _run('10 print "hi"\n', 'bbc')
        self.assertIn('Unknown statement', out + err)


class EvalSandboxTests(unittest.TestCase):
    """Expressions are evaluated with Python eval; Python internals must stay out of reach."""

    def test_attribute_access_is_rejected(self):
        for expr in (
            '(1).__class__.__bases__',
            '(1).__class__',
            '().__class__.__name__',
        ):
            out, err = _run(f'10 X = {expr}\n20 PRINT "REACHED"\n')
            self.assertNotIn('REACHED', out, msg=expr)
            self.assertNotIn('tuple', out + err, msg=expr)
            self.assertNotIn('type', out + err, msg=expr)

    def test_comprehension_and_lambda_rejected(self):
        for expr in ('[x for x in (1,2)][1]', '(lambda: 7)()'):
            out, err = _run(f'10 PRINT {expr}\n')
            self.assertIn('?', out + err, msg=expr)
            self.assertNotEqual(out.strip(), '2', msg=expr)

    def test_data_items_cannot_reach_attributes(self):
        # Before: eval ran the attribute chain and READ got 3.
        out, err = _run('10 READ A\n20 PRINT A\n30 DATA (1).__class__.__name__.__len__()\n')
        self.assertNotEqual(out.strip(), '3', msg=err)


class NestedWhileTests(unittest.TestCase):
    def test_outer_while_line_with_trailing_statement(self):
        out, err = _run(
            '10 I = 0\n'
            '20 WHILE I < 2 : J = 0\n'
            '30 WHILE J < 2\n'
            '35 PRINT I; J;\n'
            '36 J = J + 1\n'
            '37 WEND\n'
            '40 I = I + 1 : WEND\n'
        )
        self.assertEqual(out.strip(), '00011011', msg=err)

    def test_wend_does_not_rerun_statements_before_while(self):
        out, err = _run(
            '10 I = 0 : WHILE I < 3\n'
            '20 I = I + 1 : PRINT I;\n'
            '30 WEND\n'
            '40 PRINT "END"\n'
        )
        self.assertEqual(out.strip(), '123END', msg=err)

    def test_inline_while_after_other_statements(self):
        out, err = _run(
            '10 I = 0 : WHILE I < 3 : I = I + 1 : PRINT I; : WEND : PRINT "END"\n'
        )
        self.assertEqual(out.strip(), '123END', msg=err)

    def test_while_false_skips_trailing_body_statements(self):
        out, err = _run(
            '10 WHILE 0 : PRINT "NO"\n'
            '20 PRINT "NO2"\n'
            '30 WEND : PRINT "END"\n'
        )
        self.assertEqual(out.strip(), 'END', msg=err)


class PrintStringComparisonTests(unittest.TestCase):
    def test_print_string_comparisons(self):
        out, err = _run(
            '10 A$ = "Q"\n'
            '20 PRINT "A"<"B"\n'
            '30 PRINT "B">"A"\n'
            '40 PRINT "A"="A"\n'
            '50 PRINT "A"<>"A"\n'
            '60 PRINT A$="Q"\n'
            '70 PRINT "A"+"B"="AB"\n'
            '80 PRINT "X"; A$="Q"; "Y"\n'
        )
        self.assertEqual(
            out.splitlines(), ['-1', '-1', '-1', '0', '-1', '-1', 'X-1Y'], msg=err,
        )

    def test_print_string_plus_number_is_an_error(self):
        out, err = _run('10 PRINT "A" + 1\n')
        self.assertNotEqual(out.strip(), 'A', msg=err)
        self.assertIn('?', out + err)


class DimKeepsScalarTests(unittest.TestCase):
    def test_dim_does_not_clear_same_named_scalar(self):
        for dialect in ('mini', 'bbc', 'mits'):
            out, err = _run(
                '10 A = 1\n'
                '20 DIM A(3)\n'
                '30 A(2) = 7\n'
                '40 PRINT A\n'
                '50 PRINT A(2)\n',
                dialect,
            )
            self.assertEqual(out.split(), ['1', '7'], msg=(dialect, err))
            self.assertNotIn('SyntaxWarning', err, msg=dialect)


if __name__ == '__main__':
    unittest.main()
