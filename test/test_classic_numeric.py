"""Classic numeric behaviour that 1.00 claims for every dialect."""
from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


def _run(dialect: str, lines: list[str]) -> tuple[str, int]:
    interp = BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )
    for i, line in enumerate(lines, 1):
        interp.set_program_line(i * 10, line)
    buf = io.StringIO()
    with redirect_stdout(buf):
        interp.run()
    return buf.getvalue(), int(getattr(interp, 'error_line_num', 0) or 0)


class ClassicNumericTests(unittest.TestCase):
    def test_unset_numeric_is_zero(self):
        for dialect in ('mini', 'bbc', 'mits'):
            out, err = _run(dialect, ['N=N+1', 'PRINT N', 'END'])
            self.assertEqual(err, 0, msg=dialect)
            self.assertIn('1', out, msg=dialect)

    def test_int_percent_multiply(self):
        for dialect in ('mini', 'bbc', 'mits'):
            out, err = _run(
                dialect,
                ['A%=7', 'B%=3', 'C%=A%*B%', 'PRINT C%', 'END'],
            )
            self.assertEqual(err, 0, msg=dialect)
            self.assertIn('21', out, msg=dialect)
