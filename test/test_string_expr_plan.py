"""String expressions: static typing and the cached evaluation plan.

An expression's type is the type of its first operand: ``LEN(A$)+1`` is a
number even though it contains ``$``. String expressions that are plain
concatenations of literals, variables, array elements and common builtins are
parsed once and then evaluated without re-scanning their text.
"""
from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx, pytest.mark.timeout(15)]

DIALECTS = ('mini', 'bbc', 'mits')


def _interp(src: str, dialect: str) -> BASICInterpreter:
    interp = BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )
    for raw in src.strip().splitlines():
        num, _, text = raw.strip().partition(' ')
        interp.set_program_line(int(num), text)
    return interp


def _run(src: str, dialect: str = 'mini') -> tuple[str, str]:
    interp = _interp(src, dialect)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        interp.run()
    return out.getvalue(), err.getvalue()


class NumericExpressionWithStringsInPrintTests(unittest.TestCase):
    """PRINT of a numeric expression that mentions strings used to fail."""

    def test_print_numeric_builtin_of_string_plus_number(self):
        cases = (
            ('PRINT LEN(A$)+1', '3'),
            ('PRINT 1+LEN(A$)', '3'),
            ('PRINT LEN(A$)+ASC("A")', '67'),
            ('PRINT ASC("A")+1', '66'),
            ('PRINT VAL("12")+1', '13'),
            ('PRINT INSTR("hello","l")+1', '4'),
            ('PRINT -LEN(A$)+10', '8'),
            ('PRINT (LEN(A$)+1)*2', '6'),
        )
        for dialect in DIALECTS:
            for stmt, expected in cases:
                out, err = _run(f'10 A$="ab"\n20 {stmt}\n', dialect)
                self.assertEqual(out.strip(), expected, msg=(dialect, stmt, err))
                self.assertEqual(err, '', msg=(dialect, stmt))

    def test_string_items_still_print_as_strings(self):
        for dialect in DIALECTS:
            out, err = _run(
                '10 A$="ab"\n'
                '20 PRINT A$+"c"\n'
                '30 PRINT LEFT$(A$,1)+STR$(LEN(A$))\n'
                '40 PRINT CHR$(65+LEN(A$))\n',
                dialect,
            )
            self.assertEqual(out.split(), ['abc', 'a2', 'C'], msg=(dialect, err))

    def test_comparison_operand_numeric_with_string_function(self):
        for dialect in DIALECTS:
            out, err = _run(
                '10 A$="abc"\n'
                '20 IF 1+ASC(MID$(A$,2,1))=99 THEN PRINT "Y" ELSE PRINT "N"\n',
                dialect,
            )
            self.assertEqual(out.strip(), 'Y', msg=(dialect, err))


class StringPlanResultsTests(unittest.TestCase):
    """Results must match classic BASIC semantics (unchanged by the plan)."""

    PROGRAM = '''
10 A$="ab" : B$ = A$ + CHR$(34) + "c""d" + STR$(1.5)
20 PRINT B$ : PRINT LEN(B$)
30 DIM C$(3) : C$(2)="x" : D$=C$(2)+C$(1)+"|"+MID$(A$,2)+LEFT$(A$,1)+RIGHT$(A$,5)+STRING$(3,"z")+STRING$(2,65)
40 PRINT D$
50 PRINT MID$("hello",3,-1)+"|"+MID$("hello",0,2)+"|"+SPACE$(2)+"|"
60 E$=A$ : A$="changed" : PRINT E$;A$
70 FOR I=1 TO 3 : S$=S$+STR$(I)+"," : NEXT I : PRINT S$
80 PRINT LEN(A$)+ASC("A")+VAL("12")+INSTR("hello","l")
'''

    def test_results(self):
        for dialect in DIALECTS:
            out, err = _run(self.PROGRAM, dialect)
            self.assertEqual(
                [line.strip() for line in out.splitlines()],
                ['ab"c"d1.5', '9', 'x|baabzzzAA', '||  |', 'abchanged', '1,2,3,', '87'],
                msg=(dialect, err),
            )
            self.assertEqual(err, '', msg=dialect)

    def test_string_variable_named_like_a_builtin_prefix(self):
        # STRX$ / CHRIS$ / LEFTY$ are variables, not STR$ / CHR$ / LEFT$.
        for dialect in ('mini', 'bbc'):
            out, err = _run(
                '10 CHRIS$="c" : LEFTY$="l" : TIMES$="t"\n'
                '20 X$=CHRIS$+LEFTY$+TIMES$ : PRINT X$\n',
                dialect,
            )
            self.assertEqual(out.strip(), 'clt', msg=(dialect, err))

    def test_doubled_quote_is_one_quote_and_spaced_literals_join(self):
        # Checked on Archimedes BASIC V: PRINT "A""B" → A"B, PRINT "A" "B" → AB.
        for dialect in DIALECTS:
            out, err = _run(
                '10 PRINT "A""B"\n'
                '20 PRINT "A" "B"\n'
                '30 A$="x"+"A""B"+"y" : PRINT A$ : PRINT LEN(A$)\n'
                '40 X$=EVAL("""A""""B""") : PRINT X$\n',
                dialect,
            )
            self.assertEqual(
                out.splitlines(), ['A"B', 'AB', 'xA"By', '5', 'A"B'], msg=(dialect, err),
            )

    def test_mits_two_char_names_share_storage(self):
        out, err = _run('10 ABC$="x"\n20 Y$=ABD$+"!"\n30 PRINT Y$\n', 'mits')
        self.assertEqual(out.strip(), 'x!', msg=err)

    def test_numeric_added_to_string_is_still_an_error(self):
        for dialect in DIALECTS:
            out, err = _run('10 A$="a"+1\n20 PRINT "after"\n', dialect)
            self.assertNotIn('after', out, msg=dialect)
            self.assertTrue(err.strip(), msg=dialect)


class StringPlanNoRescanTests(unittest.TestCase):
    """Hot string expressions must not go through text expansion every time."""

    def _count_expansions(self, src: str, dialect: str) -> int:
        interp = _interp(src, dialect)
        calls = 0
        original = interp._expand_dynamic_calls

        def counting(expr: str) -> str:
            nonlocal calls
            calls += 1
            return original(expr)

        interp._expand_dynamic_calls = counting
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            interp.run()
        self.assertEqual(err.getvalue(), '', msg=dialect)
        return calls

    def test_loop_string_work_is_not_rescanned(self):
        src = '''
10 DIM A(10)
20 FOR I=1 TO 200
30 Y$=STR$(I)+"a"
40 Z$=Y$
50 N=LEN(Y$)+ASC("A")
60 W$=LEFT$(Z$,1)+MID$(Y$,2,1)+CHR$(65)
70 NEXT I
80 PRINT N;W$
'''
        for dialect in ('mini', 'bbc'):
            calls = self._count_expansions(src, dialect)
            self.assertLess(calls, 20, msg=dialect)


if __name__ == '__main__':
    unittest.main()
