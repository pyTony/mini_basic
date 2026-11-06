"""GW-BASIC/QBasic SCREEN, LOCATE, and LINE (x1,y1)-(x2,y2)[,colour] support.

Added to run classic IBM PC BASIC programs (e.g. a GW-BASIC 3D wireframe
cube demo) that mini_basic previously rejected with "Unknown statement:
SCREEN". These are mini/mbasic-dialect extensions, not real BBC BASIC
(which uses MODE and VDU 31/TAB instead) — see CLAUDE.md keyword-case
policy and runtime_parts/dialect.py's 'gw_screen_locate' feature gate.
"""
from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stdout

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig
from mini_basic.bbc_modes import GW_SCREEN_MODE_BASE, gw_screen_mode_spec

pytestmark = [pytest.mark.phase2, pytest.mark.graphics]


def _interp(dialect: str = 'mini') -> BASICInterpreter:
    return BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )


def _run(interp: BASICInterpreter, lines) -> str:
    for line_num, statement in lines:
        interp.set_program_line(line_num, statement)
    buf = io.StringIO()
    with redirect_stdout(buf):
        interp.run()
    return buf.getvalue()


class GwScreenModeSpecTests(unittest.TestCase):
    def test_screen_9_is_640x350_16col_ega(self):
        spec = gw_screen_mode_spec(9)
        assert spec is not None
        self.assertEqual((spec.gfx_width, spec.gfx_height), (640, 350))
        self.assertEqual((spec.text_cols, spec.text_rows), (80, 25))
        self.assertTrue(spec.plot_enabled)

    def test_screen_0_is_text_only(self):
        spec = gw_screen_mode_spec(0)
        assert spec is not None
        self.assertEqual(spec.gfx_width, 0)
        self.assertFalse(spec.plot_enabled)

    def test_screen_13_is_320x200_vga(self):
        spec = gw_screen_mode_spec(13)
        assert spec is not None
        self.assertEqual((spec.gfx_width, spec.gfx_height), (320, 200))

    def test_unknown_screen_number_is_none(self):
        self.assertIsNone(gw_screen_mode_spec(99))


class ScreenStatementTests(unittest.TestCase):
    def test_screen_9_sets_graphics_dims_and_offsets_mode(self):
        i = _interp('mini')
        out = _run(i, [(10, 'SCREEN 9'), (20, 'END')])
        self.assertEqual(i.error_line_num, 0)
        self.assertNotIn('?', out)
        self.assertEqual(i.config.graphics_width, 640)
        self.assertEqual(i.config.graphics_height, 350)
        self.assertEqual(i._graphics_mode, GW_SCREEN_MODE_BASE + 9)
        self.assertTrue(i._graphics_plot_enabled())

    def test_screen_0_disables_plot(self):
        i = _interp('mini')
        out = _run(i, [(10, 'SCREEN 0'), (20, 'END')])
        self.assertEqual(i.error_line_num, 0)
        self.assertNotIn('?', out)
        self.assertFalse(i._graphics_plot_enabled())

    def test_screen_rejected_under_bbc_dialect(self):
        i = _interp('bbc')
        out = _run(i, [(10, 'SCREEN 9'), (20, 'END')])
        self.assertNotEqual(i.error_line_num, 0)
        self.assertIn('not supported in this dialect', out)

    def test_screen_allowed_under_mbasic_dialect(self):
        i = _interp('mbasic')
        out = _run(i, [(10, 'SCREEN 9'), (20, 'END')])
        self.assertEqual(i.error_line_num, 0)
        self.assertNotIn('?', out)

    def test_mode_after_screen_clears_custom_spec(self):
        """Switching back to native MODE must drop the GW SCREEN override."""
        i = _interp('mini')
        out = _run(i, [(10, 'SCREEN 9'), (20, 'MODE 1'), (30, 'END')])
        self.assertEqual(i.error_line_num, 0)
        self.assertNotIn('?', out)
        self.assertIsNone(i._custom_mode_spec)
        self.assertEqual(i._graphics_mode, 1)


class LocateStatementTests(unittest.TestCase):
    def test_locate_sets_1_based_row_col(self):
        i = _interp('mini')
        out = _run(i, [(10, 'LOCATE 5,10'), (20, 'END')])
        self.assertEqual(i.error_line_num, 0)
        self.assertNotIn('?', out)
        self.assertEqual(i.text_row, 4)
        self.assertEqual(i.text_col, 9)

    def test_locate_row_only_keeps_current_col(self):
        i = _interp('mini')
        out = _run(i, [(10, 'LOCATE 5,10'), (20, 'LOCATE 2'), (30, 'END')])
        self.assertEqual(i.error_line_num, 0)
        self.assertNotIn('?', out)
        self.assertEqual(i.text_row, 1)
        self.assertEqual(i.text_col, 9)

    def test_locate_rejected_under_bbc_dialect(self):
        i = _interp('bbc')
        out = _run(i, [(10, 'LOCATE 1,1'), (20, 'END')])
        self.assertNotEqual(i.error_line_num, 0)
        self.assertIn('not supported in this dialect', out)


def _require_pygame_dummy() -> None:
    try:
        import pygame  # noqa: F401
    except ImportError as exc:
        raise unittest.SkipTest('pygame not installed') from exc
    os.environ['SDL_VIDEODRIVER'] = 'dummy'


def _run_pygame_without_shutdown(interp: BASICInterpreter, lines) -> str:
    from unittest.mock import patch

    for line_num, statement in lines:
        interp.set_program_line(line_num, statement)
    buf = io.StringIO()
    with patch.object(interp, '_shutdown_display', lambda *a, **k: None), patch(
        'time.sleep',
    ):
        with redirect_stdout(buf):
            interp.run()
    return buf.getvalue()


class LineStatementTests(unittest.TestCase):
    def setUp(self) -> None:
        _require_pygame_dummy()

    def test_classic_bbc_line_form_still_works(self):
        """Regression: pre-existing LINE x1,y1,x2,y2 / LINE ... TO ... forms."""
        from mini_basic.display import PygameDisplay, count_framebuffer_pixels

        i = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='pygame', hold_display_open=False)
        )
        out = _run_pygame_without_shutdown(i, [
            (10, 'MODE 8'),
            (20, 'GCOL 2'),
            (30, 'LINE 10,10,20,20'),
            (40, 'LINE 30,30 TO 40,40'),
            (50, 'END'),
        ])
        self.assertEqual(i.error_line_num, 0)
        self.assertNotIn('?', out)
        display = i._display
        self.assertIsInstance(display, PygameDisplay)
        pixels = display.capture_framebuffer()
        self.assertGreater(count_framebuffer_pixels(pixels, colour=2), 0)

    def test_gw_line_paren_form_with_colour_draws(self):
        """GW-BASIC: LINE (x1,y1)-(x2,y2),colour."""
        from mini_basic.display import PygameDisplay, count_framebuffer_pixels

        i = BASICInterpreter(
            InterpreterConfig(dialect='mini', display='pygame', hold_display_open=False)
        )
        out = _run_pygame_without_shutdown(i, [
            (10, 'SCREEN 9'),
            (20, 'DIM P(2,2)'),
            (30, 'P(1,1) = 10: P(1,2) = 10'),
            (40, 'P(2,1) = 50: P(2,2) = 50'),
            (50, 'LINE (P(1,1), P(1,2)) - (P(2,1), P(2,2)), 2'),
            (60, 'END'),
        ])
        self.assertEqual(i.error_line_num, 0)
        self.assertNotIn('?', out)
        display = i._display
        self.assertIsInstance(display, PygameDisplay)
        pixels = display.capture_framebuffer()
        self.assertGreater(count_framebuffer_pixels(pixels, colour=2), 0)

    def test_gw_line_box_form(self):
        """GW-BASIC: LINE (x1,y1)-(x2,y2),colour,B draws a rectangle outline."""
        from mini_basic.display import PygameDisplay, count_framebuffer_pixels

        i = BASICInterpreter(
            InterpreterConfig(dialect='mini', display='pygame', hold_display_open=False)
        )
        out = _run_pygame_without_shutdown(i, [
            (10, 'SCREEN 9'),
            (20, 'LINE (10,10)-(30,30), 2, B'),
            (30, 'END'),
        ])
        self.assertEqual(i.error_line_num, 0)
        self.assertNotIn('?', out)
        display = i._display
        self.assertIsInstance(display, PygameDisplay)
        pixels = display.capture_framebuffer()
        self.assertGreater(count_framebuffer_pixels(pixels, colour=2), 0)


class GwBasicCubeDemoIntegrationTest(unittest.TestCase):
    """End-to-end smoke test matching Tony's reported cube.bas program."""

    def test_cube_demo_like_program_runs_without_errors(self):
        i = _interp('mini')
        lines = [
            (40, 'CLS : SCREEN 9: COLOR 2,0'),
            (60, 'CX = 320: CY = 175'),
            (70, 'FOV = 300: ZDIST = 4'),
            (80, 'AX = 0: AY = 0'),
            (90, 'DIM V(8,3)'),
            (100, 'DIM P(8,2)'),
            (110, 'DIM E(12,2)'),
            (120, 'GOSUB 520'),
            (160, 'CLS'),
            (170, 'AX = AX + 0.08: AY = AY + 0.05'),
            (180, 'IF AX > 6.28 THEN AX = AX - 6.28'),
            (190, 'IF AY > 6.28 THEN AY = AY - 6.28'),
            (210, 'FOR I = 1 TO 8'),
            (220, 'X = V(I,1): Y = V(I,2): Z = V(I,3)'),
            (240, 'Y1 = Y * COS(AX) - Z * SIN(AX)'),
            (250, 'Z1 = Y * SIN(AX) + Z * COS(AX)'),
            (270, 'X2 = X * COS(AY) + Z1 * SIN(AY)'),
            (280, 'Z2 = -X * SIN(AY) + Z1 * COS(AY)'),
            (300, 'Z3 = Z2 + ZDIST'),
            (310, 'P(I,1) = (X2 * FOV) / Z3 + CX'),
            (320, 'P(I,2) = (Y1 * FOV) / Z3 + CY'),
            (330, 'NEXT I'),
            (350, 'FOR I = 1 TO 12'),
            (360, 'V1 = E(I,1): V2 = E(I,2)'),
            (370, 'LINE (P(V1,1), P(V1,2)) - (P(V2,1), P(V2,2)), 2'),
            (380, 'NEXT I'),
            (400, 'LOCATE 1,1: PRINT "IBM PC BASIC 3D ENGINE"'),
            (410, 'LOCATE 2,1: PRINT "PRESS CTRL+BREAK TO EXIT"'),
            (425, 'IF LOOPS > 2 THEN END'),
            (426, 'LOOPS = LOOPS + 1'),
            (430, 'GOTO 160'),
            (520, 'FOR I = 1 TO 8: READ V(I,1), V(I,2), V(I,3): NEXT I'),
            (530, 'DATA -1,-1,-1, 1,-1,-1, 1, 1,-1, -1, 1,-1'),
            (540, 'DATA -1,-1, 1, 1,-1, 1, 1, 1, 1, -1, 1, 1'),
            (550, 'FOR I = 1 TO 12: READ E(I,1), E(I,2): NEXT I'),
            (560, 'DATA 1,2, 2,3, 3,4, 4,1'),
            (570, 'DATA 5,6, 6,7, 7,8, 8,5'),
            (580, 'DATA 1,5, 2,6, 3,7, 4,8'),
            (590, 'RETURN'),
        ]
        out = _run(i, lines)
        self.assertEqual(i.error_line_num, 0, msg=out)
        self.assertNotIn('?', out)
        self.assertIn('IBM PC BASIC 3D ENGINE', out)


if __name__ == '__main__':
    unittest.main()
