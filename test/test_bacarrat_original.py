"""Stock bacarrat.bas must load unchanged (no listing patches)."""
from __future__ import annotations

import os
import unittest

from mini_basic import BASICInterpreter, InterpreterConfig

_BAS = os.path.join(os.path.dirname(__file__), '..', 'basics', 'bacarrat.bas')


class BacarratOriginalTests(unittest.TestCase):
    def test_listing_is_stock(self) -> None:
        text = open(_BAS, encoding='utf-8').read()
        self.assertIn('T2=B(3)=B(4)', text)
        self.assertIn('RANDOMIZE X', text)
        self.assertNotIn('RND(-TIME)', text)
        self.assertNotIn('REM dialect:', text)

    def test_load_ok(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(display='none', display_locked=True)
        )
        self.assertTrue(interp.load(_BAS, announce=False))
        self.assertIn(700, interp.program)
        self.assertIn('B(3)=B(4)', interp.program[700].replace(' ', ''))
