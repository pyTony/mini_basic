"""Edge-case BASIC programs that used to crash, hang, or give wrong results."""
from __future__ import annotations

import io
import math
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


class IntegerOpSignTests(unittest.TestCase):
    """MS and BBC BASIC truncate toward zero: MOD takes the dividend's sign."""

    def test_mod_sign_follows_dividend(self):
        for dialect in ('mini', 'bbc', 'mits'):
            out, err = _run(
                '10 PRINT -7 MOD 3\n'
                '20 PRINT 7 MOD -3\n'
                '30 PRINT 7 MOD 3\n'
                '40 A = -7 : B = 3 : PRINT A MOD B\n',
                dialect,
            )
            self.assertEqual(out.split(), ['-1', '1', '1', '-1'], msg=(dialect, err))

    def test_integer_division_truncates(self):
        out, err = _run('10 PRINT -7 \\ 2\n20 PRINT 7 \\ -2\n30 PRINT 7 \\ 2\n', 'mits')
        self.assertEqual(out.split(), ['-3', '-3', '3'], msg=err)
        out, err = _run('10 PRINT -7 DIV 2\n20 A% = -7 : PRINT A% DIV 2\n', 'bbc')
        self.assertEqual(out.split(), ['-3', '-3'], msg=err)

    def test_mod_by_zero_is_an_error(self):
        out, err = _run('10 PRINT 5 MOD 0\n')
        self.assertIn('division by zero', (out + err).lower())


class PowerAssociativityTests(unittest.TestCase):
    def test_power_is_left_associative(self):
        for dialect in ('mini', 'bbc', 'mits'):
            out, err = _run(
                '10 PRINT 2^3^2\n'
                '20 PRINT 2^(3^2)\n'
                '30 PRINT (2^3)^2\n'
                '40 X = 2 : PRINT X^3^2\n'
                '50 PRINT -3^2\n',
                dialect,
            )
            self.assertEqual(
                out.split(), ['64', '512', '64', '64', '-9'], msg=(dialect, err),
            )


class ValExponentTests(unittest.TestCase):
    def test_val_reads_exponent(self):
        out, err = _run(
            '10 PRINT VAL("1E3")\n'
            '20 PRINT VAL("2.5E-1")\n'
            '30 PRINT VAL("  12AB")\n'
            '40 PRINT VAL("1E")\n'
        )
        self.assertEqual(out.split(), ['1000', '0.25', '12', '1'], msg=err)


class DoubledQuoteTests(unittest.TestCase):
    """"" inside a string literal is one quote character."""

    def test_print_doubled_quotes(self):
        for dialect in ('mini', 'bbc'):
            out, err = _run(
                '10 PRINT "SAY ""HI"""\n'
                '20 A$ = """" : PRINT LEN(A$); A$\n'
                '30 B$ = "X""Y" : PRINT B$; LEN(B$)\n',
                dialect,
            )
            self.assertEqual(
                out.splitlines(), ['SAY "HI"', '1"', 'X"Y3'], msg=(dialect, err),
            )

    def test_doubled_quote_with_colon_stays_in_string(self):
        out, err = _run('10 PRINT "A"":B" : PRINT "C"\n')
        self.assertEqual(out.splitlines(), ['A":B', 'C'], msg=err)


    def test_doubled_quotes_in_data_if_and_instr(self):
        out, err = _run(
            '10 DATA "A""B", 2\n'
            '20 READ X$, N : PRINT X$; N\n'
            '30 IF X$ = "A""B" THEN PRINT "EQ"\n'
            '40 PRINT INSTR("XY""Z", """")\n',
        )
        self.assertEqual(out.splitlines(), ['A"B2', 'EQ', '3'], msg=err)


class Chr34ConcatTests(unittest.TestCase):
    def test_concat_after_chr34_keeps_tail(self):
        out, err = _run('10 Q$ = "Q" + CHR$(34) + "R" : PRINT Q$; LEN(Q$)\n')
        self.assertEqual(out.split(), ['Q"R3'], msg=err)

    def test_print_instr_with_concat_argument(self):
        out, err = _run('10 PRINT INSTR("XY" + CHR$(34) + "Z", CHR$(34))\n')
        self.assertEqual(out.split(), ['3'], msg=err)


class FnLocalErrorTests(unittest.TestCase):
    def test_on_error_local_traps_return_expression(self):
        out, err = _run(
            '10 PRINT FNa(1, 0)\n'
            '100 DEF FNa(Y, X) : ON ERROR LOCAL = 7\n'
            '110 = ATN(Y/X)\n',
            'bbc',
        )
        self.assertEqual(out.split(), ['7'], msg=err)


class NestedIfElseTests(unittest.TestCase):
    def test_else_binds_to_inner_if(self):
        for dialect in ('mini', 'bbc'):
            out, err = _run(
                '10 A = 1 : B = 2\n'
                '20 IF A = 1 THEN IF B = 3 THEN PRINT "X" ELSE PRINT "Y"\n'
                '30 IF A = 2 THEN IF B = 2 THEN PRINT "P" ELSE PRINT "Q"\n'
                '40 PRINT "END"\n',
                dialect,
            )
            # BBC: a false IF jumps to the first ELSE on the line (line 30 → Q).
            self.assertEqual(out.split(), ['Y', 'Q', 'END'], msg=(dialect, err))

    def test_else_if_chain(self):
        out, err = _run(
            '10 FOR B = 1 TO 3\n'
            '20 IF B = 1 THEN PRINT "P" ELSE IF B = 2 THEN PRINT "Q" ELSE PRINT "R"\n'
            '30 NEXT\n',
            'bbc',
        )
        self.assertEqual(out.split(), ['P', 'Q', 'R'], msg=err)


class CaseOtherwiseTests(unittest.TestCase):
    def test_otherwise_statement_on_same_line(self):
        out, err = _run(
            '10 FOR X = 1 TO 4\n'
            '20 CASE X OF\n'
            '30 WHEN 1 : PRINT "ONE"\n'
            '40 WHEN 2, 3 : PRINT "TWOTHREE"\n'
            '50 OTHERWISE PRINT "OTHER"\n'
            '60 ENDCASE\n'
            '70 NEXT\n',
            'bbc',
        )
        self.assertEqual(
            out.split(), ['ONE', 'TWOTHREE', 'TWOTHREE', 'OTHER'], msg=err,
        )


class NumberPrintTests(unittest.TestCase):
    def test_float_noise_is_not_printed(self):
        out, err = _run(
            '10 PRINT 0.1 + 0.2\n'
            '20 FOR I = 0 TO 1 STEP 0.1 : NEXT : PRINT I\n'
            '30 PRINT 1 / 3\n'
        )
        self.assertEqual(
            out.split(), ['0.3', '1.1', '0.333333333333333'], msg=err,
        )

    def test_leading_zero_and_plus_literals(self):
        out, err = _run(
            '10 PRINT 010\n'
            '20 PRINT +5\n'
            '30 A = 010 : PRINT A\n'
            '40 PRINT 007 + 1\n'
            '50 PRINT 0.5; 1.05\n'
        )
        self.assertEqual(out.split(), ['10', '5', '10', '8', '0.51.05'], msg=err)


class TabColumnTests(unittest.TestCase):
    def test_bbc_tab_is_zero_based(self):
        out, err = _run('10 PRINT TAB(5); "X"\n20 PRINT "AB"; TAB(4); "Y"\n', 'bbc')
        self.assertEqual(out.splitlines(), ['     X', 'AB  Y'], msg=err)

    def test_ms_tab_is_one_based(self):
        out, err = _run('10 PRINT TAB(5); "X"\n', 'mits')
        self.assertEqual(out.splitlines(), ['    X'], msg=err)

    def test_second_tab_on_line_counts_columns_once(self):
        for dialect, line in (('mits', '    X    Y'), ('mini', '    X    Y'), ('bbc', '     X    Y')):
            out, err = _run('10 PRINT TAB(5); "X"; TAB(10); "Y"\n', dialect)
            self.assertEqual(out.splitlines(), [line], msg=(dialect, err))

    def test_bbc_consecutive_tabs_stay_on_one_line(self):
        out, err = _run('10 FOR I% = 1 TO 5 : PRINT TAB(I%); "*"; : NEXT\n', 'bbc')
        self.assertEqual(out.splitlines(), [' *****'], msg=err)


class CrunchedMsCodeTests(unittest.TestCase):
    """MS / Commodore BASIC ignore spaces: PRINTA is PRINT A."""

    def test_crunched_statements(self):
        for dialect in ('mits', 'commodore'):
            out, err = _run(
                '10 A=2:PRINTA\n'
                '20 PRINT"X";A\n'
                '30 GOTO50\n'
                '40 PRINT"NO"\n'
                '50 IFA=2THEN70\n'
                '60 PRINT"NO2"\n'
                '70 IFA<>2THENPRINT"NO3"\n'
                '80 FORI=1TO3:PRINTI;:NEXTI\n'
                '90 GOSUB200:END\n'
                '200 PRINT"SUB":RETURN\n',
                dialect,
            )
            self.assertEqual(out.split(), ['2', 'X2', '123SUB'], msg=(dialect, err))

    def test_crunched_on_goto_and_rem_payload(self):
        out, err = _run(
            '10 K=2:ONKGOTO100,200\n'
            '100 PRINT"ONE":END\n'
            '200 PRINT"TWO":REMPRINTNOT\n',
            'mits',
        )
        self.assertEqual(out.split(), ['TWO'], msg=err)


def _run_with_input(src: str, replies: list, dialect: str = 'mini') -> tuple[str, str]:
    from unittest.mock import patch

    with patch('builtins.input', side_effect=list(replies)):
        return _run(src, dialect)


class InputReplyTests(unittest.TestCase):
    def test_quoted_reply_drops_quotes(self):
        for dialect in ('mini', 'mits'):
            out, err = _run_with_input(
                '10 INPUT N$\n20 PRINT "["; N$; "]"\n',
                ['"quoted, text"'],
                dialect,
            )
            self.assertIn('[quoted, text]', out, msg=(dialect, err))

    def test_quoted_item_in_list(self):
        out, err = _run_with_input(
            '10 INPUT A$, B\n20 PRINT A$; "|"; B\n',
            ['"x, y", 5'],
        )
        self.assertIn('x, y|5', out, msg=err)

    def test_missing_values_continue_on_next_line(self):
        for dialect in ('mini', 'mits'):
            out, err = _run_with_input(
                '10 INPUT A, B\n20 PRINT A + B\n',
                ['1', '2'],
                dialect,
            )
            self.assertIn('3', out.splitlines()[-1], msg=(dialect, out, err))
            self.assertNotIn('Enter a number', out + err, msg=dialect)


class BasicErrorWordingTests(unittest.TestCase):
    """Errors should read as BASIC, not as leaked Python exception text."""

    LEAKS = (
        'float()', 'complex', 'could not convert', 'object is not',
        'never closed', 'container or iterable', 'nonnegative',
        'expected a positive', 'real number', 'unsupported operand',
    )

    def _assert_basic_error(self, line: str, expected: str) -> None:
        out, err = _run(f'10 {line}\n')
        text = (out + err).lower()
        self.assertIn('?', text, msg=line)
        for leak in self.LEAKS:
            self.assertNotIn(leak, text, msg=(line, text))
        self.assertIn(expected, text, msg=(line, text))

    def test_python_wording_is_translated(self):
        cases = (
            ('PRINT (-8)^(1/3)', 'illegal function call'),
            ('PRINT SQR(-1)', 'illegal function call'),
            ('PRINT LOG(0)', 'illegal function call'),
            ('A = "X"', 'type mismatch'),
            ('PRINT (1 + 2', 'syntax'),
            ('PRINT 1 in 1', 'syntax'),
        )
        for line, expected in cases:
            self._assert_basic_error(line, expected)


class IntegerAssignTruncatesTests(unittest.TestCase):
    """BBC BASIC and BBC SDL truncate toward zero when storing into A%."""

    def test_real_to_integer_variable_truncates(self):
        for dialect in ('bbc', 'mini'):
            out, err = _run(
                '10 A% = 3.7 : B% = -3.7 : C% = 7 / 2\n'
                '20 DIM X%(2) : X%(1) = 2.9 : X%(1) += 0.9\n'
                '30 PRINT A%\n40 PRINT B%\n50 PRINT C%\n60 PRINT X%(1)\n',
                dialect,
            )
            # X%(1) = 2.9 → 2; += 0.9 → 2.9 → 2 (small steps stall, as in BBC).
            self.assertEqual(out.split(), ['3', '-3', '3', '2'], msg=(dialect, err))

    def test_ms_dialects_still_round(self):
        out, err = _run('10 A% = 3.7 : B% = -3.7\n20 PRINT A%\n30 PRINT B%\n', 'mits')
        self.assertEqual(out.split(), ['4', '-4'], msg=err)


class CompiledMathBuiltinTests(unittest.TestCase):
    """SIN/COS/RAD/... stay on the compiled fast path (jclock spring loop)."""

    def _interp(self):
        return BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )

    def test_math_builtins_compile(self):
        interp = self._interp()
        for expr in (
            '320 + R*SIN(RAD(T)) - X - 250',
            'ABS(X) + SQR(Y) + COS(T) + TAN(T) + ATN(T) + DEG(T) + EXP(T)',
        ):
            compiled = interp._get_compiled_expr(expr, is_condition=False)
            self.assertFalse(compiled.use_fallback, msg=expr)
            self.assertIsNotNone(compiled.code, msg=expr)

    def test_compiled_values_match(self):
        out, err = _run(
            '10 T = 30 : R = 300 : Y = 16 : X = -2.5\n'
            '20 PRINT 320 + R*SIN(RAD(T)) - 250\n'
            '30 PRINT ABS(X) + SQR(Y)\n'
            '40 PRINT DEG(ATN(1))\n',
            'bbc',
        )
        self.assertEqual(out.split(), ['220', '6.5', '45'], msg=err)

    def test_array_reads_compile_after_dim_even_if_warmed_before(self):
        interp = self._interp()
        expr = '(X%+R*SIN(RAD(T))-X%(I%)-250)/(1+T/60)'
        early = interp._get_compiled_expr(expr)  # RUN warm-up: no DIM yet
        self.assertTrue(early.has_array)
        interp._dim_array('X%(50)')
        self.assertFalse(early.has_array)  # same object, now compiled
        self.assertFalse(early.use_fallback)
        interp.int_variables.update({'X': 320, 'I': 3})
        interp.variables.update({'R': 300.0, 'T': 30.0})
        interp._array_set('X', 'int', [3], 10)
        expected = (320 + 300 * 0.5 - 10 - 250) / (1 + 30 / 60)
        self.assertAlmostEqual(early.eval_numeric(interp), expected, places=9)

    def test_compiled_array_read_matches_slow_path_and_errors(self):
        out, err = _run(
            '10 DIM A(3), B%(2, 2)\n'
            '20 A(2) = 1.5 : B%(1, 2) = 7 : I = 2\n'
            '30 PRINT A(I) * 2 + B%(1, I)\n'
            '40 PRINT A(B%(1,2) - 5)\n'
            '50 PRINT A(9)\n',
            'bbc',
        )
        lines = [line.strip() for line in out.splitlines() if not line.startswith('?')]
        self.assertEqual(lines, ['10', '1.5'], msg=err)
        self.assertIn('subscript', (out + err).lower())

    def test_sqr_negative_is_still_an_error(self):
        out, err = _run('10 Y = -4 : PRINT SQR(Y)\n', 'bbc')
        self.assertIn('illegal function call', (out + err).lower())


class BbcSystemVariableTests(unittest.TestCase):
    """@vdu% is a BBCSDL system variable, not the VDU keyword glued to %."""

    def test_at_vdu_is_not_split_as_keyword(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        self.assertEqual(
            interp.canonicalize_program_line('@vdu%?74 AND= &7F : MODE 7'),
            '@vdu%?74 AND= &7F : MODE 7',
        )

    def test_lowercase_words_are_not_crunched_keywords_in_bbc(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        # print5 / mode7 are variable names in BBC (keywords are uppercase).
        self.assertEqual(interp.canonicalize_program_line('print5 = 1'), 'print5 = 1')
        self.assertEqual(interp.canonicalize_program_line('MODE7'), 'MODE 7')


class PrintApostropheTests(unittest.TestCase):
    """Checked on ARM BBC BASIC V 1.05: PRINT "A"'' → A, two blank lines, prompt."""

    def test_trailing_apostrophes_are_newlines_plus_final_newline(self):
        out, err = _run('10 PRINT "A"\'\'\n20 PRINT "B"\n', 'bbc')
        self.assertEqual(out, 'A\n\n\nB\n', msg=err)

    def test_single_trailing_apostrophe(self):
        out, err = _run('10 PRINT "A"\'\n20 PRINT "B"\n', 'bbc')
        self.assertEqual(out, 'A\n\nB\n', msg=err)

    def test_apostrophe_between_items_and_semicolon_end(self):
        out, err = _run('10 PRINT "A"\'"B";\n20 PRINT "C"\n', 'bbc')
        self.assertEqual(out, 'A\nBC\n', msg=err)


class ApostropheCommentTests(unittest.TestCase):
    """mini: ' is a REM synonym. bbc: ' is only the PRINT/INPUT newline."""

    def test_mini_tail_comment_hides_colon_statements(self):
        out, err = _run('10 X = 1 \' note: PRINT "NO"\n20 PRINT X\n')
        self.assertEqual(out.split(), ['1'], msg=err)

    def test_mini_print_tail_comment(self):
        out, err = _run('10 PRINT "A" \' show it\n20 PRINT "B"; \' more text: PRINT "NO"\n30 PRINT "C"\n')
        self.assertEqual(out.splitlines(), ['A', 'BC'], msg=err)

    def test_mini_glued_apostrophe_is_still_print_newline(self):
        out, err = _run('10 PRINT "A"\'"B"\n20 PRINT "C"\'\'\n30 PRINT "D"\n')
        self.assertEqual(out, 'A\nB\nC\n\n\nD\n', msg=err)

    def test_mini_bbc_style_print_apostrophes_survive(self):
        # Unhinted BBCSDL programs (animal.txt) run as mini.
        out, err = _run(
            '10 PRINT \' "Animals:"\n'
            '20 A$ = "Y" : IF A$="Y" THEN PRINT "Why not?"\'\' ELSE PRINT "NO"\n'
            '30 G1$ = "a" : G2$ = "b" : PRINT G1$ \' G2$\n'
            '40 PRINT \'"R" : PRINT "S" \'"T"\n'
            '50 PRINT "END"\n'
        )
        self.assertEqual(
            out, '\nAnimals:\nWhy not?\n\n\na\nb\n\nR\nS\nT\nEND\n', msg=err,
        )

    def test_mini_whole_line_comment(self):
        out, err = _run('10 \' whole line: PRINT "NO"\n20 PRINT "YES"\n')
        self.assertEqual(out.split(), ['YES'], msg=err)

    def test_bbc_apostrophe_is_not_a_comment(self):
        out, err = _run('10 X = 1 \' note\n20 PRINT "AFTER"\n', 'bbc')
        self.assertIn('?', out + err)
        self.assertNotIn('AFTER', out)

    def test_bbc_whole_line_apostrophe_is_not_a_comment(self):
        out, err = _run('10 \' just a note\n20 PRINT "AFTER"\n', 'bbc')
        self.assertIn('?', out + err)
        self.assertNotIn('AFTER', out)

    def test_bbc_apostrophe_dialect_hint_still_applies(self):
        out, err = _run('10 \' dialect: bbc\n20 PRINT "OK"\n', 'bbc')
        self.assertEqual(out.strip(), 'OK', msg=err)

    def test_bbc_print_apostrophe_newlines(self):
        out, err = _run('10 PRINT "A" \' "B"\n', 'bbc')
        self.assertEqual(out, 'A\nB\n', msg=err)


class BbcNumericPrintFieldTests(unittest.TestCase):
    """@% = &90A default: G9 format, numbers right-justified in 10 columns."""

    def _lines(self, program: str) -> list:
        out, err = _run(program, 'bbc')
        self.assertNotIn('?', out + err, msg=out + err)
        return out.splitlines()

    def test_plain_print_right_justifies(self):
        # ARM BBC BASIC V: A%=3.7 : PRINT A% → "         3"
        self.assertEqual(
            self._lines('10 A% = 3.7 : PRINT A%\n20 PRINT -7\n30 PRINT 3.5\n'),
            ['         3', '        -7', '       3.5'],
        )

    def test_semicolon_switches_off_justification(self):
        self.assertEqual(
            self._lines('10 PRINT "X";3\n20 PRINT 1;2\n30 PRINT 1;2,3\n'),
            # , moves to the next 10-column field, then right-justifies in it.
            ['X3', '         12', '         12' + ' ' * 18 + '3'],
        )

    def test_nine_significant_digits(self):
        self.assertEqual(
            self._lines('10 PRINT 1/3\n20 PRINT PI\n30 PRINT 0.1+0.2\n'),
            ['0.333333333', '3.14159265', '       0.3'],
        )

    def test_str_dollar_does_not_pad(self):
        self.assertEqual(self._lines('10 PRINT STR$(3);"|";STR$(1/3)\n'), ['3|0.333333333'])

    def test_mini_keeps_unpadded_numbers(self):
        out, err = _run('10 PRINT 3\n20 PRINT 1/3\n')
        self.assertEqual(out.splitlines(), ['3', '0.333333333333333'], msg=err)


class KeywordIsNotLabelTests(unittest.TestCase):
    """CLOSE : / CONT : / REPORT : are statements, not labels named CLOSE."""

    def test_bare_keyword_before_colon_is_a_statement(self):
        for dialect in ('mini', 'mits'):
            out, err = _run('10 CLOSE : PRINT "C"\n20 PRINT "D"\n', dialect)
            self.assertEqual(out.split(), ['C', 'D'], msg=(dialect, out, err))

    def test_real_label_still_works(self):
        out, err = _run('10 GOTO there\n20 PRINT "NO"\n30 there: PRINT "YES"\n')
        self.assertEqual(out.split(), ['YES'], msg=err)


class InputHashArrayTests(unittest.TestCase):
    def test_bad_number_into_array_element_stores_zero(self):
        import os
        import tempfile

        old = os.getcwd()
        os.chdir(tempfile.mkdtemp())
        try:
            out, err = _run(
                '10 DIM A(3), B%(3)\n'
                '20 F% = OPENOUT("t.dat") : PRINT# F%, "abc", "xyz" : CLOSE# F%\n'
                '30 A(1) = 5 : B%(2) = 7\n'
                '40 F% = OPENIN("t.dat") : INPUT# F%, A(1), B%(2) : CLOSE# F%\n'
                '50 PRINT A(1)\n60 PRINT B%(2)\n',
                'bbc',
            )
        finally:
            os.chdir(old)
        self.assertNotIn('indices', out + err)
        self.assertEqual([line.strip() for line in out.splitlines()], ['0', '0'], msg=err)


class LoadLegacyEncodingTests(unittest.TestCase):
    """Old BBC / Windows sources are Latin-1 / CP1252, not UTF-8."""

    def _load_bytes(self, data: bytes):
        import os
        import tempfile

        fd, path = tempfile.mkstemp(suffix='.bas')
        os.close(fd)
        try:
            with open(path, 'wb') as handle:
                handle.write(data)
            interp = BASICInterpreter(
                InterpreterConfig(dialect='bbc', display='none', display_locked=True)
            )
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                ok = interp.load(path, announce=False)
            return ok, interp, out.getvalue() + err.getvalue()
        finally:
            os.remove(path)

    def test_latin1_source_loads(self):
        ok, interp, msgs = self._load_bytes(
            b'10 REM Copyright \xa9 1981\r\n20 PRINT "caf\xe9"\r\n'
        )
        self.assertTrue(ok, msgs)
        self.assertIn('©', interp.program[10])
        self.assertIn('café', interp.program[20])

    def test_binary_junk_is_still_rejected(self):
        ok, interp, msgs = self._load_bytes(b'\x00\x01\xff\xfe\x00junk')
        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main()


class InkeyPlatformIdTests(unittest.TestCase):
    """INKEY(-256) is the platform id; negative INKEY is standard BBC BASIC."""

    def test_inkey_minus_256_is_bbcsdl_id(self):
        for dialect in ('bbc', 'mini'):
            out, err = _run(
                '10 BB4W% = (INKEY(-256) == &57)\n'
                '20 PRINT BB4W%;" ";INKEY(-256)\n',
                dialect,
            )
            self.assertEqual(out.split(), ['0', '115'], msg=(dialect, err))

    def test_double_equals_is_equality(self):
        for dialect in ('bbc', 'mini'):
            out, err = _run(
                '10 X% = (3 == 3) : PRINT X%\n'
                '20 IF 3 == 3 THEN PRINT "y"\n'
                '30 IF 2 == 3 THEN PRINT "n" ELSE PRINT "e"\n'
                '40 PRINT (3 == &57)\n',
                dialect,
            )
            self.assertEqual(out.split(), ['-1', 'y', 'e', '0'], msg=(dialect, err))


class ColonlessUntilTests(unittest.TestCase):
    """BBC: UNTIL starts a new statement without a colon (disco.bbc line 660)."""

    def test_repeat_body_until_on_one_line(self):
        for dialect in ('bbc', 'mini'):
            out, err = _run(
                '10 i1% = 5 : REPEAT i2%=i2%+1 UNTIL i2%<>i1% AND i2%>6\n'
                '20 REPEAT A%=A%+1 UNTIL A%>3 : PRINT A%;" ";i2%\n'
                '30 REPEAT UNTIL TRUE\n'
                '40 REPEAT S$=S$+"UNTIL" UNTIL LEN(S$)>9\n'
                '50 REPEAT B%=B%+FNu(1) UNTIL(B%>2)\n'
                '60 PRINT S$;" ";B%\n'
                '70 END\n'
                '80 DEF FNu(x)=x\n',
                dialect,
            )
            self.assertEqual(out.split(), ['4', '7', 'UNTILUNTIL', '3'], msg=(dialect, err))
            self.assertNotIn('UNTIL', err, msg=dialect)


class ByteVariableTests(unittest.TestCase):
    """BBCSDL byte variables (NAME&) in expressions (disco.bbc line 950)."""

    def test_byte_vars_read_in_expressions(self):
        out, err = _run(
            '10 r1&=10 : r2&=250 : f=0.5\n'
            '20 r& = r1& + f * (r2& - r1&)\n'
            '30 PRINT r&;" ";(r2&-r1&)\n'
            '40 x&=300 : y&=-1 : PRINT x&;" ";y&\n'
            '50 a%=7 : a&=3 : a=1.5 : PRINT a%;" ";a&;" ";a\n'
            '60 b&=5 : b&+=1 : PRINT b& AND &FF;" ";&10+b&\n',
            'bbc',
        )
        self.assertEqual(out.split(), ['130', '240', '44', '255', '7', '3', '1.5', '6', '22'], msg=err)
        self.assertEqual(err, '')


class RectangleStatementTests(unittest.TestCase):
    """RECTANGLE [FILL|SWAP] x,y,w[,h] [TO x,y] dispatch (disco.bbc)."""

    def test_rectangle_forms_reach_display(self):
        from unittest.mock import MagicMock, patch

        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        display = MagicMock()
        display.mouse_state.return_value = (0, 0, 0)
        interp._display = display
        for n, text in [
            (10, 'B%=64'),
            (20, 'RECTANGLE 2*(1+(B%-4)/2), 2, 8, 8'),
            (30, 'RECTANGLE FILL 1, 2, 3'),
            (40, 'RECTANGLE SWAP 2*1, 2*2, 2*B%-1, 2*B%-1 TO 2*3, 2*4'),
            (50, 'RECTANGLE 1, 2, 3, 4 TO 5, 6'),
            (60, 'RECTANGLE FILL 1, 2, 3, 4 TO 5, 6'),
        ]:
            interp.set_program_line(n, text)
        errs = []
        with patch.object(interp, '_graphics_plot_enabled', return_value=True), \
                patch.object(interp, '_display_enabled', return_value=True), \
                patch.object(interp, '_ensure_display'), \
                patch.object(interp, '_sync_graphics'), \
                patch.object(interp, '_runtime_error', side_effect=lambda m, *a, **k: errs.append(m)):
            interp.run()
        self.assertEqual(errs, [])
        display.draw_rectangle.assert_called_once_with(62, 2, 8, 8)
        display.fill_rectangle.assert_called_once_with(1, 2, 3, 3)
        self.assertEqual(display.transfer_rectangle.call_args_list, [
            ((2, 4, 127, 127, 6, 8, 'swap'),),
            ((1, 2, 3, 4, 5, 6, 'copy'),),
            ((1, 2, 3, 4, 5, 6, 'move'),),
        ])


class EllipseStatementTests(unittest.TestCase):
    """ELLIPSE [FILL] x,y,a,b[,angle] dispatch (surks.bbc grid effect)."""

    def test_ellipse_forms_reach_display(self):
        from unittest.mock import MagicMock, patch

        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        display = MagicMock()
        display.mouse_state.return_value = (0, 0, 0)
        interp._display = display
        for n, text in [
            (10, 'x%=10 : y%=20 : r%=5 : I%=3'),
            (20, 'ELLIPSE 2*x%, 2*y%, 2*r%, 2*I%'),
            (30, 'ELLIPSE FILL 1, 2, 3, 4, 0.5'),
        ]:
            interp.set_program_line(n, text)
        errs = []
        with patch.object(interp, '_graphics_plot_enabled', return_value=True), \
                patch.object(interp, '_display_enabled', return_value=True), \
                patch.object(interp, '_ensure_display'), \
                patch.object(interp, '_sync_graphics'), \
                patch.object(interp, '_runtime_error', side_effect=lambda m, *a, **k: errs.append(m)):
            interp.run()
        self.assertEqual(errs, [])
        self.assertEqual(display.draw_ellipse.call_args_list, [
            ((20, 40, 10, 6, 0.0, False),),
            ((1, 2, 3, 4, 0.5, True),),
        ])

    def test_ellipse_lowercase_keyword_folds_in_mini(self):
        # CLAUDE.md keyword-case policy: mini is not strict about keyword case.
        out, err = _run(
            '10 gcol 0,1\n'
            '20 ellipse 20,20,10,5\n'
            '30 print "ok"\n',
        )
        self.assertEqual(out.split(), ['ok'], msg=err)
        self.assertEqual(err, '')


class EllipseGeometryTests(unittest.TestCase):
    """Pixel-level checks for BBCGraphics.draw_ellipse (axis-aligned, unrotated)."""

    def test_outline_touches_axis_extremes_and_leaves_centre_clear(self):
        from mini_basic.bbc_graphics import BBCGraphics

        gfx = BBCGraphics(64, 64)
        gfx.gcol(0, 1)
        gfx.draw_ellipse(32, 32, 20, 10, filled=False)
        self.assertEqual(gfx.point_colour(32 + 20, 32), 1)
        self.assertEqual(gfx.point_colour(32 - 20, 32), 1)
        self.assertEqual(gfx.point_colour(32, 32 + 10), 1)
        self.assertEqual(gfx.point_colour(32, 32 - 10), 1)
        self.assertEqual(gfx.point_colour(32, 32), 0)

    def test_filled_area_matches_pi_a_b(self):
        from mini_basic.bbc_graphics import BBCGraphics

        a, b = 15, 8
        gfx = BBCGraphics(64, 64)
        gfx.gcol(0, 1)
        gfx.draw_ellipse(32, 32, a, b, filled=True)
        count = sum(
            1
            for sy in range(64)
            for sx in range(64)
            if gfx.point_colour(sx, sy) == 1
        )
        expected = math.pi * a * b
        self.assertLess(abs(count - expected) / expected, 0.15)


class SurksMiniSmokeTests(unittest.TestCase):
    """examples/graphics/surks_mini.bbc: mini_basic-compatible fork of surks.bbc
    (original uses a struct-array element read, circle{(I%)}.r%, which
    mini_basic doesn't support yet — see docs/LANGUAGE_FEATURES_1.00.md).
    """

    def test_runs_without_runtime_error(self):
        import threading

        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.load('examples/graphics/surks_mini.bbc', announce=False)

        errors = []

        def patched(msg, *args, **kwargs):
            errors.append((msg, kwargs.get('statement')))
            raise SystemExit(1)

        interp._runtime_error = patched

        thread = threading.Thread(target=interp.run, daemon=True)
        thread.start()
        thread.join(timeout=5)
        self.assertEqual(errors, [])


class StructArrayFieldTests(unittest.TestCase):
    """DIM struct{} / struct-array element access, including indexed
    reads/writes (surks.bbc's circle{(I%)}.r%). Struct-array element keys
    are built from the index's evaluated value (see
    _normalize_struct_array_index_refs in mini_basic/runtime_parts/expr.py),
    so a write via one index variable and a read via another holding the
    same value must agree on the same element.
    """

    def test_flat_struct_numeric_and_string_fields_read_write(self):
        # DIM name{a%,b$,c} / name.a% read+assign — documented as already working.
        for dialect in ('mini', 'bbc'):
            out, err = _run(
                '10 DIM pt{ x%, y%, label$ }\n'
                '20 pt.x% = 3 : pt.y% = 4 : pt.label$ = "P"\n'
                '30 pt.x% = pt.x% + 1\n'
                '40 PRINT pt.x%; pt.y%; pt.label$\n',
                dialect,
            )
            self.assertEqual(out.split(), ['44P'], msg=(dialect, err))
            self.assertEqual(err, '')

    def test_struct_array_element_write_does_not_error(self):
        # DIM circle{(n) x%,y%,r%,t%} ; circle{(0)}.r% = v — write side works.
        out, err = _run(
            '10 DIM circle{(4) x%, y%, r%, t%}\n'
            '20 circle{(0)}.x% = 5\n'
            '30 circle{(0)}.r% = 7\n'
            '40 PRINT "ok"\n',
        )
        self.assertEqual(out.split(), ['ok'], msg=err)
        self.assertEqual(err, '')

    def test_struct_array_element_read_by_variable_index(self):
        # circle{(I%)}.r% — reading a struct-array element's field back by a
        # variable index (same variable used for the write).
        out, err = _run(
            '10 DIM circle{(4) x%, y%, r%, t%}\n'
            '20 circle{(0)}.r% = 7\n'
            '30 I% = 0\n'
            '40 R% = circle{(I%)}.r%\n'
            '50 PRINT R%\n',
        )
        self.assertEqual(out.split(), ['7'], msg=err)
        self.assertEqual(err, '')

    def test_struct_array_element_write_and_read_use_different_index_vars(self):
        # circle{(N%)}.r% = 7 written via N%, then read back via a
        # differently-named variable I% holding the same value. This is the
        # exact pattern that broke examples/graphics/surks.bbc (a circle
        # collision-check loop writes with one loop variable and reads back
        # with another) until struct-array keys were built from the index's
        # evaluated value instead of its source text.
        out, err = _run(
            '10 DIM circle{(4) x%, y%, r%, t%}\n'
            '20 N% = 0\n'
            '30 circle{(N%)}.r% = 7\n'
            '40 I% = 0\n'
            '50 PRINT circle{(I%)}.r%\n',
        )
        self.assertEqual(out.split(), ['7'], msg=err)
        self.assertEqual(err, '')


class SwirlStructSysTests(unittest.TestCase):
    """swirl.bbc: DIM mode{}, SYS SDL calls, ABSSIN glue, PLOT 165 arcs."""

    def test_struct_member_named_like_keyword_in_mini(self):
        # mode.w% must not fold to the MODE statement.
        for dialect in ('mini', 'bbc'):
            out, err = _run(
                '10 DIM mode{ fmt%, w%, h% }\n'
                '20 mode.w% = 640\n'
                '30 PRINT mode.w% + 1\n',
                dialect,
            )
            self.assertEqual(out.split(), ['641'], msg=(dialect, err))

    def test_sys_display_mode_fills_struct_and_ticks_to_var(self):
        out, err = _run(
            '10 DIM mode{ fmt%, w%, h%, r%, d% }\n'
            '20 SYS "SDL_GetCurrentDisplayMode", 0, mode{}\n'
            '30 ok% = mode.w% > 0 AND mode.h% > 0 : PRINT ok%\n'
            '40 G$ = "SDL_GetTicks"\n'
            '50 SYS G$ TO T0%\n'
            '60 SYS "SDL_Delay", 20\n'
            '70 SYS G$TO T1%\n'
            '80 PRINT T1% - T0% >= 20\n'
        )
        self.assertEqual(out.split(), ['-1', '-1'], msg=err)

    def test_sys_unknown_name_is_out_of_scope(self):
        out, err = _run('10 SYS "OS_Write0", "hi"\n')
        self.assertIn('? Out of scope: SYS', out + err)
        self.assertIn('OS_Write0', out + err)

    def test_monadic_glued_to_function_call(self):
        out, err = _run(
            '10 x = -0.5\n'
            '20 PRINT ABSSIN(x) = ABS(SIN(x))\n'
            '30 PRINT SINRAD(PI/2)\n'
        )
        self.assertEqual(out.split(), ['-1', '1'], msg=err)


class PlotArcTests(unittest.TestCase):
    def test_plot_165_draws_anticlockwise_arc_with_thickness(self):
        from mini_basic.bbc_graphics import BBCGraphics

        gfx = BBCGraphics(64, 64)
        gfx.gcol(0, 1)
        gfx.line_thickness = 3
        gfx.move_absolute(32, 32)       # centre
        gfx.move_absolute(52, 32)       # start: east, radius 20
        gfx.plot_code(165, 32, 60)      # end direction: north
        # Quarter arc east → north only (anticlockwise).
        self.assertEqual(gfx.point_colour(32 + 14, 32 + 14), 1)  # 45°, r≈19.8
        self.assertEqual(gfx.point_colour(32 - 14, 32 + 14), 0)  # 135°
        self.assertEqual(gfx.point_colour(32 + 14, 32 - 14), 0)  # -45°
        self.assertEqual(gfx.point_colour(32, 32), 0)            # centre untouched


class PlotArcSeamOverlapTests(unittest.TestCase):
    """A rotating arc's cut ends must not flicker pixel-by-pixel (swirl.bbc)."""

    def test_arc_seam_pixel_stays_lit_across_tiny_rotation(self):
        from mini_basic.bbc_graphics import BBCGraphics

        radius = 20
        for deg in range(0, 360, 3):
            gfx = BBCGraphics(64, 64)
            gfx.gcol(0, 1)
            gfx.line_thickness = 1
            a0 = math.radians(deg)
            a1 = a0 + math.pi  # half-circle sweep, like swirl.bbc
            start_x = 32 + round(radius * math.cos(a0))
            start_y = 32 + round(radius * math.sin(a0))
            gfx.move_absolute(32, 32)
            gfx.move_absolute(start_x, start_y)
            gfx.plot_code(
                165,
                32 + round(1000 * math.cos(a1)),
                32 + round(1000 * math.sin(a1)),
            )
            # The pixel right at the arc's start must always be lit, at any
            # sub-degree rotation — not on/off depending on rounding.
            self.assertEqual(
                gfx.point_colour(start_x, start_y),
                1,
                msg=f'deg={deg} start seam not lit',
            )
