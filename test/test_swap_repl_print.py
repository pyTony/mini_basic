"""Immediate SWAP and PRINT after a graphics RUN (terminal, not pygame)."""
from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


class SwapReplPrintTests(unittest.TestCase):
    def test_immediate_swap_then_print(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        out = io.StringIO()
        with redirect_stdout(out):
            interp.execute_immediate('A%=1:B%=2: SWAP A%,B%')
            interp.execute_immediate('PRINT A%')
            interp.execute_immediate('PRINT B%')
        text = out.getvalue()
        self.assertIn('2', text)
        self.assertIn('1', text)
        self.assertEqual(interp.int_variables.get('A'), 2)
        self.assertEqual(interp.int_variables.get('B'), 1)

    def test_immediate_print_does_not_reopen_pygame(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.config.display = 'pygame'
        interp._display_live = False
        interp._active_line_num = 0
        out = io.StringIO()
        with redirect_stdout(out):
            with patch.object(interp, '_ensure_display') as ensure:
                interp._print_program_text('2', newline=True)
                ensure.assert_not_called()
            interp._flush_program_output()
        self.assertIn('2', out.getvalue())

    def test_immediate_print_poll_false_does_not_exit_repl(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp._active_line_num = 0
        interp._display_live = True
        interp._display = type('D', (), {
            'write': lambda self, t: None,
            'newline': lambda self: None,
            'mark_dirty': lambda self: None,
            'poll': lambda self: False,
        })()
        with patch.object(interp, '_display_enabled', return_value=True):
            with patch.object(interp, '_display_write_vdu_string'):
                with patch.object(interp, '_invoke_on_close_and_exit') as die:
                    with patch.object(interp, '_mark_display_closed') as closed:
                        interp._print_program_text('1', newline=True)
        die.assert_not_called()
        closed.assert_called()


if __name__ == '__main__':
    unittest.main()
