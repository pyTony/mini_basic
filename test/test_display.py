import os
import sys
import time
import unittest

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic.display import (
    NullDisplay,
    aspect_fit_size,
    colour_to_rgb,
    count_framebuffer_pixels,
    create_display,
    desktop_size,
)

pytestmark = [pytest.mark.phase2, pytest.mark.graphics]



class DisplayTests(unittest.TestCase):
    def test_desktop_size_uses_largest_display(self):
        pygame = type('P', (), {})()
        pygame.display = type('D', (), {
            'get_desktop_sizes': staticmethod(lambda: [(1280, 720), (1920, 1080)]),
            'Info': staticmethod(lambda: type('I', (), {'current_w': 800, 'current_h': 600})()),
        })()
        self.assertEqual(desktop_size(pygame), (1920, 1080))

    def test_null_display_is_noop(self):
        display = NullDisplay()
        display.begin_run()
        display.write('hello')
        display.plot(1, 2, 3)
        display.present()
        display.end_run()

    def test_bbc_palette(self):
        self.assertEqual(colour_to_rgb(0), (0, 0, 0))
        self.assertEqual(colour_to_rgb(7), (255, 255, 255))

    def test_create_terminal_backend(self):
        from mini_basic.display import TerminalDisplay

        display = create_display('terminal')
        self.assertIsInstance(display, TerminalDisplay)

    def test_terminal_reverse_colour_cells(self):
        """COLOUR 0,7 (black on white) must stick on TerminalDisplay cells."""
        from mini_basic.display import TerminalDisplay

        display = TerminalDisplay(text_cols=20, text_rows=5)
        display.begin_run()
        display.set_colour(0)       # fg black
        display.set_colour(128 + 7) # bg white
        display.goto(0, 0)
        display.write('CRASH')
        self.assertEqual(display._text[0][0], ('C', 0, 7))
        self.assertEqual(display._text[0][4], ('H', 0, 7))
        display.set_colour(7)
        display.set_colour(128 + 0)
        display.goto(1, 0)
        display.write('ok')
        self.assertEqual(display._text[1][0], ('o', 7, 0))
        display.end_run()

    def test_pygame_text_grid(self):
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from mini_basic.display import PygameDisplay

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        display = PygameDisplay(text_cols=10, text_rows=5, scale=1)
        display.begin_run()
        display.set_colour(2)
        display.goto(1, 2)
        display.write('Hi')
        display.present()
        self.assertEqual(display._text[1][2][:2], ('H', 2))
        self.assertEqual(display._text[1][3][:2], ('i', 2))
        self.assertFalse(display._text[1][2][3])
        display.end_run()

    def test_pygame_poll_reports_closed_window(self):
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from mini_basic.display import PygameDisplay

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        display = PygameDisplay(text_cols=10, text_rows=5, scale=1)
        display.begin_run()
        display._open = False
        self.assertFalse(display.poll())
        display.end_run()

    def test_pygame_mark_closed_then_begin_run_reopens(self):
        """User close must free surfaces; begin_run must open a new window."""
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from mini_basic.display import PygameDisplay

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        display = PygameDisplay(text_cols=10, text_rows=5, scale=1)
        display.begin_run()
        self.assertTrue(display.is_open)
        display.mark_closed()
        self.assertFalse(display.is_open)
        self.assertIsNone(display._screen)
        # end_run after already-closed must not leave zombies (idempotent)
        display.end_run()
        display.begin_run()
        self.assertTrue(display.is_open)
        self.assertIsNotNone(display._screen)
        display.write('ok')
        display.present()
        display.end_run()

    def test_pygame_end_run_does_not_quit_sdl(self):
        """Second RUN must not inherit a Clock last_tick across pygame.quit()."""
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from mini_basic.display import PygameDisplay

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        display = PygameDisplay(text_cols=10, text_rows=5, scale=1, fps_limit=60)
        display.begin_run()
        self.assertTrue(pygame.get_init())
        display.present(force=True)
        display.end_run()
        self.assertIsNone(display._clock)
        # Video closed; pygame itself stays up so get_ticks() is not reset.
        self.assertTrue(pygame.get_init())
        display.begin_run()
        # Poisoned last_tick (old bug: Clock survived pygame.quit() + tick reset).
        display._last_present_ms = pygame.time.get_ticks() + 20_000
        t0 = time.perf_counter()
        display.present(force=True)
        elapsed = time.perf_counter() - t0
        self.assertLess(elapsed, 2.0)
        display.end_run()

    def test_interpreter_reopens_pygame_after_close(self):
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from mini_basic.config import InterpreterConfig
        from mini_basic.runtime import BASICInterpreter
        from mini_basic.type_system import ProgramExit

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        interp = BASICInterpreter(
            InterpreterConfig(display='pygame', dialect='bbc', hold_display_open=True)
        )
        interp._ensure_display()
        self.assertTrue(interp._display_enabled())
        # Simulate X button: surfaces torn down, live flag stale (old bug).
        interp._display.mark_closed()
        self.assertFalse(interp._display_is_alive())
        self.assertFalse(interp._display_enabled())
        # Program/REPL path that used to crash:
        interp._ensure_display()
        self.assertTrue(interp._display_enabled())
        interp.execute_immediate('PRINT "alive"')
        # ON CLOSE path clears live and exits program
        interp._display.mark_closed()
        interp._display_live = True
        with self.assertRaises(ProgramExit):
            interp._invoke_on_close_and_exit()
        self.assertFalse(interp._display_live)
        # Next ensure reopens for another RUN
        interp._ensure_display()
        self.assertTrue(interp._display.is_open)
        interp._shutdown_display(hold=False)

    def test_aspect_fit_mode9_into_gnome_usable_height(self):
        """2× MODE 9 (1280×1024) into a 1080p client of 1280×932 keeps 5:4."""
        self.assertEqual(aspect_fit_size(1280, 1024, 1280, 932), (1165, 932))
        self.assertEqual(aspect_fit_size(1280, 1024, 1280, 1024), (1280, 1024))

    def test_mode9_default_scale_is_2x_on_1080p_windows(self):
        """WSL and native Windows should both keep default 2x on a 1080p desk."""
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from unittest import mock

        from mini_basic.display import PygameDisplay

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        with mock.patch('mini_basic.display.desktop_size', return_value=(1920, 1080)):
            with mock.patch('mini_basic.display.sys.platform', 'win32'):
                display = PygameDisplay(
                    graphics_width=640,
                    graphics_height=512,
                    scale=2,
                    scale_locked=False,
                )
                display.begin_run()
                display.set_mode(9)
                self.assertEqual(display.scale, 2)
                self.assertEqual(display._screen.get_size(), (1280, 1024))
                display.end_run()

    def test_pygame_scale_locked_honours_cli_scale(self):
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from unittest import mock

        from mini_basic.display import PygameDisplay

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        with mock.patch('mini_basic.display.desktop_size', return_value=(1920, 1080)):
            display = PygameDisplay(
                graphics_width=320,
                graphics_height=256,
                scale=2,
                scale_locked=True,
            )
            display.begin_run()
            display.set_mode(1)
            self.assertEqual(display.scale, 2)
            self.assertEqual(display._screen.get_size(), (640, 512))
            self.assertEqual(display._surface_size(), (640, 512))
            display.end_run()

    def test_pygame_scale_locked_not_clamped_to_desktop(self):
        """--scale 3 and --scale 4 must differ even when neither fits 1080p height."""
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from unittest import mock

        from mini_basic.display import PygameDisplay

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        # MODE 8 size: 640×512 ×3 = 1920×1536 > 1080p — old code clamped both 3 and 4 to 2.
        sizes = {}
        with mock.patch('mini_basic.display.desktop_size', return_value=(1920, 1080)):
            for n in (3, 4):
                display = PygameDisplay(
                    graphics_width=640,
                    graphics_height=512,
                    scale=n,
                    scale_locked=True,
                )
                display.begin_run()
                display.set_mode(8)
                sizes[n] = (display.scale, display._screen.get_size())
                display.end_run()
        self.assertEqual(sizes[3], (3, (1920, 1536)))
        self.assertEqual(sizes[4], (4, (2560, 2048)))
        self.assertNotEqual(sizes[3][1], sizes[4][1])

    def test_mode0_maps_nonzero_text_colours_to_white(self):
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from mini_basic.config import InterpreterConfig
        from mini_basic.display import colour_to_rgb
        from mini_basic.runtime import BASICInterpreter

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        cfg = InterpreterConfig(dialect='bbc', display='pygame')
        interp = BASICInterpreter(cfg)
        interp.new(announce=False)
        interp.execute_immediate('MODE 0')
        interp.execute_immediate('COLOUR 1')
        interp.execute_immediate('PRINT "A";')
        interp.execute_immediate('COLOUR 3')
        interp.execute_immediate('PRINT "B";')
        d = interp._display
        d._render_graphics_mode()
        white = colour_to_rgb(7)
        red = colour_to_rgb(1)
        yellow = colour_to_rgb(3)
        self.assertEqual(d._canvas.get_at((2, 4))[:3], white)
        self.assertEqual(d._canvas.get_at((10, 4))[:3], white)
        self.assertNotEqual(white, red)
        self.assertNotEqual(white, yellow)

    def test_bbc_colour_wraps_to_eight_bits(self):
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from mini_basic.config import InterpreterConfig
        from mini_basic.runtime import BASICInterpreter

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        cfg = InterpreterConfig(dialect='bbc', display='pygame')
        interp = BASICInterpreter(cfg)
        interp.new(announce=False)
        interp.execute_immediate('MODE 0')
        interp.execute_immediate('COLOUR 256')
        self.assertEqual(interp.text_fg_colour, 0)
        interp.execute_immediate('COLOUR 384')
        self.assertEqual(interp.text_bg_colour, 0)
        interp.execute_immediate('COLOUR 255')
        self.assertEqual(interp.text_bg_colour, 127)

    def test_colour_136_enables_flash_on_subsequent_print(self):
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from unittest import mock

        from mini_basic.config import InterpreterConfig
        from mini_basic.display import colour_to_rgb
        from mini_basic.runtime import BASICInterpreter

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        cfg = InterpreterConfig(dialect='bbc', display='pygame')
        interp = BASICInterpreter(cfg)
        interp.new(announce=False)
        interp.execute_immediate('MODE 0')
        interp.execute_immediate('COLOUR 7')
        interp.execute_immediate('PRINT "A";')
        interp.execute_immediate('COLOUR 136')
        interp.execute_immediate('PRINT "2";')
        d = interp._display
        row = d._cursor_row
        self.assertEqual(d._text[row][1][0], '2')
        self.assertTrue(d._text[row][1][3])
        cw = d._effective_cell_width()

        # Flash-only COLOUR 136 keeps background 0 (black); count non-black pixels.
        bg_rgb = colour_to_rgb(0)

        def count_glyph_pixels():
            d._render_graphics_mode()
            count = 0
            x0 = cw
            for y in range(d._effective_cell_height()):
                for x in range(x0, x0 + cw):
                    if d._canvas.get_at((x, y))[:3] != bg_rgb:
                        count += 1
            return count

        with mock.patch.object(d._pygame.time, 'get_ticks', return_value=0):
            flash_on = count_glyph_pixels()
        with mock.patch.object(d._pygame.time, 'get_ticks', return_value=600):
            flash_off = count_glyph_pixels()
        self.assertGreater(flash_on, 0)
        self.assertEqual(flash_off, 0)

        # After the first present, dirty is clear — flash must still redraw.
        def count_canvas_glyph():
            count = 0
            x0 = cw
            for y in range(d._effective_cell_height()):
                for x in range(x0, x0 + cw):
                    if d._canvas.get_at((x, y))[:3] != bg_rgb:
                        count += 1
            return count

        d._dirty = False
        d._compose_full = False
        with mock.patch.object(d._pygame.time, 'get_ticks', return_value=0):
            d.present()
        self.assertGreater(count_canvas_glyph(), 0)
        d._dirty = False
        d._compose_full = False
        with mock.patch.object(d._pygame.time, 'get_ticks', return_value=600):
            d.present()
        self.assertEqual(count_canvas_glyph(), 0)

    def test_mode_resets_text_colours_to_white_on_black(self):
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from mini_basic.config import InterpreterConfig
        from mini_basic.runtime import BASICInterpreter

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        cfg = InterpreterConfig(dialect='bbc', display='pygame')
        interp = BASICInterpreter(cfg)
        interp.new(announce=False)
        interp.execute_immediate('MODE 0')
        interp.execute_immediate('COLOUR 1')
        interp.execute_immediate('COLOUR 129')
        interp.execute_immediate('MODE 0')
        self.assertEqual(interp.text_fg_colour, 7)
        self.assertEqual(interp.text_bg_colour, 0)
        self.assertEqual(interp._display._fg_colour, 7)
        self.assertEqual(interp._display._bg_colour, 0)

    def test_colos_cells_keep_per_cell_background_on_rerender(self):
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from unittest import mock

        from mini_basic.display import PygameDisplay, colour_to_rgb

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        display = PygameDisplay(scale=1)
        display.begin_run()
        display.set_mode(0)
        display.set_colour(1)
        display.write('*')
        display.set_colour(129)
        display.write('*')
        first_bg = colour_to_rgb(0)
        cw = display._effective_cell_width()
        ch_h = display._effective_cell_height()
        sample = (cw - 1, ch_h - 1)
        display._render_graphics_mode()
        before = display._canvas.get_at(sample)[:3]
        display.set_colour(200)
        with mock.patch.object(display._pygame.time, 'get_ticks', return_value=0):
            display._render_graphics_mode()
        with mock.patch.object(display._pygame.time, 'get_ticks', return_value=600):
            display._render_graphics_mode()
        after = display._canvas.get_at(sample)[:3]
        self.assertEqual(before, first_bg)
        self.assertEqual(after, first_bg)
        display.end_run()

    def test_teletext_flash_does_not_bleed_into_previous_cell(self):
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from unittest import mock

        from mini_basic.display import PygameDisplay

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        display = PygameDisplay(scale=1)
        display.begin_run()
        display.set_mode(7)
        display._text[0][0] = ('A', 7, 4, -1, False, False)
        display._text[0][1] = ('B', 1, 0, -1, False, True)
        cw = display._effective_cell_width()
        ch_h = display._effective_cell_height()
        sample_x = cw - 1
        sample_y = ch_h // 2

        def capture_bg_pixel(ticks: int):
            with mock.patch.object(display._pygame.time, 'get_ticks', return_value=ticks):
                display._render_text_mode()
            colour = display._canvas.get_at((sample_x, sample_y))
            return (int(colour[0]), int(colour[1]), int(colour[2]))

        flash_on_pixel = capture_bg_pixel(0)
        flash_off_pixel = capture_bg_pixel(600)
        self.assertEqual(flash_on_pixel, flash_off_pixel)
        self.assertEqual(flash_on_pixel, colour_to_rgb(4))
        display.end_run()

    def test_pygame_capture_after_plot(self):
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from mini_basic.display import PygameDisplay

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        display = PygameDisplay(
            graphics_width=640,
            graphics_height=512,
            scale=1,
        )
        display.begin_run()
        display.set_mode(8)
        display.gcol(0, 3)
        display.plot_code(69, 200, 200)
        display.present()
        pixels = display.capture_framebuffer()
        self.assertGreater(count_framebuffer_pixels(pixels, colour=3), 0)
        width, height, canvas = display.capture_canvas_rgb()
        self.assertEqual((width, height), (640, 512))
        self.assertIn(colour_to_rgb(3), [px for row in canvas for px in row])
        display.end_run()

    def test_vdu_2322_custom_mode_text_grid_and_present(self):
        """squares.bbc: VDU 23,22,512;512;8,16,16,0 must not assert on missing font.

        Custom size without char metrics left 512//80=6px cells (non-MOS) with
        _font still None after MODE 8 open.
        """
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        from mini_basic.display import PygameDisplay

        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        display = PygameDisplay(
            graphics_width=640,
            graphics_height=512,
            text_cols=80,
            text_rows=32,
            scale=1,
        )
        display.begin_run()
        display.set_mode(8)
        display.set_graphics_size(512, 512, charx=8, chary=16, ncols=16, charset=0)
        self.assertEqual(display.graphics_width, 512)
        self.assertEqual(display.graphics_height, 512)
        self.assertEqual(display.text_cols, 64)
        self.assertEqual(display.text_rows, 32)
        self.assertEqual(display._effective_cell_width(), 8)
        display.write('X')
        display.present(force=True)  # previously AssertionError: _font is None
        display.end_run()


if __name__ == '__main__':
    unittest.main()
