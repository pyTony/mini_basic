"""squares.bbc performance + munching-squares kernel correctness."""
from __future__ import annotations

import os
import time
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig


class SquaresSpeedTests(unittest.TestCase):
    def test_pure_bitwise_eor_and_compiles(self):
        i = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', optimization_level=2)
        )
        i.int_variables['X'] = 5
        i.int_variables['Y'] = 3
        self.assertEqual(int(i._eval_numeric('(X% EOR Y%) AND 255')), 6)
        ce = i._get_compiled_expr('(X% EOR Y%) AND 255', False)
        self.assertFalse(ce.use_fallback)
        self.assertIsNotNone(ce.code)

    def test_squares_kernel_matches_formula(self):
        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        path = os.path.join(_ROOT, 'examples', 'graphics', 'squares.bbc')
        if not os.path.isfile(path):
            self.skipTest('squares.bbc missing')
        i = BASICInterpreter(
            InterpreterConfig(
                dialect='bbc',
                display='pygame',
                optimization_level=2,
                hold_display_open=False,
            )
        )
        i.load(path)
        # W%=512 uses uniform OS scale 2 (smaller W% yields mixed 1280/1024 scales)
        i.program[130] = 'END'
        i.run()
        gfx = i._display._gfx
        for x in (0, 1, 15, 100, 255, 511):
            for y in (0, 7, 100, 511):
                b = (x ^ y) & 255
                expect = (b, b >> 1, 255 - b)
                sx, sy = gfx._to_screen(2 * x, 2 * y)
                self.assertEqual(
                    gfx.rgb_pixels[sy][sx], expect, f'OS plot 2*{x},2*{y} -> {sx},{sy}',
                )
        i._shutdown_display(hold=False)

    def test_full_squares_under_five_seconds_dummy(self):
        """Regression: full 512×512 must finish well under SDL-class ~5s."""
        os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
        try:
            import pygame  # noqa: F401
        except ImportError:
            self.skipTest('pygame not installed')
        path = os.path.join(_ROOT, 'examples', 'graphics', 'squares.bbc')
        if not os.path.isfile(path):
            self.skipTest('squares.bbc missing')
        i = BASICInterpreter(
            InterpreterConfig(
                dialect='bbc',
                display='pygame',
                optimization_level=2,
                hold_display_open=False,
            )
        )
        i.load(path)
        i.program[130] = 'END'
        t0 = time.perf_counter()
        i.run()
        elapsed = time.perf_counter() - t0
        i._shutdown_display(hold=False)
        self.assertLess(elapsed, 5.0, f'squares took {elapsed:.2f}s (want <5s)')


if __name__ == '__main__':
    unittest.main()
