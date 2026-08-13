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

    def test_comparison_assignment_uses_compiled_numeric(self):
        """CONT = (ZX*ZX+ZY*ZY < 4) must eval compiled -1/0, not boolean parser."""
        i = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', optimization_level=2)
        )
        i.variables['ZX'] = 0.0
        i.variables['ZY'] = 0.0
        expr = 'ZX * ZX + ZY * ZY < 4'
        ce = i._get_compiled_expr(expr, is_condition=False)
        self.assertFalse(ce.use_fallback, 'expected compiled path for numeric comparison')
        self.assertIsNotNone(ce.code)
        self.assertEqual(int(ce.eval_numeric(i)), -1)
        self.assertEqual(int(i._eval_numeric(expr)), -1)
        i.variables['ZX'] = 3.0
        self.assertEqual(int(ce.eval_numeric(i)), 0)
        self.assertEqual(int(i._eval_numeric('(ZX * ZX + ZY * ZY < 4)')), 0)
        # Mixed AND as a numeric value (same BBC -1/0) also stays compiled.
        i.variables['CONT'] = -1.0
        i.int_variables['I'] = 0
        mixed = 'CONT AND (I% < 16)'
        ce_m = i._get_compiled_expr(mixed, is_condition=False)
        self.assertFalse(ce_m.use_fallback)
        self.assertEqual(int(ce_m.eval_numeric(i)), -1)

    def test_mixed_boolean_cont_and_comparison_compiles(self):
        """WHILE CONT AND (I% < N) must compile (not recursive boolean fallback)."""
        i = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', optimization_level=2)
        )
        i.variables['CONT'] = -1.0
        i.int_variables['I'] = 0
        expr = 'CONT AND (I% < 16)'
        ce = i._get_compiled_expr(expr, is_condition=True)
        self.assertFalse(ce.use_fallback, 'expected compiled path for mixed AND+compare')
        self.assertIsNotNone(ce.code)
        self.assertTrue(ce.eval_condition(i))
        self.assertTrue(i._eval_condition(expr))
        i.int_variables['I'] = 20
        self.assertFalse(ce.eval_condition(i))
        self.assertFalse(i._eval_condition(expr))
        i.variables['CONT'] = 0.0
        i.int_variables['I'] = 0
        self.assertFalse(i._eval_condition(expr))
        # Chain of comparisons (animal-style)
        i.variables['A'] = 1.0
        i.variables['B'] = 2.0
        i.variables['C'] = 3.0
        chain = 'A < B AND B < C'
        ce2 = i._get_compiled_expr(chain, is_condition=True)
        self.assertFalse(ce2.use_fallback)
        self.assertTrue(ce2.eval_condition(i))
        # Pure bitwise still compiles (no regression)
        i.int_variables['X'] = 5
        i.int_variables['Y'] = 3
        ce3 = i._get_compiled_expr('(X% EOR Y%) AND 255', False)
        self.assertFalse(ce3.use_fallback)
        self.assertEqual(int(ce3.eval_numeric(i)), 6)

    def test_mixed_boolean_while_loop_fast_path(self):
        """Tiny WHILE with CONT AND (I%<N) must terminate correctly under opt=2."""
        i = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', optimization_level=2)
        )
        lines = [
            (10, 'CONT = TRUE'),
            (20, 'I% = 0'),
            (30, 'N% = 1000'),
            (40, 'WHILE CONT AND (I% < N%)'),
            (50, 'I% = I% + 1'),
            (60, 'ENDWHILE'),
            (70, 'PRINT I%'),
            (80, 'END'),
        ]
        for ln, st in lines:
            i.program[ln] = st
        t0 = time.perf_counter()
        # capture print
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            i.run()
        elapsed = time.perf_counter() - t0
        self.assertEqual(buf.getvalue().strip(), '1000')
        # 1000 iterations of compiled condition should be well under a second
        self.assertLess(elapsed, 2.0, f'WHILE mixed boolean took {elapsed:.3f}s')

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
