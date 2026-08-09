import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

from mini_basic.format.save_case import format_program_line
from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0]


class SaveCaseFormatTests(unittest.TestCase):
    def test_upper_folds_keywords_and_identifiers(self):
        line = format_program_line('let n = 1: print "HeLLo"; n', 'upper')
        self.assertEqual(line, 'LET N = 1: PRINT "HeLLo"; N')

    def test_lower_folds_keywords_and_identifiers(self):
        line = format_program_line('DEF FNfact(n)=n*FNfact(n-1)', 'lower')
        self.assertIn('def fnfact', line)
        self.assertIn('fnfact', line)

    def test_rem_comment_is_preserved(self):
        original = 'rem Keep This Mixed CASE in comment'
        self.assertEqual(format_program_line(original, 'upper'), original)
        self.assertEqual(format_program_line(original, 'lower'), original)

    def test_apostrophe_comment_is_preserved(self):
        original = "' Do not touch this String"
        self.assertEqual(format_program_line(original, 'upper'), original)

    def test_string_literals_are_preserved(self):
        line = format_program_line('PRINT "MiXeD"; n', 'upper')
        self.assertEqual(line, 'PRINT "MiXeD"; N')


class SaveCaseIntegrationTests(unittest.TestCase):
    def test_save_upper_in_bbc_dialect(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        interp.program[10] = 'let count = 3: rem keep Note'
        interp.program[20] = 'print count, "Ok"'
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'fold.bas')
            interp.save(path)
            with open(path, encoding='utf-8') as handle:
                text = handle.read()
        self.assertIn('LET COUNT = 3: rem keep Note', text)
        self.assertIn('PRINT COUNT,"Ok"', text)

    @pytest.mark.mits
    def test_save_lower_when_save_case_is_one(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mits'))
        interp.save_case = 1
        interp.program[10] = 'LET N = 5'
        interp.program[20] = 'PRINT FNfact(N)'
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'lower.bas')
            interp.save(path)
            with open(path, encoding='utf-8') as handle:
                text = handle.read()
        self.assertIn('let n = 5', text)
        self.assertIn('print fnfact(n)', text.lower())

    def test_save_case_ignored_in_mini_dialect(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
        interp.save_case = 0
        interp.program[10] = 'let Count = 1'
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'mini.bas')
            interp.save(path)
            with open(path, encoding='utf-8') as handle:
                text = handle.read()
        self.assertIn('LET Count = 1', text)

    def test_save_case_system_variable(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        interp.execute_immediate('_save_case = 1')
        self.assertEqual(interp.save_case, 1)

    def test_list_detokenizes_upper_in_bbc_dialect(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        interp.program[10] = 'let count = 3: rem keep Note'
        interp.program[20] = 'print count, "Ok"'
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program()
        out = buf.getvalue()
        self.assertIn('LET COUNT = 3: rem keep Note', out)
        self.assertIn('PRINT COUNT,"Ok"', out)

    @pytest.mark.mits
    def test_list_detokenizes_lower_when_save_case_is_one(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mits'))
        interp.save_case = 1
        interp.program[10] = 'LET N = 5'
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program()
        self.assertIn('let n = 5', buf.getvalue().lower())

    def test_list_preserves_mixed_case_in_mini_dialect(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
        interp.program[10] = 'let Count = 1'
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program()
        self.assertIn('LET Count = 1', buf.getvalue())

    def test_list_matches_save_text_in_bbc_dialect(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        interp.program[10] = 'let n=2: rem X'
        interp.program[20] = 'print n'
        list_buf = io.StringIO()
        with redirect_stdout(list_buf):
            interp.list_program()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'same.bas')
            interp.save(path)
            with open(path, encoding='utf-8') as handle:
                saved = handle.read()
        self.assertIn('LET N = 2: rem X', list_buf.getvalue())
        self.assertIn('10 LET N = 2: rem X', saved)
        self.assertIn('20 PRINT N', saved)

    # Expanded for Phase-1 corner cases (after making save_case pass for BBC)
    def test_bbc_save_list_preserves_string_case_but_folds_idents(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        interp.program[10] = 'print "MiXeD"; n'
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.list_program()
        out = buf.getvalue()
        self.assertIn('PRINT "MiXeD"; N', out)  # ident folded, string preserved

    def test_bbc_array_save_folds(self):
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        interp.program[10] = 'dim a(2): a(0)=1: print a(0)'
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'arr.bas')
            interp.save(path)
            with open(path, encoding='utf-8') as handle:
                text = handle.read()
        self.assertIn('DIM A(2)', text)
        self.assertIn('PRINT A(0)', text)


if __name__ == '__main__':
    unittest.main()