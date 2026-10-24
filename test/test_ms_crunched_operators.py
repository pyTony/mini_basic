"""mits / commodore: AND / OR / XOR glued between operands (crunched listings).

Old MS BASIC listings drop every space: ``IFQ1<1ORQ1>8ORQ2<1ORQ2>8THEN1600``,
``IFS<N-EORD(7)<0THEN1990`` (that is ``N-E OR D(7)``). The real tokenizer finds
the keyword anywhere; we split only in unambiguous spots (after a number or
``)``, or between two classic short names) and never inside ordinary
identifiers such as SCORE, RESTORE or ORDER.
"""
from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx, pytest.mark.timeout(15)]

MS = ('mits', 'commodore')


def _interp(dialect: str) -> BASICInterpreter:
    return BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )


def _stored(dialect: str, text: str) -> str:
    interp = _interp(dialect)
    interp.set_program_line(10, text)
    return interp.program[10]


def _run(dialect: str, src: str) -> tuple[str, str]:
    interp = _interp(dialect)
    for raw in src.strip().splitlines():
        num, _, text = raw.partition(' ')
        interp.set_program_line(int(num), text)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        interp.run()
    return out.getvalue(), err.getvalue()


class CrunchedLogicOperatorTests(unittest.TestCase):

    def test_number_then_operator_then_name(self):
        for dialect in MS:
            for q1, q2, expect in ((3, 9, 'OUT'), (0, 4, 'OUT'), (9, 4, 'OUT'), (3, 4, 'IN')):
                out, err = _run(
                    dialect,
                    f'10 Q1={q1}:Q2={q2}\n'
                    '20 IFQ1<1ORQ1>8ORQ2<1ORQ2>8THEN60\n'
                    '30 PRINT"IN":END\n'
                    '60 PRINT"OUT"\n',
                )
                self.assertEqual(out.strip(), expect, msg=(dialect, q1, q2, err))

    def test_and_after_number(self):
        for dialect in MS:
            out, err = _run(
                dialect,
                '10 C1=3\n20 IFC1>=1ANDC1<9THEN50\n30 PRINT"NO":END\n50 PRINT"YES"\n',
            )
            self.assertEqual(out.strip(), 'YES', msg=(dialect, err))

    def test_two_short_names_with_or_between(self):
        for dialect in MS:
            self.assertIn('N-E OR D(7)<0', _stored(dialect, 'IFS<N-EORD(7)<0THEN1990'))
            for s, d7, expect in ((1, 1, 'T'), (5, -1, 'T'), (5, 1, 'F')):
                out, err = _run(
                    dialect,
                    f'10 DIM D(8):S={s}:N=5:E=3:D(7)={d7}\n'
                    '20 IFS<N-EORD(7)<0THEN50\n30 PRINT"F":END\n50 PRINT"T"\n',
                )
                self.assertEqual(out.strip(), expect, msg=(dialect, s, d7, err))

    def test_close_paren_then_operator(self):
        for dialect in MS:
            self.assertIn(') OR Q', _stored(dialect, 'IF(A>1)ORQ=2THEN9'))
            out, err = _run(
                dialect,
                '10 A=3:Q=2\n20 IF(A>1)AND(Q=2)THEN50\n30 PRINT"NO":END\n50 PRINT"YES"\n',
            )
            self.assertEqual(out.strip(), 'YES', msg=(dialect, err))

    def test_ordinary_names_are_not_split(self):
        for dialect in MS:
            out, err = _run(
                dialect,
                '10 SCORE=3:ORDER=4:ERRORS=5\n'
                '20 PRINT SCORE;ORDER;ERRORS\n'
                '30 RESTORE:READ A:PRINT A\n'
                '40 FORI=1TO2:PRINTI;:NEXTI\n'
                '50 DATA 7\n',
            )
            self.assertEqual(err, '', msg=(dialect, err))
            self.assertEqual(
                out.split(), ['3', '4', '5', '7', '1', '2'], msg=(dialect, out),
            )

    def test_strings_comments_and_data_untouched(self):
        for dialect in MS:
            for text in (
                'PRINT"1ORQ1 AND)ORX"',
                'REM IF Q1<1ORQ1>8',
                'DATA 1ORQ1,2',
            ):
                self.assertEqual(_stored(dialect, text), text, msg=(dialect, text))

    def test_idempotent(self):
        interp = _interp('mits')
        once = interp.canonicalize_program_line('IFQ1<1ORQ1>8ORQ2<1ORQ2>8THEN1600')
        self.assertEqual(interp.canonicalize_program_line(once), once)

    def test_other_dialects_untouched(self):
        for dialect in ('mini', 'bbc', 'tiny'):
            self.assertNotIn(' OR ', _stored(dialect, 'X=Q1<1ORQ1'), msg=dialect)


if __name__ == '__main__':
    unittest.main()
