"""mits / commodore / tiny: lines are uppercased at entry, as MS BASIC did.

Identifiers are case-insensitive in these dialects, so everything outside
string literals, REM / ' comments and DATA payloads is stored in uppercase.
"""
from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx, pytest.mark.timeout(15)]

MS_DIALECTS = ('mits', 'commodore', 'tiny')


def _interp(dialect: str, **config) -> BASICInterpreter:
    return BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True, **config)
    )


def _stored(dialect: str, text: str, **config) -> str:
    interp = _interp(dialect, **config)
    interp.set_program_line(10, text)
    return interp.program[10]


class MsEntryFoldTests(unittest.TestCase):

    def test_keywords_and_names_are_uppercased(self):
        for dialect in ('mits', 'commodore'):
            self.assertEqual(
                _stored(dialect, 'for i = 1 to 2 : print i; : next i'),
                'FOR I = 1 TO 2 : PRINT I; : NEXT I',
                msg=dialect,
            )

    def test_string_literals_keep_their_case(self):
        for dialect in MS_DIALECTS:
            self.assertEqual(
                _stored(dialect, 'print "Hello, World"; a$'),
                'PRINT "Hello, World"; A$',
                msg=dialect,
            )

    def test_rem_and_apostrophe_comments_keep_their_case(self):
        self.assertEqual(_stored('mits', 'rem Hello there'), 'REM Hello there')
        self.assertEqual(
            _stored('mits', 'x = 1 : rem Set x'), 'X = 1 : REM Set x',
        )
        self.assertEqual(_stored('mits', "x = 1 ' Note"), "X = 1 ' Note")

    def test_data_payload_keeps_case_until_colon(self):
        self.assertEqual(
            _stored('mits', 'data abc, "Def" : read a$'),
            'DATA abc, "Def" : READ A$',
        )

    def test_fold_is_idempotent(self):
        once = _stored('mits', 'if a$ = "x" then print "Yes" else rem No')
        interp = _interp('mits')
        self.assertEqual(interp.canonicalize_program_line(once), once)

    def test_case_sensitive_override_keeps_names(self):
        stored = _stored('mits', 'abc = 1 : print abc', identifiers_case_sensitive=True)
        self.assertIn('abc', stored)

    def test_bbc_is_not_folded(self):
        self.assertEqual(_stored('bbc', 'print x'), 'print x')

    def test_lowercase_program_runs(self):
        for dialect in MS_DIALECTS:
            interp = _interp(dialect)
            interp.set_program_line(10, 'let a = 2')
            interp.set_program_line(20, 'print a * 3')
            interp.set_program_line(30, 'data hello')
            interp.set_program_line(40, 'read b$ : print b$') if dialect != 'tiny' else None
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                interp.run()
            lines = out.getvalue().split()
            self.assertEqual(lines[0], '6', msg=(dialect, err.getvalue()))
            if dialect != 'tiny':
                self.assertEqual(lines[1], 'hello', msg=(dialect, err.getvalue()))


class EntryRewritesSkipCommentsTests(unittest.TestCase):
    """Entry canonicalize must not rewrite comment text (LIST / SAVE show it)."""

    CASES = {
        'mini': (
            ('X = 1 : REM Note Tanx', 'X = 1 : REM Note Tanx'),
            ("X = 1 ' NOTE Tanx", "X = 1 ' NOTE Tanx"),
            ('PRINT "a" : REM NOTE', 'PRINT "a" : REM NOTE'),
            ('FOR I=1TO3 : REM x1TOy', 'FOR I=1 TO 3 : REM x1TOy'),
            ('REM A $ CIRCLEFILL', 'REM A $ CIRCLEFILL'),
            ("' A $ b", "' A $ b"),
        ),
        'bbc': (
            ('X=1:REM Note Tanx', 'X=1:REM Note Tanx'),
            ('X=1:REMNOTE', 'X=1:REMNOTE'),
            ('IF X THEN REM NOTE', 'IF X THEN REM NOTE'),
        ),
        'mits': (
            ('x = 1 : rem Note Tanx', 'X = 1 : REM Note Tanx'),
            ("x = 1 ' Note", "X = 1 ' Note"),
        ),
    }

    def test_comment_text_is_stored_verbatim(self):
        for dialect, cases in self.CASES.items():
            for text, expected in cases:
                self.assertEqual(_stored(dialect, text), expected, msg=(dialect, text))


if __name__ == '__main__':
    unittest.main()
