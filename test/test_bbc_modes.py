import io
import os
import sys
import unittest
from unittest.mock import patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

from mini_basic.bbc_modes import bbc_mode_spec, bbc_os_scales, teletext_mosaic_pattern
from mini_basic.bbc_graphics import BBCGraphics
from mini_basic.display import PygameDisplay
from mini_basic.runtime import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0]


class BBCModeSpecTests(unittest.TestCase):
    def test_mode1_is_320_square_par(self):
        spec = bbc_mode_spec(1)
        assert spec is not None
        self.assertEqual(spec.gfx_width, 320)
        self.assertEqual(spec.gfx_height, 256)
        self.assertEqual((spec.text_cols, spec.text_rows), (40, 32))
        self.assertEqual((spec.par_w, spec.par_h), (1, 1))
        self.assertEqual(spec.par_display_size(), (320, 256))

    def test_mode0_tall_pixels(self):
        spec = bbc_mode_spec(0)
        assert spec is not None
        self.assertEqual(spec.par_display_size(), (320, 256))

    def test_mode2_wide_pixels(self):
        spec = bbc_mode_spec(2)
        assert spec is not None
        self.assertEqual(spec.par_display_size(), (320, 256))

    def test_mode7_teletext_canvas(self):
        spec = bbc_mode_spec(7)
        assert spec is not None
        self.assertEqual(spec.logical_canvas_size(), (640, 500))
        self.assertEqual(spec.par_display_size(), (640, 500))

    def test_mosaic_pattern_185(self):
        self.assertEqual(teletext_mosaic_pattern(185), 25)

    def test_mode8_bb4w_resolution(self):
        spec = bbc_mode_spec(8)
        assert spec is not None
        self.assertEqual(spec.gfx_width, 640)
        self.assertEqual(spec.gfx_height, 512)
        self.assertEqual((spec.text_cols, spec.text_rows), (80, 32))
        self.assertEqual((spec.par_w, spec.par_h), (1, 1))
        self.assertEqual(spec.par_display_size(), (640, 512))
        self.assertTrue(spec.plot_enabled)

    def test_mode19_vga_square_pixels(self):
        spec = bbc_mode_spec(19)
        assert spec is not None
        self.assertEqual(spec.gfx_width, 640)
        self.assertEqual(spec.gfx_height, 480)
        self.assertEqual((spec.par_w, spec.par_h), (1, 1))
        self.assertEqual(spec.par_display_size(), (640, 480))

    def test_mode9_bb4w_resolution(self):
        spec = bbc_mode_spec(9)
        assert spec is not None
        self.assertEqual(spec.gfx_width, 640)
        self.assertEqual((spec.text_cols, spec.text_rows), (40, 32))

    def test_os_scales_for_mode8_canvas(self):
        self.assertEqual(bbc_os_scales(640, 512), (2, 2))


class BBCModeRuntimeTests(unittest.TestCase):
    def test_mode1_updates_config(self):
        interp = BASICInterpreter()
        interp.execute_immediate('MODE 1')
        self.assertEqual(interp.config.graphics_width, 320)
        self.assertEqual(interp.config.graphics_height, 256)
        self.assertEqual(interp.config.display_cols, 40)
        self.assertEqual(interp.config.display_rows, 32)

    def test_mode0_text_grid(self):
        interp = BASICInterpreter()
        interp.execute_immediate('MODE 0')
        self.assertEqual(interp.config.display_cols, 80)
        self.assertEqual(interp.config.display_rows, 32)
        self.assertEqual(interp.config.graphics_width, 640)

    def test_plot_ignored_in_mode7(self):
        interp = BASICInterpreter(
            config=InterpreterConfig(display='null')
        )
        interp.execute_immediate('MODE 7')
        interp.execute_immediate('PLOT 69,10,10')
        interp.execute_immediate('GCOL 0,1')

    def test_mode7_text_dimensions(self):
        interp = BASICInterpreter()
        interp.execute_immediate('MODE 7')
        self.assertEqual(interp.config.display_cols, 40)
        self.assertEqual(interp.config.display_rows, 25)

    def test_mode8_enables_plotting_and_sets_resolution(self):
        interp = BASICInterpreter()
        interp.execute_immediate('MODE 8')
        self.assertTrue(interp._graphics_plot_enabled())
        self.assertEqual(interp.config.graphics_width, 640)
        self.assertEqual(interp.config.graphics_height, 512)
        self.assertEqual(interp.config.display_cols, 80)
        self.assertEqual(interp.config.display_rows, 32)


class BBCGraphicsDrawTests(unittest.TestCase):
    def test_draw_absolute_plots_foreground_pixel(self):
        gfx = BBCGraphics(640, 512, x_scale=2, y_scale=2)
        gfx.gcol(0, 2)
        gfx.move_absolute(600, 32)
        gfx.draw_absolute(600, 32)
        sx, sy = gfx._to_screen(600, 32)
        self.assertEqual(gfx.pixels[sy][sx], 2)

    def test_draw_relative_offsets_from_cursor(self):
        gfx = BBCGraphics(640, 512, x_scale=2, y_scale=2)
        gfx.gcol(0, 3)
        gfx.move_absolute(100, 100)
        gfx.draw_relative(10, 0)
        sx, sy = gfx._to_screen(110, 100)
        self.assertEqual(gfx.pixels[sy][sx], 3)


class ReplConsoleCleanupTests(unittest.TestCase):
    def test_repl_exit_shuts_down_display_and_restores_console(self):
        interp = BASICInterpreter(
            config=InterpreterConfig(display='null')
        )
        interp._display_live = True
        interp._ansi_console_enabled = True
        buf = io.StringIO()
        # _restore_console only emits CSI on a TTY (avoids breaking redirect tests).
        buf.isatty = lambda: True  # type: ignore[method-assign]
        with patch('sys.stdout', buf):
            interp._restore_console()
        self.assertIn('\x1b[?25h', buf.getvalue())
        interp._shutdown_display(hold=False)
        self.assertFalse(interp._display_live)


class TeletextDisplayTests(unittest.TestCase):
    def test_teletext_colour_and_mosaic(self):
        display = PygameDisplay(scale=1)
        display.set_mode(7)
        display.write(chr(129) + 'RED' + chr(145) + chr(185))
        self.assertEqual(display._text[0][1][1], 1)
        self.assertEqual(display._text[0][5][3], 25)


if __name__ == '__main__':
    unittest.main()
