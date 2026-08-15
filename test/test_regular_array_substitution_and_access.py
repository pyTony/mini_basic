"""1D/2D array DIM, assign, and expression access."""
from __future__ import annotations

import unittest

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


class RegularArraySubstitutionTests(unittest.TestCase):
    def test_regular_array_substitution_and_access(self):
        interp = BASICInterpreter(
            InterpreterConfig(display='none', display_locked=True)
        )
        interp.set_program_line(10, 'DIM A(5)')
        interp.set_program_line(20, 'DIM B%(2,2)')
        interp.set_program_line(30, 'A(1) = 42')
        interp.set_program_line(40, 'B%(1,2) = 100')
        interp.set_program_line(50, 'PRINT A(1)')
        interp.set_program_line(60, 'PRINT B%(1,2)')
        interp.set_program_line(70, 'END')
        interp.run()
        self.assertEqual(float(interp.eval_expr('A(1)')), 42.0)
        self.assertEqual(int(interp.eval_expr('B%(1,2)')), 100)
