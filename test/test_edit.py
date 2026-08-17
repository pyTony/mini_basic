"""EDIT n prefill / POSIX arrows, and bare EDIT → system editor."""
from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import MagicMock, patch

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig
from mini_basic.repl.windows_input import LineEditCancelled, windows_line_edit
from mini_basic.runtime_parts.helpers import (
    _posix_editing_input,
    _prompt_editing_input,
)

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


class EditCommandTests(unittest.TestCase):
    def test_line_edit_works_without_msvcrt(self) -> None:
        """Linux EDIT n must not import msvcrt (that hid the prefilled text)."""
        keys = list('\n')
        with patch.dict(sys.modules, {'msvcrt': None}):
            result = windows_line_edit(
                '310 ',
                default='    WEND',
                getwch=lambda: keys.pop(0),
                use_history=False,
                use_completion=False,
                escape_cancels=True,
            )
        self.assertEqual(result, '    WEND')

    def test_posix_left_arrow_does_not_cancel(self) -> None:
        """Left arrow is ESC [ D — must move the cursor, not abandon the edit."""
        keys = list('\x1b[D\n')
        result = _posix_editing_input(
            '420 ',
            'ang += 0.03',
            getwch=lambda: keys.pop(0),
        )
        self.assertEqual(result, 'ang += 0.03')

    def test_posix_ctrl_c_cancels_line_edit(self) -> None:
        keys = list('\x03')
        with self.assertRaises(LineEditCancelled):
            _posix_editing_input(
                '420 ',
                'ang += 0.03',
                getwch=lambda: keys.pop(0),
            )

    def test_edit_line_esc_leaves_program_unchanged(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.program[420] = 'ang += 0.03'
        with patch(
            'mini_basic.runtime_parts.helpers._prompt_editing_input',
            side_effect=LineEditCancelled(),
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.edit_line(420)
        self.assertEqual(interp.program[420], 'ang += 0.03')
        self.assertIn('Cancelled', buf.getvalue())

    def test_edit_line_ctrl_c_leaves_program_unchanged(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.program[420] = 'ang += 0.03'
        with patch(
            'mini_basic.runtime_parts.helpers._prompt_editing_input',
            side_effect=KeyboardInterrupt(),
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.edit_line(420)
        self.assertEqual(interp.program[420], 'ang += 0.03')
        self.assertIn('Cancelled', buf.getvalue())

    def test_posix_editing_input_arrows_edit_prefill(self) -> None:
        keys = list('\x1b[D\x7f\n')
        result = _posix_editing_input(
            '420 ',
            'ang += 0.03',
            getwch=lambda: keys.pop(0),
        )
        self.assertEqual(result, 'ang += 0.3')

    def test_prefill_does_not_use_readline(self) -> None:
        """WSL GNU readline insert_text doubles EDIT lines; never use it to prefill."""
        fake_readline = MagicMock()
        with patch('mini_basic.runtime_parts.helpers.sys.platform', 'linux'):
            with patch('mini_basic.runtime_parts.helpers.sys.stdin.isatty', return_value=True):
                with patch(
                    'mini_basic.runtime_parts.helpers._posix_editing_input',
                    side_effect=OSError('no termios'),
                ):
                    with patch(
                        'mini_basic.runtime_parts.helpers._get_readline_module',
                        return_value=fake_readline,
                    ):
                        with patch('builtins.input', return_value='PRINT "new"'):
                            result = _prompt_editing_input('50 ', 'PRINT "old"')
        self.assertEqual(result, 'PRINT "new"')
        fake_readline.set_startup_hook.assert_not_called()
        fake_readline.insert_text.assert_not_called()

    def test_edit_line_does_not_preview_the_stored_line(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.program[310] = 'WEND'
        interp.line_indent[310] = 4
        with patch(
            'mini_basic.runtime_parts.helpers._prompt_editing_input',
            return_value='    WEND',
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                interp.edit_line(310)
        self.assertNotIn('WEND', buf.getvalue())
        self.assertEqual(interp.program[310], 'WEND')

    def test_choose_editor_prefers_env(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        with patch.dict(os.environ, {'EDITOR': 'nano', 'VISUAL': ''}, clear=False):
            with patch('shutil.which', return_value='/usr/bin/nano'):
                cmd = interp._choose_external_editor()
        self.assertEqual(cmd, ['/usr/bin/nano'])

    def test_edit_reloads_memory_then_declines_real_file(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.set_program_line(10, 'PRINT 1')
        interp.loaded_filename = 'game.bas'

        def fake_edit(path: str) -> bool:
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('20 PRINT 2\n')
            return True

        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            with patch.object(interp, '_launch_external_editor', side_effect=fake_edit):
                with patch('builtins.input', return_value='n') as prompted:
                    interp.edit_program()
        prompted.assert_called_once()
        self.assertIn('game.bas', prompted.call_args[0][0])
        self.assertEqual(interp.program.get(20), 'PRINT 2')
        self.assertNotIn(10, interp.program)
        self.assertEqual(interp.loaded_filename, 'game.bas')
        self.assertIn('Reloaded', out.getvalue())
        self.assertIn('Kept in memory only', out.getvalue())

    def test_edit_saves_real_file_when_confirmed(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        with tempfile.TemporaryDirectory() as tmp:
            real = os.path.join(tmp, 'game.bas')
            with open(real, 'w', encoding='utf-8') as handle:
                handle.write('10 PRINT 1\n')
            interp.working_dir = tmp
            interp.load(real, announce=False)
            interp.loaded_filename = real

            def fake_edit(path: str) -> bool:
                with open(path, 'w', encoding='utf-8') as handle:
                    handle.write('20 PRINT 2\n')
                return True

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                with patch.object(interp, '_launch_external_editor', side_effect=fake_edit):
                    with patch('builtins.input', return_value='y'):
                        interp.edit_program()
            self.assertEqual(interp.program.get(20), 'PRINT 2')
            with open(real, encoding='utf-8') as handle:
                disk = handle.read()
            self.assertIn('PRINT 2', disk)
            self.assertNotIn('PRINT 1', disk)

    def test_edit_tmp_only_prompts_save_as(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.set_program_line(10, 'PRINT 1')
        self.assertIsNone(interp.loaded_filename)

        def fake_edit(path: str) -> bool:
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('30 PRINT 3\n')
            return True

        with tempfile.TemporaryDirectory() as tmp:
            interp.working_dir = tmp
            out = io.StringIO()
            with redirect_stdout(out), redirect_stderr(io.StringIO()):
                with patch.object(interp, '_launch_external_editor', side_effect=fake_edit):
                    with patch('builtins.input', return_value='new.bas') as prompted:
                        interp.edit_program()
            self.assertIn('Save as', prompted.call_args[0][0])
            self.assertEqual(interp.program.get(30), 'PRINT 3')
            self.assertTrue(os.path.isfile(os.path.join(tmp, 'new.bas')))
            self.assertEqual(interp.loaded_filename, 'new.bas')

    def test_edit_unchanged_skips_save_prompt(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.set_program_line(10, 'PRINT 1')
        interp.loaded_filename = 'game.bas'
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            with patch.object(interp, '_launch_external_editor', return_value=True):
                with patch('builtins.input', side_effect=AssertionError('no prompt')):
                    interp.edit_program()
        self.assertEqual(interp.program[10], 'PRINT 1')
        self.assertIn('No changes', out.getvalue())

    def test_editor_missing_prints_hint(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.program[10] = 'PRINT 1'
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(io.StringIO()):
            with patch.object(interp, '_choose_external_editor', return_value=None):
                interp.edit_program()
        self.assertIn('no editor', buf.getvalue())
        self.assertEqual(interp.program[10], 'PRINT 1')


if __name__ == '__main__':
    unittest.main()
