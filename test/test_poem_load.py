"""poem.txt and similar corpus files: leading bootstrap before numbered lines."""
from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stdout

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig  # noqa: E402

_POEM = os.path.join(_ROOT, 'test', 'corpus', 'bbcsdl', 'general', 'poem.txt')

pytestmark = [pytest.mark.phase0]


class PoemLoadTests(unittest.TestCase):
    def test_poem_txt_loads_with_bootstrap_line(self) -> None:
        if not os.path.isfile(_POEM):
            self.skipTest('poem.txt corpus missing')
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none'),
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.load(_POEM, announce=False)
        self.assertGreater(len(interp.program), 10)
        self.assertIn(0, interp.program)
        self.assertIn('ON ERROR', interp.program[0].upper())
        self.assertIn(10, interp.program)


if __name__ == '__main__':
    unittest.main()