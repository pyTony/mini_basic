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


if __name__ == '__main__':
    unittest.main()
