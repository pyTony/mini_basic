"""INPUT must leave the next PRINT on a new line (not overwrite the typed text)."""
from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


class InputThenPrintTests(unittest.TestCase):
    def test_prompts_are_on_separate_lines(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(dialect='mits', display='none', display_locked=True)
        )
        interp.set_program_line(10, 'PRINT "HOW MANY PLAYERS";')
        interp.set_program_line(20, 'INPUT P')
        interp.set_program_line(30, 'PRINT "WHAT IS THE NAME OF PLAYER1";')
        interp.set_program_line(40, 'INPUT N$')
        interp.set_program_line(50, 'PRINT "OK"')
        interp.set_program_line(60, 'END')
        out = io.StringIO()
        with redirect_stdout(out), patch('builtins.input', side_effect=['2', 'Ann']):
            interp.run()
        text = out.getvalue()
        self.assertIn('HOW MANY PLAYERS', text)
        self.assertIn('WHAT IS THE NAME', text)
        self.assertIn('OK', text)
        self.assertNotIn('PLAYERS? WHAT IS THE NAME', text)
        self.assertNotIn('PLAYER1?OK', text.replace(' ', ''))

    def test_terminal_tab_input_commits_typed_text(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(dialect='mits', display='terminal', display_locked=True)
        )
        interp.set_program_line(10, 'PRINT TAB(0);"SEED";')
        interp.set_program_line(20, 'INPUT X')
        interp.set_program_line(30, 'PRINT "NEXT"')
        interp.set_program_line(40, 'END')
        out = io.StringIO()
        with redirect_stdout(out), patch('builtins.input', side_effect=['7']):
            interp.run()
        disp = interp._display
        if disp is not None and hasattr(disp, '_text'):
            rows = [''.join(cell[0] for cell in row) for row in disp._text]
            joined = '\n'.join(rows)
            self.assertIn('7', joined)
            self.assertIn('NEXT', joined)

    def test_string_prompt_presents_before_input_after_tab(self) -> None:
        """PRINT TAB then INPUT \"prompt\" must paint the prompt before blocking."""
        interp = BASICInterpreter(
            InterpreterConfig(dialect='mits', display='terminal', display_locked=True)
        )
        interp.set_program_line(10, 'PRINT TAB(26);"BACCARAT"')
        interp.set_program_line(20, 'INPUT "PRESS ENTER TO CONTINUE";Z$')
        interp.set_program_line(30, 'END')
        force_presents_before_input: list[int] = []

        def fake_input(_prompt: str = '') -> str:
            disp = interp._display
            self.assertIsNotNone(disp)
            rows = [''.join(cell[0] for cell in row) for row in disp._text]
            self.assertIn('PRESS ENTER TO CONTINUE', '\n'.join(rows))
            force_presents_before_input.append(present_spy.call_count)
            return ''

        interp._ensure_display()
        with patch.object(interp._display, 'present', wraps=interp._display.present) as present_spy:
            out = io.StringIO()
            with redirect_stdout(out), patch('builtins.input', side_effect=fake_input):
                interp.run()
        self.assertEqual(len(force_presents_before_input), 1)
        self.assertGreater(force_presents_before_input[0], 0)
        self.assertTrue(any(
            call.kwargs.get('force') for call in present_spy.call_args_list
        ))

    def test_streaming_input_does_not_reprint_reply(self) -> None:
        """stdin already echoed the reply; do not print it again on the next line."""
        interp = BASICInterpreter(
            InterpreterConfig(dialect='mits', display='terminal', display_locked=True)
        )
        interp.set_program_line(10, 'PRINT "HOW MANY PLAYERS";')
        interp.set_program_line(20, 'INPUT P')
        interp.set_program_line(30, 'PRINT "NEXT"')
        interp.set_program_line(40, 'END')
        out = io.StringIO()
        with redirect_stdout(out), patch('builtins.input', side_effect=['2']):
            interp.run()
        text = out.getvalue()
        self.assertNotIn('\n2\n', text.replace('\r', ''))
        self.assertNotRegex(text, r'\n2\s*\n')
        self.assertIn('HOW MANY PLAYERS', text)
        self.assertIn('NEXT', text)
        disp = interp._display
        rows = [''.join(cell[0] for cell in row) for row in disp._text]
        self.assertIn('2', '\n'.join(rows))


if __name__ == '__main__':
    unittest.main()
