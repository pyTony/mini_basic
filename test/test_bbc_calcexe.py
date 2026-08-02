"""Tests for BBC Sprow program support (CalcEXE and related features)."""
import io
import os
import sys
import unittest
from unittest.mock import patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic.bbc_detokenize import bbc_binary_to_source, detokenize_line_body
from mini_basic.config import InterpreterConfig
from mini_basic.runtime import BASICInterpreter
from mini_basic.type_system import ChainTransfer


class BBCCalcEXEFeatureTests(unittest.TestCase):
    def test_hex_literal_and_at_percent(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none'))
        self.assertEqual(interp.eval_expr('&90A'), 2314.0)
        interp.execute_immediate('@%=&90A')
        self.assertEqual(interp.bbc_at_percent, 2314)
        self.assertEqual(interp.print_field_width, 10)

    def test_chain_keyword_spacing(self):
        body = bytes([0xD7]) + b'"CALCEXT"' + bytes([0x0D])
        self.assertEqual(detokenize_line_body(body), 'CHAIN "CALCEXT"')

    def test_star_command_no_error(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none'))
        buf = io.StringIO()
        with patch.object(sys, 'stdout', buf):
            interp.execute_immediate('*FX4,1')
            interp.execute_immediate('*TV254')
        self.assertEqual(buf.getvalue(), '')

    def test_chain_loads_extension(self):
        base = os.path.join(os.path.expanduser('~'), 'Downloads', 'calcexe')
        main = os.path.join(base, 'CalcEXE')
        ext = os.path.join(base, 'CalcEXT')
        if not os.path.isfile(main) or not os.path.isfile(ext):
            self.skipTest('CalcEXE/CalcEXT not installed')
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none'))
        interp.working_dir = base
        interp.load(main, announce=False)
        before = len(interp.program)
        self.assertGreater(before, 100)
        with patch.object(interp, '_read_get_char', return_value=32):
            with self.assertRaises(ChainTransfer):
                interp.execute_immediate('CHAIN "CalcEXT"')
        self.assertNotEqual(len(interp.program), before)

    def test_calcexe_loads_procedures(self):
        path = os.path.join(os.path.expanduser('~'), 'Downloads', 'calcexe', 'CalcEXE')
        if not os.path.isfile(path):
            self.skipTest('CalcEXE not installed')
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none'))
        interp.working_dir = os.path.dirname(path)
        interp.load(path, announce=False)
        interp._prepare_run()
        self.assertIn('screen', interp.user_procedures)
        self.assertIn('err', interp.user_procedures)

    def test_calcexe_startup_to_repeat(self):
        path = os.path.join(os.path.expanduser('~'), 'Downloads', 'calcexe', 'CalcEXE')
        if not os.path.isfile(path):
            self.skipTest('CalcEXE not installed')
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none'))
        interp.working_dir = os.path.dirname(path)
        interp.load(path, announce=False)
        interp._reset_run_state()
        interp._prepare_run()
        line_nums = interp._run_line_nums
        buf = io.StringIO()
        with patch.object(sys, 'stdout', buf), patch.object(interp, '_read_get_char', return_value=32):
            start = line_nums.index(140)
            for i in range(start, line_nums.index(170) + 1):
                ln = line_nums[i]
                interp.execute_line(ln, interp.program[ln], line_nums)
        out = buf.getvalue()
        self.assertIn('Ready', out)


if __name__ == '__main__':
    unittest.main()