"""``AND (`` / ``OR (`` in a compiled condition is an operator, not an array read.

Mandelbrot ``WHILE (I% < M%) AND (ZX*ZX+ZY*ZY < 4)`` was flagged as an array
expression and fell back to the slow text evaluator on every iteration.
"""
from __future__ import annotations

import unittest

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx, pytest.mark.timeout(15)]

CONDITIONS = (
    'CONT AND (I% < MAXITER%)',
    '(I% < MAXITER%) AND (ZX * ZX + ZY * ZY < 4)',
    '(A% > 1) OR (B% > 1)',
    'NOT (A% > 1)',
    '(A% EOR (B%))',
)


def _interp(dialect: str) -> BASICInterpreter:
    return BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )


class OperatorParenIsNotArrayTests(unittest.TestCase):

    def test_conditions_stay_compiled(self):
        for dialect in ('bbc', 'mini'):
            interp = _interp(dialect)
            for cond in CONDITIONS:
                compiled = interp._get_compiled_expr(cond, is_condition=True)
                self.assertFalse(compiled.use_fallback, msg=(dialect, cond))
                self.assertFalse(compiled.has_array, msg=(dialect, cond))


if __name__ == '__main__':
    unittest.main()
