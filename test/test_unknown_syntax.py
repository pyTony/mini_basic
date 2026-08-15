"""Unknown / unimplemented BASIC command and syntax error handling."""
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


class UnknownSyntaxTests(unittest.TestCase):
    def _imm(self, cmd: str, *, dialect: str = 'bbc') -> str:
        interp = BASICInterpreter(
            InterpreterConfig(
                dialect=dialect,
                display='none',
                display_locked=True,
            ),
        )
        buf = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(err):
            interp.execute_immediate(cmd)
        return buf.getvalue() + err.getvalue()

    def _run(self, lines, *, dialect: str = 'bbc', strict: bool = False) -> str:
        interp = BASICInterpreter(
            InterpreterConfig(
                dialect=dialect,
                display='none',
                display_locked=True,
                strict_dialect=strict,
            ),
        )
        for ln, stmt in lines:
            interp.set_program_line(ln, stmt)
        buf = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(err):
            interp.run()
        return buf.getvalue() + err.getvalue()

    def test_unknown_statement_continues(self) -> None:
        out = self._run([(10, 'PRINT 1'), (20, 'FOO 42'), (30, 'PRINT 2')])
        self.assertIn('? Unknown statement: FOO', out)
        self.assertIn('at line 20', out.lower())
        self.assertIn('1', out)
        self.assertIn('2', out)

    def test_unknown_statement_includes_line_location(self) -> None:
        out = self._run([(10, 'FOO 1')])
        self.assertIn('? Unknown statement: FOO', out)
        self.assertIn('at line 10', out.lower())

    def test_on_error_traps_unknown(self) -> None:
        out = self._run(
            [
                (5, 'ON ERROR GOTO 100'),
                (10, 'FOO'),
                (20, 'PRINT "after"'),
                (100, 'PRINT "trapped"'),
                (110, 'END'),
            ],
        )
        self.assertNotIn('after', out)
        self.assertIn('trapped', out)

    def test_unimplemented_bbc_commands_are_specific(self) -> None:
        # Test informativeness of error messages for (some) unimplemented.
        # Platform-bound commands (OS, machine lang like CALL/USR/SYS/INSTALL) are documented in
        # runtime.py _UNIMPLEMENTED_COMMANDS and should error with ? Unimplemented: (no silent fail).
        # We prioritize non-platform for Phase-1 core tests; see comments in runtime.py.
        # These tests cover error reporting corner cases.
        cases = {
            'SYS "OS_Write0", "hi"': 'SYS (RISC OS / OS call)',
            'CALL &FFFD': 'CALL (machine-code subroutine)',
            'USR &FFFD': 'USR (machine-code function)',
        }
        for stmt, detail in cases.items():
            with self.subTest(stmt=stmt):
                out = self._imm(stmt)
                self.assertIn('? Unimplemented:', out, out)
                self.assertIn(detail, out, out)

    def test_unknown_fn_reports_name(self) -> None:
        out = self._imm('PRINT FNmissing(1)')
        self.assertIn('? FN error: FNmissing not defined', out)

    def test_unknown_builtin_in_print_reports_error(self) -> None:
        out = self._imm('PRINT ZZZ(1)')
        # Informative error for unknown func (no function XXX), includes location in immediate.
        # We map Python NameError etc. to consistent message. See _expression_error_detail.
        self.assertIn('? Expression error: no function ZZZ', out)
        # The preview in location may include the expr, that's ok for informativeness.
        self.assertIn('in immediate', out)

    def test_incomplete_print_expression_reports_error(self) -> None:
        out = self._imm('PRINT 1+')
        self.assertIn('? Expression error:', out)
        self.assertTrue(
            'incomplete expression' in out or 'invalid syntax' in out,
            out,
        )

    def test_bad_assignment_reports_syntax_error(self) -> None:
        out = self._imm('A = = 1')
        self.assertIn('? Syntax error: bad expression `= 1`', out)

    def test_dialect_strict_blocks_while_at_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'bad.bas')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('10 WHILE 1\n20 WEND\n30 END\n')
            interp = BASICInterpreter(
                InterpreterConfig(dialect='mits', strict_dialect=True),
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.load(path)
            self.assertEqual(len(interp.program), 0)
            self.assertIn('WHILE not allowed', buf.getvalue())

    def test_dialect_non_strict_warns_on_dialect_change(self) -> None:
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc'))
        interp.program[10] = 'WHILE I% < 3'
        interp.program[20] = 'WEND'
        interp._program_source_numbered = False
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertTrue(interp.set_dialect('mits'))
        self.assertIn('Warning:', buf.getvalue())

    def test_end_def_gives_hint(self) -> None:
        out = self._run([(10, 'END DEF')])
        self.assertIn('END DEF closes DEF FN', out)

    def test_local_outside_proc_errors(self) -> None:
        out = self._imm('LOCAL A')
        self.assertIn('? LOCAL error', out)

    # Expanded Phase-1 coverage for error message informativeness and corner cases
    def test_incomplete_expr_error(self) -> None:
        out = self._imm('PRINT 1+')
        self.assertIn('? Expression error:', out)
        self.assertTrue('incomplete' in out or 'invalid syntax' in out, out)

    def test_unset_numeric_prints_zero(self) -> None:
        out = self._imm('PRINT FOO')
        self.assertIn('0', out)
        self.assertNotIn('? Expression error:', out)

    def test_install_is_silent_stub(self) -> None:
        out = self._imm('INSTALL "lib"')
        self.assertNotIn('?', out)


if __name__ == '__main__':
    unittest.main()