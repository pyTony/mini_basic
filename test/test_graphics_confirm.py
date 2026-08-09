"""Graphics implementation-ready checks using pygame framebuffer capture."""
from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

pytestmark = [pytest.mark.phase2, pytest.mark.graphics]

from mini_basic.display import (
    PygameDisplay,
    colour_to_rgb,
    count_framebuffer_pixels,
    create_display,
)
from mini_basic import BASICInterpreter, InterpreterConfig, _script_file_kind

_FERN_MINI = """
MODE 8
OFF
GCOL 2
x=0
y=0
FOR i%=1 TO 120
  r = RND(1)
  CASE TRUE OF
    WHEN r<=0.1 A=0: B=0: C=0: D=0.16: E=0: F=0
    WHEN r>0.1 AND r<=0.86 A=.85: B=.04: C=-.04: D=.85: E=0: F=1.6
    WHEN r>0.86 AND r<=0.93 A=.2: B=-.26: C=.23: D=.22: E=0: F=1.6
    WHEN r>0.93 A=-.15: B =.28: C=.26: D=.24: E=0: F=.44
  ENDCASE
  newx=A*x+B*y+E
  newy=C*x+D*y+F
  x=newx
  y=newy
  MOVE 600+96*x, 32+96*y
  DRAW 600+96*x, 32+96*y
NEXT i%
END
""".strip()


def _require_pygame_dummy() -> None:
    try:
        import pygame  # noqa: F401
    except ImportError as exc:
        raise unittest.SkipTest('pygame not installed') from exc
    os.environ['SDL_VIDEODRIVER'] = 'dummy'


def _pygame_interp() -> BASICInterpreter:
    return BASICInterpreter(
        InterpreterConfig(
            dialect='bbc',
            display='pygame',
            optimization_level=0,
            hold_display_open=False,
        )
    )


def _run_without_display_shutdown(interp: BASICInterpreter) -> None:
    with patch.object(interp, '_shutdown_display', lambda *a, **k: None), patch(
        'time.sleep',
    ):
        interp.run()


def _capture_after_run(interp: BASICInterpreter):
    display = interp._display
    if not isinstance(display, PygameDisplay):
        raise AssertionError('expected PygameDisplay backend')
    return display.capture_framebuffer(), display.capture_canvas_rgb()


class GraphicsCaptureTests(unittest.TestCase):
    def setUp(self) -> None:
        _require_pygame_dummy()

    @staticmethod
    def _shorten_loaded_fern(interp: BASICInterpreter, *, iterations: int) -> None:
        for line_num in sorted(interp.program):
            stmt = interp.program[line_num]
            upper = stmt.strip().upper()
            if upper.startswith('FOR '):
                interp.program[line_num] = f'FOR i%=1 TO {iterations}'
            elif upper.startswith('REPEAT'):
                interp.program[line_num] = 'END'

    def test_pygame_capture_framebuffer_and_canvas(self):
        display = create_display(
            'pygame',
            graphics_width=640,
            graphics_height=512,
            scale=1,
        )
        self.assertIsInstance(display, PygameDisplay)
        display.begin_run()
        display.set_mode(8)
        display.gcol(0, 2)
        display.move_absolute(600, 32)
        display.draw_absolute(600, 32)
        display.present()

        pixels = display.capture_framebuffer()
        self.assertEqual(len(pixels), 512)
        self.assertEqual(len(pixels[0]), 640)
        self.assertGreater(count_framebuffer_pixels(pixels, colour=2), 0)

        width, height, canvas = display.capture_canvas_rgb()
        self.assertEqual((width, height), (640, 512))
        green = colour_to_rgb(2)
        flat = [px for row in canvas for px in row]
        self.assertIn(green, flat)
        display.end_run()

    def test_mode8_interpreter_draw_visible_green(self):
        lines = [
            (10, 'MODE 8'),
            (20, 'GCOL 2'),
            (30, 'MOVE 600, 32'),
            (40, 'DRAW 600, 32'),
            (50, 'END'),
        ]
        interp = _pygame_interp()
        for line_num, statement in lines:
            interp.set_program_line(line_num, statement)
        _run_without_display_shutdown(interp)
        pixels, (_, _, canvas) = _capture_after_run(interp)
        self.assertGreater(count_framebuffer_pixels(pixels, colour=2), 0)
        self.assertIn(colour_to_rgb(2), [px for row in canvas for px in row])

    def test_colour_130_cls_clears_green_background(self):
        """COLOUR 130 sets background colour 2; CLS must clear graphics to green."""
        lines = [
            (10, 'MODE 9'),
            (20, 'COLOUR 130'),
            (30, 'CLS'),
            (40, 'END'),
        ]
        interp = _pygame_interp()
        for line_num, statement in lines:
            interp.set_program_line(line_num, statement)
        _run_without_display_shutdown(interp)
        pixels, (width, height, canvas) = _capture_after_run(interp)
        self.assertEqual((width, height), (640, 512))
        green_count = count_framebuffer_pixels(pixels, colour=2)
        self.assertGreater(green_count, width * height // 2)
        self.assertIn(colour_to_rgb(2), [px for row in canvas for px in row])

    def test_fractal_pattern_renders_many_green_pixels(self):
        interp = _pygame_interp()
        line_num = 10
        for raw in _FERN_MINI.splitlines():
            interp.set_program_line(line_num, raw.strip())
            line_num += 10
        _run_without_display_shutdown(interp)
        pixels, _ = _capture_after_run(interp)
        green_count = count_framebuffer_pixels(pixels, colour=2)
        self.assertGreater(green_count, 40, f'expected fern pixels, got {green_count}')

    def test_loaded_fern_txt_renders_green_pixels(self):
        path = os.path.join(
            _ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'graphics',
            'fern.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('missing fern.txt')
        interp = _pygame_interp()
        interp.load(path)
        self._shorten_loaded_fern(interp, iterations=120)
        _run_without_display_shutdown(interp)
        pixels, _ = _capture_after_run(interp)
        self.assertGreater(count_framebuffer_pixels(pixels, colour=2), 40)

    def test_implementation_ready_confirmation(self):
        """End-to-end: corpus .txt loads as program and draws visible graphics."""
        path = os.path.join(
            _ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'graphics',
            'fern.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('missing fern.txt')
        self.assertEqual(_script_file_kind(path), 'program')

        interp = _pygame_interp()
        interp.load(path)
        self._shorten_loaded_fern(interp, iterations=80)

        buf = io.StringIO()
        with redirect_stdout(buf):
            _run_without_display_shutdown(interp)
        errors = [line for line in buf.getvalue().splitlines() if line.startswith('?')]
        self.assertEqual(errors, [], errors)
        self.assertTrue(interp._graphics_plot_enabled())

        pixels, (width, height, canvas) = _capture_after_run(interp)
        self.assertEqual((width, height), (640, 512))
        green_count = count_framebuffer_pixels(pixels, colour=2)
        self.assertGreater(green_count, 20, 'fern should paint green pixels')
        self.assertIn(colour_to_rgb(2), [px for row in canvas for px in row])

    def test_bbc_graphics_demo_draws_expected_colours(self):
        path = os.path.join(_ROOT, 'examples', 'mini', 'bbc_graphics_demo.bas')
        if not os.path.isfile(path):
            self.skipTest('missing bbc_graphics_demo.bas')
        interp = BASICInterpreter(
            InterpreterConfig(
                dialect='mini',
                display='pygame',
                optimization_level=0,
                hold_display_open=False,
            )
        )
        interp.load(path, announce=False)
        _run_without_display_shutdown(interp)
        pixels, (_, _, canvas) = _capture_after_run(interp)
        cyan = count_framebuffer_pixels(pixels, colour=6)
        green = count_framebuffer_pixels(pixels, colour=2)
        red = count_framebuffer_pixels(pixels, colour=1)
        self.assertGreater(cyan, 500, 'large cyan circle on the right')
        self.assertGreater(green, 80, 'green rectangle outline upper left')
        self.assertGreater(red, 200, 'red triangle and small circle')
        yellow = colour_to_rgb(11)
        flat = [px for row in canvas for px in row]
        bright_yellow = sum(
            1 for px in flat
            if px == yellow or (px[0] > 180 and px[1] > 180 and px[2] < 80)
        )
        self.assertGreater(bright_yellow, 40, 'yellow caption text')

    def test_mode19_window_is_landscape_vga(self):
        """MODE 19 (640×480 VGA) must open a landscape 4:3 window, not portrait."""
        display = create_display('pygame', scale=1, scale_locked=True)
        display.begin_run()
        display.set_mode(19)
        display.set_colour(11)
        display.goto(14, 10)
        display.write('Readable VGA caption')
        display.present()
        win_w, win_h = display._window_client_size()
        self.assertEqual((win_w, win_h), (640, 480))
        self.assertGreater(win_w, win_h)
        self.assertEqual(display._pixel_block_size(), (1, 1))
        display.end_run()

    def test_mode0_keeps_tall_bbc_pixels(self):
        """Authentic BBC MODE 0 still uses par 1:2 (tall non-square pixels)."""
        display = create_display('pygame', scale=1, scale_locked=True)
        display.begin_run()
        display.set_mode(0)
        self.assertEqual(display._pixel_block_size(), (1, 2))
        self.assertEqual(display._window_client_size(), (640, 512))
        display.end_run()

    def test_graphics_mode_caption_uses_crisp_glyph_columns(self):
        """MODE 1 captions must not squash SysFont glyphs into unreadable smears."""
        display = create_display('pygame', scale=2, scale_locked=True)
        display.begin_run()
        display.set_mode(1)
        display.set_colour(11)
        caption = 'bbc_graphics_demo'
        display.goto(22, 6)
        display.write(caption)
        display.present()
        self.assertIsInstance(display._font, display._pygame.font.Font)
        cw = display._effective_cell_width()
        ch = display._effective_cell_height()
        y = 22 * ch
        canvas = display._canvas
        yellow = colour_to_rgb(11)
        for index, expected_ch in enumerate(caption):
            x0 = (6 + index) * cw
            yellow_count = sum(
                1
                for dx in range(cw)
                for dy in range(ch)
                if canvas.get_at((x0 + dx, y + dy))[:3] == yellow
            )
            self.assertGreater(
                yellow_count,
                0,
                f'expected visible glyph for {expected_ch!r}',
            )
            self.assertLessEqual(
                yellow_count,
                20,
                f'glyph for {expected_ch!r} should be crisp bitmap, not smeared',
            )
        screen_w, screen_h, screen_rows = display.capture_screen_rgb()
        self.assertEqual((screen_w, screen_h), (640, 512))
        # Nearest-neighbour 2× upscale doubles logical pixel blocks on screen.
        self.assertEqual(screen_rows[0][0], screen_rows[0][1])
        self.assertEqual(screen_rows[0][0], screen_rows[1][0])
        display.end_run()

    def test_sprites_demo_draws_sprites_and_caption(self):
        path = os.path.join(_ROOT, 'examples', 'mini', 'sprites_demo.bas')
        if not os.path.isfile(path):
            self.skipTest('missing sprites_demo.bas')
        interp = BASICInterpreter(
            InterpreterConfig(
                dialect='mini',
                display='pygame',
                optimization_level=0,
                hold_display_open=False,
            )
        )
        interp.load(path, announce=False)
        _run_without_display_shutdown(interp)
        display = interp._display
        if not isinstance(display, PygameDisplay):
            self.raiseFailure('expected PygameDisplay')
        text = ''.join(
            display._text[22][col][0]
            for col in range(display.text_cols)
            if display._text[22][col][0] != ' '
        )
        self.assertEqual(text, 'sprites_demo')
        self.assertEqual(len(display._sprite_placements), 2)
        _, _, canvas = display.capture_canvas_rgb()
        red = colour_to_rgb(1)
        green = colour_to_rgb(2)
        canvas_flat = [px for row in canvas for px in row]
        self.assertGreater(canvas_flat.count(red), 20, 'red invader sprite')
        self.assertGreater(canvas_flat.count(green), 15, 'green ship sprite')

    def test_circle_fill_pixel_count_matches_area(self):
        """CIRCLE FILL must paint roughly pi*r^2 screen pixels (MODE 8 scales OS units)."""
        from test.bbc_expect import circle_screen_pixel_area

        interp = _pygame_interp()
        radius = 40
        interp.program = {
            10: 'MODE 8',
            20: 'OFF',
            30: 'ORIGIN 320, 256',
            40: 'GCOL 3',
            50: f'CIRCLE FILL 0, 0, {radius}',
            60: 'END',
        }
        _run_without_display_shutdown(interp)
        display = interp._display
        if not isinstance(display, PygameDisplay):
            self.fail('expected PygameDisplay')
        pixels, _ = _capture_after_run(interp)
        filled = count_framebuffer_pixels(pixels, colour=3)
        expected = circle_screen_pixel_area(radius, display._gfx.x_scale)
        self.assertGreater(filled, expected * 0.85)
        self.assertLess(filled, expected * 1.15)

    def test_circle_outline_thinner_than_fill(self):
        from test.bbc_expect import circle_screen_outline_bounds, circle_screen_pixel_area

        interp = _pygame_interp()
        radius = 35
        interp.program = {
            10: 'MODE 8',
            20: 'OFF',
            30: 'ORIGIN 320, 256',
            40: 'GCOL 5',
            50: f'CIRCLE 0, 0, {radius}',
            60: 'END',
        }
        _run_without_display_shutdown(interp)
        display = interp._display
        if not isinstance(display, PygameDisplay):
            self.fail('expected PygameDisplay')
        pixels, _ = _capture_after_run(interp)
        outline = count_framebuffer_pixels(pixels, colour=5)
        low, high = circle_screen_outline_bounds(radius, display._gfx.x_scale)
        fill_estimate = circle_screen_pixel_area(radius, display._gfx.x_scale)
        self.assertGreater(outline, low)
        self.assertLess(outline, high)
        self.assertLess(outline, fill_estimate * 0.35)

    def test_circlefill_alias_matches_circle_fill(self):
        from test.bbc_expect import circle_screen_pixel_area

        interp = _pygame_interp()
        radius = 30
        interp.program = {
            10: 'MODE 8',
            20: 'OFF',
            30: 'ORIGIN 320, 256',
            40: 'GCOL 2',
            50: f'CIRCLEFILL 0, 0, {radius}',
            60: 'END',
        }
        _run_without_display_shutdown(interp)
        display = interp._display
        if not isinstance(display, PygameDisplay):
            self.fail('expected PygameDisplay')
        pixels, _ = _capture_after_run(interp)
        filled = count_framebuffer_pixels(pixels, colour=2)
        expected = circle_screen_pixel_area(radius, display._gfx.x_scale)
        self.assertGreater(filled, expected * 0.85)
        self.assertLess(filled, expected * 1.15)

    def test_wheel_spokes_cluster_at_screen_centre(self):
        """wheel.txt colour discs must ring around centre, not hug bottom-left. (Note: program draws discs, not spokes/lines.)"""
        import math

        path = os.path.join(
            _ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'graphics',
            'wheel.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('missing wheel.txt')

        interp = _pygame_interp()
        interp.load(path)
        for line_num in sorted(interp.program):
            upper = interp.program[line_num].strip().upper()
            if upper.startswith('REPEAT') and 'WAIT' not in upper:
                interp.program[line_num] = 'REM once'
            elif upper.startswith('UNTIL FALSE'):
                interp.program[line_num] = 'REM end'
            elif 'REPEAT WAIT' in upper:
                interp.program[line_num] = 'REM wait'

        _run_without_display_shutdown(interp)
        pixels, _ = _capture_after_run(interp)
        display = interp._display
        if not isinstance(display, PygameDisplay):
            self.fail('expected PygameDisplay')

        filled = count_framebuffer_pixels(pixels, colour=1)
        self.assertGreater(filled, 15000, 'expected many filled disc/circle pixels')

        pts = [(col, row) for row, r in enumerate(pixels) for col, p in enumerate(r) if p == 1]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        self.assertAlmostEqual(cx, display.graphics_width / 2, delta=35)
        self.assertAlmostEqual(cy, display.graphics_height / 2, delta=35)

        angles = sorted(
            math.degrees(math.atan2(col - cx, -(row - cy)))
            for col, row in pts[:: max(1, len(pts) // 400)]
        )
        spread = max(angles) - min(angles)
        self.assertGreater(spread, 120.0)

    def test_gcol_xor_mode_erases_line_via_interpreter(self):
        interp = _pygame_interp()
        interp.program = {
            10: 'MODE 8',
            20: 'ORIGIN 640, 512',
            30: 'GCOL 0, 1',
            40: 'MOVE -200, 0',
            50: 'DRAW 200, 0',
            60: 'GCOL 3, 1',
            70: 'MOVE -200, 0',
            80: 'DRAW 200, 0',
            90: 'END',
        }
        _run_without_display_shutdown(interp)
        pixels, _ = _capture_after_run(interp)
        self.assertEqual(count_framebuffer_pixels(pixels, colour=1), 0)

    def test_cli_pygame_corpus_txt_draws_pixels(self):
        path = os.path.join(
            _ROOT,
            'test',
            'corpus',
            'bbcsdl',
            'graphics',
            'illusion.txt',
        )
        if not os.path.isfile(path):
            self.skipTest('missing illusion.txt')

        interp = _pygame_interp()
        interp.load(path)
        for line_num in sorted(interp.program):
            upper = interp.program[line_num].strip().upper()
            if upper.startswith('REPEAT'):
                interp.program[line_num] = 'END'

        _run_without_display_shutdown(interp)
        pixels, _ = _capture_after_run(interp)
        self.assertGreater(count_framebuffer_pixels(pixels), 0)


if __name__ == '__main__':
    unittest.main()
