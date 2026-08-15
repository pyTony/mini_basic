"""Short regressions for animal-style PRINT / INPUT / FNstrip — no full listing."""
from __future__ import annotations

import io
import os
import sys
import unittest
from unittest import mock

import pytest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig
from test.animal_snippets import FNSTRIP_LINES, bbc_none, load_lines

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


def _letters_on_row(display, row: int) -> list[tuple[int, str]]:
    return [
        (col, cell[0])
        for col, cell in enumerate(display._text[row])
        if cell[0] != ' '
    ]


class AnimalTextPrintTests(unittest.TestCase):
    def test_trailing_apostrophe_string_print(self) -> None:
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        content, suppress = interp._strip_bbc_print_newline_suffix(
            '"Creative Computing"\'\'',
        )
        self.assertTrue(suppress)
        text, _, _ = interp._render_print_content(content, ';', 0)
        self.assertEqual(text, 'Creative Computing')

    @pytest.mark.graphics
    def test_animal_header_columns_are_consecutive(self) -> None:
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='pygame'))
        lines = {
            3: 'CLS:@%=&90A:WIDTH 0:PRINT TAB(15)"ANIMAL"',
            4: 'PRINT "Creative Computing Morristown New Jersey"\'\'',
            5: 'PRINT "Play \'Guess the Animal\'"',
        }
        for ln, stmt in lines.items():
            interp.program[ln] = stmt
        interp.line_nums = sorted(interp.program.keys())
        interp._prepare_run()
        for ln in interp.line_nums:
            interp.execute_line(ln, interp.program[ln], interp.line_nums)
            interp._flush_display(force=True)
        display = interp._display
        assert display is not None
        self.assertEqual(display.text_cols, 80)
        animal_cols = [col for col, _ in _letters_on_row(display, 0)]
        self.assertEqual(animal_cols, list(range(14, 20)))
        title_letters = _letters_on_row(display, 1)
        self.assertEqual(''.join(ch for _, ch in title_letters[:8]), 'Creative')
        self.assertEqual([c for c, _ in title_letters[:8]], list(range(0, 8)))
        play_letters = _letters_on_row(display, 2)
        self.assertIn('Play', ''.join(ch for _, ch in play_letters))
        gaps = [b - a for a, b in zip(animal_cols, animal_cols[1:])]
        self.assertTrue(all(gap == 1 for gap in gaps))
        cell_w = display._effective_cell_width()
        if display._font is not None:
            self.assertLessEqual(display._font.size('M')[0], cell_w + 1)
        else:
            self.assertLessEqual(8, cell_w + 1)

    def test_input_syncs_print_column_before_following_print(self) -> None:
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        interp.config.display_cols = 80
        interp.print_column = 54
        interp._sync_print_column_after_input()
        self.assertEqual(interp.print_column, 0)
        content = '"Please tell me a question that would distinguish "'
        text, _, _ = interp._render_print_content(content, ';', interp.print_column)
        self.assertNotIn('\n', text)
        self.assertEqual(text, 'Please tell me a question that would distinguish ')

    def test_input_prompt_flushed_before_blocking_read(self) -> None:
        """INPUT string prompt must appear before input() blocks."""
        interp = bbc_none()
        interp.set_program_line(10, 'INPUT "What animal were you thinking of? ",V$')
        interp.set_program_line(20, 'END')
        interp._prepare_run()
        stream = io.StringIO()
        visible: list[str] = []

        def read_input(prompt: str = '') -> str:
            visible.append(stream.getvalue())
            return 'platypus'

        with mock.patch.object(interp, '_get_program_stdout', return_value=stream), mock.patch.object(
            interp, '_read_program_input', side_effect=read_input,
        ):
            interp.execute_line(10, interp.program[10], [10, 20])

        self.assertTrue(visible, 'INPUT never called _read_program_input')
        self.assertIn('What animal were you thinking of?', visible[0])

    def test_fnstrip_preserves_albatross(self) -> None:
        interp = load_lines(bbc_none(), FNSTRIP_LINES)
        fn = interp._lookup_user_function('STRIP')
        self.assertIsNotNone(fn)
        self.assertEqual(interp._eval_user_function(fn, ['"albatross"']), 'albatross')

    def test_fnstrip_strips_leading_article(self) -> None:
        interp = load_lines(bbc_none(), FNSTRIP_LINES)
        fn = interp._lookup_user_function('STRIP')
        self.assertIsNotNone(fn)
        self.assertEqual(interp._eval_user_function(fn, ['"a sparrow"']), 'sparrow')
        self.assertEqual(interp._eval_user_function(fn, ['"an elephant"']), 'elephant')

    def test_pygame_input_uses_display_not_terminal(self) -> None:
        interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='pygame'))
        prompts: list[str] = []

        class _RecordingDisplay:
            def read_line(self, *, max_length: int = 255, tee=None) -> str:
                if tee is not None:
                    tee('Y')
                    tee('\n')
                return 'Y'

            def poll(self) -> bool:
                return True

            def write(self, text: str) -> None:
                prompts.append(text)

            def newline(self) -> None:
                return None

            def present(self) -> None:
                return None

        interp._display = _RecordingDisplay()
        interp._display_live = True
        with mock.patch.object(interp, '_ensure_display'), mock.patch.object(
            interp, '_flush_display',
        ), mock.patch('builtins.input', side_effect=AssertionError('terminal input')):
            line = interp._read_program_input('Name? ')
        self.assertEqual(line, 'Y')
        self.assertEqual(prompts, ['Name? '])


if __name__ == '__main__':
    unittest.main()
