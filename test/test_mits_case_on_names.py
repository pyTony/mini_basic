"""mits with ``case: on``: lowercase / camelCase names are not crunched keywords.

``printDistance:`` was rewritten to ``print Distance:`` (a keyword glued to a
name, as old MS listings write PRINTA) and so never became a label. With
case-sensitive identifiers only the uppercase keyword is split; case-insensitive
mits still splits PRINTA / IFA=0THEN50 as before.
"""
from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx, pytest.mark.timeout(15)]


def _interp(case_sensitive):
    return BASICInterpreter(InterpreterConfig(
        dialect='mits', display='none', display_locked=True,
        identifiers_case_sensitive=case_sensitive,
    ))


def _stored(case_sensitive, text):
    interp = _interp(case_sensitive)
    interp.set_program_line(10, text)
    return interp.program[10]


class CaseOnNamesTests(unittest.TestCase):

    def test_keyword_prefixed_names_are_left_alone(self):
        for text in (
            'printDistance: PRINT "X"',
            'readCommand: INPUT "C";a$',
            'nextWarpStep: NEXT stepIndex',
            'endProgram: END',
            'clearTable: CLEAR',
            'ifReady = 1',
            'forecast = 2',
        ):
            self.assertEqual(_stored(True, text), text, msg=text)

    def test_uppercase_crunch_still_splits_with_case_on(self):
        self.assertEqual(_stored(True, 'FORI=1TO3'), 'FOR I=1 TO 3')
        self.assertEqual(_stored(True, 'IFA=0THEN50'), 'IF A=0 THEN 50')
        self.assertEqual(_stored(True, 'PRINTA'), 'PRINT A')

    def test_case_insensitive_mits_still_crunches(self):
        self.assertEqual(_stored(False, 'printa'), 'PRINT A')
        self.assertEqual(_stored(False, 'ifa=0then50'), 'IF A=0 THEN 50')

    def test_labels_with_keyword_prefixes_work(self):
        interp = _interp(True)
        for num, text in (
            (10, 'GOTO printHeader'),
            (20, 'PRINT "SKIPPED"'),
            (30, 'printHeader: PRINT "HEADER"'),
            (40, 'GOSUB readCommand'),
            (50, 'GOTO endProgram'),
            (60, 'readCommand: PRINT "READ":RETURN'),
            (70, 'endProgram: PRINT "END":END'),
        ):
            interp.set_program_line(num, text)
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            interp.run()
        self.assertEqual(err.getvalue(), '')
        self.assertEqual(out.getvalue().split(), ['HEADER', 'READ', 'END'])


if __name__ == '__main__':
    unittest.main()
