"""A GOTO inside a subroutine must not end the caller's FOR/WHILE/REPEAT loop.

Super Star Trek's quadrant-name subroutine jumps around (GOTO 9210) while the
library-computer loop that called it is still running; RETURN comes back to
that loop's NEXT. Loops opened *inside* the subroutine are still dropped by
RETURN (MS BASIC), and a GOTO that leaves a loop in the same routine still
ends it.
"""
from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx, pytest.mark.timeout(15)]


def _run(dialect: str, src: str) -> tuple[str, str]:
    interp = BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )
    for raw in src.strip().splitlines():
        num, _, text = raw.partition(' ')
        interp.set_program_line(int(num), text)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        interp.run()
    return out.getvalue(), err.getvalue()


class GotoInsideGosubTests(unittest.TestCase):

    def test_for_loop_survives_goto_in_subroutine(self):
        for dialect in ('mits', 'commodore', 'mini', 'bbc'):
            out, err = _run(
                dialect,
                '10 FOR I=1 TO 3\n'
                '20 GOSUB 100\n'
                '30 PRINT I;"|";\n'
                '40 NEXT I\n'
                '50 PRINT "DONE":END\n'
                '100 GOTO 200\n'
                '200 RETURN\n',
            )
            self.assertEqual(err, '', msg=(dialect, err))
            self.assertEqual(out.replace(' ', '').strip(), '1|2|3|DONE', msg=(dialect, out))

    def test_nested_loops_and_several_gotos_in_the_subroutine(self):
        for dialect in ('mits', 'mini'):
            out, err = _run(
                dialect,
                '10 FOR I=1 TO 2\n'
                '20 FOR J=1 TO 2\n'
                '30 GOSUB 100\n'
                '40 NEXT J\n'
                '50 NEXT I\n'
                '60 PRINT "N=";N:END\n'
                '100 N=N+1:GOTO 300\n'
                '200 N=N+100\n'
                '300 GOTO 400\n'
                '400 RETURN\n',
            )
            self.assertEqual(err, '', msg=(dialect, err))
            self.assertEqual(out.replace(' ', '').strip(), 'N=4', msg=(dialect, out))

    def test_while_loop_survives_goto_in_subroutine(self):
        for dialect in ('mini', 'bbc'):
            out, err = _run(
                dialect,
                '10 I=0\n'
                '20 WHILE I<3\n'
                '30 GOSUB 100\n'
                '40 I=I+1\n'
                '50 ENDWHILE\n'
                '60 PRINT I:END\n'
                '100 GOTO 200\n'
                '200 RETURN\n',
            )
            self.assertEqual(err, '', msg=(dialect, err))
            self.assertEqual(out.strip(), '3', msg=dialect)

    def test_goto_leaving_a_loop_in_the_same_routine_still_ends_it(self):
        for dialect in ('mits', 'mini'):
            out, err = _run(
                dialect,
                '10 FOR I=1 TO 5\n'
                '20 IF I=3 THEN 60\n'
                '30 PRINT I;\n'
                '40 NEXT I\n'
                '60 PRINT "OUT":END\n',
            )
            self.assertEqual(err, '', msg=(dialect, err))
            self.assertEqual(out.replace(' ', '').strip(), '12OUT', msg=(dialect, out))

    def test_loop_opened_inside_the_subroutine_is_dropped_by_return(self):
        for dialect in ('mits', 'mini'):
            out, err = _run(
                dialect,
                '10 GOSUB 100\n'
                '20 FOR K=1 TO 2\n'
                '30 PRINT K;\n'
                '40 NEXT K\n'
                '50 PRINT "BACK":END\n'
                '100 FOR K=1 TO 3\n'
                '110 IF K=2 THEN 200\n'
                '120 NEXT K\n'
                '200 RETURN\n',
            )
            self.assertEqual(err, '', msg=(dialect, err))
            self.assertEqual(out.replace(' ', '').strip(), '12BACK', msg=(dialect, out))


if __name__ == '__main__':
    unittest.main()
