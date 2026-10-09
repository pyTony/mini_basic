"""DIM memory guardrails."""
from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0]


class DimMemoryTests(unittest.TestCase):
    def test_himem_string_dim_within_bbc_budget(self):
        lines = [
            (10, 'MAX=(HIMEM-LOMEM)/40'),
            (20, 'DIM A$(MAX)'),
            (30, 'PRINT MAX'),
            (40, 'END'),
        ]
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        for line_num, statement in lines:
            interp.program[line_num] = statement
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.run()
        self.assertEqual(buf.getvalue().strip(), '10000')

    def test_oversized_dim_reports_out_of_memory(self):
        lines = [
            (10, 'DIM A(200000)'),
            (20, 'END'),
        ]
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        for line_num, statement in lines:
            interp.program[line_num] = statement
        errors: list[str] = []

        def track(msg, *a, **k):
            errors.append(str(msg))

        with patch.object(interp, '_runtime_error', track):
            interp.run()
        self.assertTrue(any('Out of memory' in item for item in errors))


if __name__ == '__main__':
    unittest.main()