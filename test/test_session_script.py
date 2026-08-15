"""Session scripts: INPUT.TXT style and stdin batch."""
from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic.runtime import (
    _looks_like_repl_command_script,
    _script_file_kind,
    main,
)

pytestmark = [pytest.mark.phase0]


class SessionScriptTests(unittest.TestCase):
    def test_sniff_input_txt_style(self):
        lines = [
            '10 A=38 : B=13\n',
            '20 PRINT A+B\n',
            'RUN\n',
            'Q\n',
            'DIR\n',
        ]
        self.assertTrue(_looks_like_repl_command_script(lines))

    def test_sniff_pure_numbered_is_program(self):
        lines = ['10 PRINT 1\n', '20 END\n']
        self.assertFalse(_looks_like_repl_command_script(lines))

    def test_main_runs_session_txt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'sess.txt')
            with open(path, 'w', encoding='utf-8') as f:
                f.write('10 A=38 : B=13\n20 PRINT A+B\nRUN\nQ\n')
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(['-q', path])
            self.assertEqual(code, 0)
            self.assertIn('51', buf.getvalue())
            self.assertIn('Goodbye!', buf.getvalue())

    def test_script_kind_dash_is_commands(self):
        self.assertEqual(_script_file_kind('-'), 'commands')

    def test_main_dash_c_immediate(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(['-q', '-c', 'PRINT 2+2', '-c', 'Q'])
        self.assertEqual(code, 0)
        self.assertIn('4', buf.getvalue())

    def test_main_dash_c_no_banner_without_quiet(self):
        """pip-from-GitHub smoke: -c PRINT 6*7 is just the answer."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(['-c', 'PRINT 6*7'])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn('42', out)
        self.assertNotIn('=== mini-BASIC ===', out)

    def test_main_dash_c_session_lines(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main([
                '-q',
                '-c', '10 A=38 : B=13',
                '-c', '20 PRINT A+B',
                '-c', 'RUN',
                '-c', 'Q',
            ])
        self.assertEqual(code, 0)
        self.assertIn('51', buf.getvalue())

    def test_main_dash_c_embedded_newlines(self):
        buf = io.StringIO()
        text = '10 A=1\n20 PRINT A+40\nRUN\nQ'
        with redirect_stdout(buf):
            code = main(['-q', '-c', text])
        self.assertEqual(code, 0)
        self.assertIn('41', buf.getvalue())


if __name__ == '__main__':
    unittest.main()
