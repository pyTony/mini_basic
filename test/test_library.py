"""LIBRARY / INSTALL — load another file's DEF PROC/FN into this program."""
from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig  # noqa: E402

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]

_LIBRARY_SOURCE = """\
10 REM a tiny library: only definitions, no top-level code
20 DEF PROCgreet(who$)
30 PRINT "Hello, " + who$
40 ENDPROC
50 DEF FNdouble(n)
60 =n*2
"""


class LibraryStatementTests(unittest.TestCase):
    def _run_with_library(self, main_source: str, dialect: str = 'bbc') -> str:
        with tempfile.TemporaryDirectory() as tmp:
            lib_path = os.path.join(tmp, 'teklib.bas')
            with open(lib_path, 'w', encoding='utf-8') as f:
                f.write(_LIBRARY_SOURCE)
            main_path = os.path.join(tmp, 'main.bas')
            with open(main_path, 'w', encoding='utf-8') as f:
                f.write(main_source)
            interp = BASICInterpreter(
                InterpreterConfig(
                    dialect=dialect,
                    display='none',
                    display_locked=True,
                ),
            )
            interp.working_dir = tmp
            self.assertTrue(interp.load(main_path, announce=False))
            buf = io.StringIO()
            err = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(err):
                interp.run()
            return buf.getvalue() + err.getvalue()

    def test_library_merges_proc_and_fn(self) -> None:
        out = self._run_with_library(
            '10 LIBRARY "teklib"\n'
            '20 PROCgreet("Tony")\n'
            '30 PRINT FNdouble(21)\n'
        )
        self.assertNotIn('?', out)
        self.assertIn('Hello, Tony', out)
        self.assertIn('42', out)

    def test_install_is_alias_for_library(self) -> None:
        out = self._run_with_library(
            '10 INSTALL "teklib"\n'
            '20 PROCgreet("World")\n'
        )
        self.assertNotIn('?', out)
        self.assertIn('Hello, World', out)

    def test_library_does_not_run_top_level_library_code(self) -> None:
        # The library's own top-level REM/code never executes — only its
        # DEF PROC/FN become callable. Calling an undefined PROC from the
        # library's top level should NOT have produced any extra output.
        out = self._run_with_library(
            '10 LIBRARY "teklib"\n'
            '20 PRINT "done"\n'
        )
        self.assertEqual(out.strip(), 'done')

    def test_library_missing_file_reports_error(self) -> None:
        out = self._run_with_library('10 LIBRARY "no_such_library"\n')
        self.assertIn('? LIBRARY error: file not found', out)


if __name__ == '__main__':
    unittest.main()
