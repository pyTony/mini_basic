"""Text-only session: no auto pygame; terminal interrupt during RUN."""
from __future__ import annotations

import os
import sys
import unittest
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig
from mini_basic.util.session import session_supports_gui, terminal_interrupt_pending

pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]


class SessionSupportsGuiTests(unittest.TestCase):
    def test_no_graphics_env_disables_gui(self):
        with patch.dict(os.environ, {'MINIBASIC_NO_GRAPHICS': '1'}, clear=False):
            self.assertFalse(session_supports_gui())

    def test_display_terminal_env_disables_gui(self):
        with patch.dict(os.environ, {'MINIBASIC_DISPLAY': 'terminal'}, clear=False):
            self.assertFalse(session_supports_gui())

    def test_linux_without_display_disables_gui(self):
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ('DISPLAY', 'WAYLAND_DISPLAY', 'MINIBASIC_NO_GRAPHICS', 'MINIBASIC_DISPLAY')
        }
        with patch.dict(os.environ, env, clear=True):
            with patch('sys.platform', 'linux'):
                self.assertFalse(session_supports_gui())

    def test_linux_with_display_allows_gui(self):
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ('MINIBASIC_NO_GRAPHICS', 'MINIBASIC_DISPLAY')
        }
        env['DISPLAY'] = ':0'
        with patch.dict(os.environ, env, clear=True):
            with patch('sys.platform', 'linux'):
                self.assertTrue(session_supports_gui())

    def test_dummy_sdl_does_not_force_text_only(self):
        """Tests use SDL_VIDEODRIVER=dummy with pygame; still allow auto-enable."""
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ('MINIBASIC_NO_GRAPHICS', 'MINIBASIC_DISPLAY')
        }
        env['SDL_VIDEODRIVER'] = 'dummy'
        if sys.platform.startswith('linux') and 'DISPLAY' not in env:
            env['DISPLAY'] = ':0'
        with patch.dict(os.environ, env, clear=True):
            # On Windows/mac always true unless env override; on Linux need DISPLAY
            if sys.platform.startswith('linux'):
                self.assertTrue(session_supports_gui())
            else:
                self.assertTrue(session_supports_gui())


class AutoEnableGuiGateTests(unittest.TestCase):
    def test_no_gui_session_keeps_terminal(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='terminal', optimization_level=0),
        )
        parsed = [(10, 'MODE 8', 0), (20, 'GCOL 0,1', 0)]
        with patch('mini_basic.util.session.session_supports_gui', return_value=False):
            with redirect_stdout(StringIO()):
                interp._maybe_auto_enable_pygame_display(parsed, announce=True)
        self.assertEqual(interp.config.display, 'terminal')

    def test_gui_session_still_auto_enables(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='terminal', optimization_level=0),
        )
        parsed = [(10, 'CLS', 0), (20, 'PRINT "x"', 0)]
        with patch('mini_basic.util.session.session_supports_gui', return_value=True):
            with redirect_stdout(StringIO()):
                interp._maybe_auto_enable_pygame_display(parsed, announce=False)
        self.assertEqual(interp.config.display, 'pygame')

    def test_refresh_off_program_starts_without_auto_present(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', hold_display_open=False),
        )
        interp.program[10] = 'MODE 9'
        interp.program[20] = '*REFRESH OFF'
        interp.program[30] = 'CIRCLE FILL 0,0,10'
        interp.program[40] = '*REFRESH'
        self.assertTrue(interp._program_uses_refresh_off())
        interp._refresh_enabled = True
        interp._apply_program_refresh_off_at_start()
        self.assertFalse(interp._refresh_enabled)

    def test_load_updates_caption_from_basename(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', hold_display_open=False),
        )
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bbc = os.path.join(root, 'examples', 'graphics', 'soccerball.bbc')
        bas = os.path.join(root, 'examples', 'graphics', 'soccerball.bas')
        if not (os.path.isfile(bbc) and os.path.isfile(bas)):
            self.skipTest('soccerball examples missing')
        with redirect_stdout(StringIO()):
            self.assertTrue(interp.load(bbc, announce=False))
        self.assertEqual(interp.config.display_caption, 'soccerball.bbc')
        with redirect_stdout(StringIO()):
            self.assertTrue(interp.load(bas, announce=False))
        self.assertEqual(interp.config.display_caption, 'soccerball.bas')

    def test_ensure_display_replaces_terminal_after_auto_pygame(self):
        """REPL already has TerminalDisplay; RUN must swap to pygame (not paint console)."""
        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from mini_basic.display import TerminalDisplay, PygameDisplay

        interp = BASICInterpreter(
            InterpreterConfig(
                dialect='bbc',
                display='terminal',
                optimization_level=2,
                hold_display_open=False,
            )
        )
        interp._display = TerminalDisplay(text_cols=40, text_rows=25)
        interp._display.begin_run()
        interp._display_live = True
        parsed = [(10, 'MODE 9', 0), (20, 'COLOUR 130', 0)]
        with patch('mini_basic.util.session.session_supports_gui', return_value=True):
            interp._maybe_auto_enable_pygame_display(parsed, announce=False)
        self.assertEqual(interp.config.display, 'pygame')
        interp._ensure_display()
        self.assertIsInstance(interp._display, PygameDisplay)
        interp._shutdown_display(hold=False)

    def test_display_locked_terminal_never_upgrades(self):
        interp = BASICInterpreter(
            InterpreterConfig(
                dialect='bbc',
                display='terminal',
                display_locked=True,
                optimization_level=0,
            ),
        )
        parsed = [(10, 'MODE 8', 0)]
        with patch('mini_basic.util.session.session_supports_gui', return_value=True):
            interp._maybe_auto_enable_pygame_display(parsed, announce=False)
        self.assertEqual(interp.config.display, 'terminal')


class TerminalInterruptTests(unittest.TestCase):
    def test_check_user_interrupt_raises_on_ctrl_c(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', optimization_level=0),
        )
        interp._run_interrupt_watch = True
        with patch(
            'mini_basic.util.session.terminal_interrupt_pending',
            return_value='ctrl-c',
        ):
            with self.assertRaises(KeyboardInterrupt):
                interp._check_user_interrupt()

    def test_check_user_interrupt_raises_on_esc(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', optimization_level=0),
        )
        interp._run_interrupt_watch = True
        with patch(
            'mini_basic.util.session.terminal_interrupt_pending',
            return_value='esc',
        ):
            with self.assertRaises(KeyboardInterrupt):
                interp._check_user_interrupt()

    def test_check_user_interrupt_idle_when_watch_off(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', optimization_level=0),
        )
        interp._run_interrupt_watch = False
        with patch(
            'mini_basic.util.session.terminal_interrupt_pending',
            return_value='esc',
        ):
            interp._check_user_interrupt()  # no raise

    def test_run_loop_aborts_on_terminal_interrupt(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', optimization_level=0),
        )
        interp.program[10] = 'PRINT "start"'
        interp.program[20] = 'GOTO 10'
        calls = {'n': 0}

        def fake_pending():
            calls['n'] += 1
            return 'esc' if calls['n'] > 2 else None

        with patch(
            'mini_basic.util.session.terminal_interrupt_pending',
            side_effect=fake_pending,
        ):
            with redirect_stdout(StringIO()) as buf:
                interp.run()
        self.assertTrue(interp._run_aborted or 'Goodbye' in buf.getvalue())


if __name__ == '__main__':
    unittest.main()
