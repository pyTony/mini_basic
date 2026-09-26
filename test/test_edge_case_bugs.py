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
        lines = [line for line in out.splitlines() if not line.startswith('?')]
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
