"""Runs the BASIC programs under test/programs/ through the interpreter and
checks their output against an inline convention, one test per file.

Each file in test/programs/ is a plain, portable BASIC program (no
mini_basic-only syntax by default) so it can also be loaded unmodified into
a real reference implementation (BBCSDL / BB4W) for cross-checking, not
just run here. All directives below are ordinary REM comments, so a real
BASIC tokenizer ignores them exactly like mini_basic does:

  REM DIALECT: bbc|mini        (optional; default bbc)
  REM EXPECT: <one line>       (repeatable; joined with \n for multi-line
                                 expected stdout)
  REM XFAIL: <reason>          (optional; if present, a mismatch is
                                 reported as an expected failure instead of
                                 a hard failure -- the feature isn't done
                                 in mini_basic yet, even though a real BBC
                                 BASIC handles it)

Adding a new .bas/.bbc file to test/programs/ automatically gets a test;
no registration needed.
"""
from __future__ import annotations

import glob
import io
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx, pytest.mark.timeout(15)]

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROGRAMS_DIR = os.path.join(_ROOT, 'test', 'programs')


def _discover_programs():
    if not os.path.isdir(_PROGRAMS_DIR):
        return []
    paths = sorted(
        glob.glob(os.path.join(_PROGRAMS_DIR, '*.bas'))
        + glob.glob(os.path.join(_PROGRAMS_DIR, '*.bbc'))
    )
    return paths


def _parse_directives(path):
    dialect = 'bbc'
    expect_lines = []
    xfail_reason = None
    with open(path, encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            upper = line.upper()
            if upper.startswith('REM DIALECT:'):
                dialect = line.split(':', 1)[1].strip().lower()
            elif upper.startswith('REM EXPECT:'):
                expect_lines.append(line.split(':', 1)[1].strip())
            elif upper.startswith('REM XFAIL:'):
                xfail_reason = line.split(':', 1)[1].strip()
    return dialect, '\n'.join(expect_lines), xfail_reason


def _run_program(path, dialect):
    interp = BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )
    interp.load(path, announce=False)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        interp.run()
    return out.getvalue().strip(), err.getvalue()


class ProgramsCorpusTests(unittest.TestCase):
    """One generated test method per file in test/programs/ (see below)."""


def _make_test(path):
    def test(self):
        dialect, expected, xfail_reason = _parse_directives(path)
        self.assertTrue(expected, f'{path} has no REM EXPECT: line(s)')
        actual, err = _run_program(path, dialect)
        ok = actual == expected and not err
        if xfail_reason and not ok:
            pytest.xfail(f'{xfail_reason} (got {actual!r}, err={err!r})')
        self.assertEqual(actual, expected, msg=err)
        self.assertEqual(err, '')

    return test


for _path in _discover_programs():
    _name = 'test_' + os.path.splitext(os.path.basename(_path))[0]
    setattr(ProgramsCorpusTests, _name, _make_test(_path))


if __name__ == '__main__':
    unittest.main()
