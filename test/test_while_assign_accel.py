"""WHILE assignment-body accelerator (Mandelbrot inner-loop dispatch)."""
from __future__ import annotations

import io
import os
import sys
import time
import unittest
from contextlib import redirect_stdout

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


def _run(lines, dialect='bbc', opt=2):
    interp = BASICInterpreter(
        InterpreterConfig(
            dialect=dialect,
            display='none',
            display_locked=True,
            optimization_level=opt,
        )
    )
    buf = io.StringIO()
    with redirect_stdout(buf):
        for i, line in enumerate(lines, 1):
            interp.set_program_line(i * 10, line)
        interp.run()
    return buf.getvalue(), interp


class WhileAssignAccelTests(unittest.TestCase):
    def test_assign_only_while_counts(self):
        out, interp = _run([
            'I%=0',
            'WHILE I%<5',
            'I%=I%+1',
            'WEND',
            'PRINT I%',
            'END',
        ])
        self.assertNotIn('?', out)
        self.assertEqual(out.strip().splitlines()[-1].strip(), '5')
        self.assertEqual(int(interp.int_variables['I']), 5)

    def test_endwhile_assign_body(self):
        out, interp = _run([
            'N%=0',
            'WHILE N%<3',
            'N%=N%+1',
            'ENDWHILE',
            'PRINT N%',
        ])
        self.assertNotIn('?', out)
        self.assertEqual(int(interp.int_variables['N']), 3)

    def test_print_in_body_still_interpreted(self):
        out, _ = _run([
            'I=0',
            'WHILE I<3',
            'I=I+1',
            'PRINT I',
            'WEND',
            'END',
        ])
        self.assertNotIn('?', out)
        self.assertEqual(
            [ln.strip() for ln in out.strip().splitlines() if ln.strip()],
            ['1', '2', '3'],
        )

    def test_inline_while_then_print(self):
        out, interp = _run([
            'I%=0',
            'WHILE I%<4:I%=I%+1:WEND:PRINT I%',
            'END',
        ])
        self.assertNotIn('?', out)
        self.assertEqual(int(interp.int_variables['I']), 4)
        self.assertIn('4', out)

    def test_never_entered_while(self):
        out, interp = _run([
            'I%=9',
            'WHILE I%<3',
            'I%=I%+1',
            'WEND',
            'PRINT I%',
        ])
        self.assertNotIn('?', out)
        self.assertEqual(int(interp.int_variables['I']), 9)

    def test_mandelbrot_like_inner_matches_python(self):
        """Tiny Mandelbrot WHILE body must match a Python reference pixel."""
        cx, cy = -0.75, 0.1
        maxiter = 24
        i = 0
        zx = zy = 0.0
        while (i < maxiter) and (zx * zx + zy * zy < 4):
            temp = zx * zx - zy * zy
            zy = 2 * zx * zy + cy
            zx = temp + cx
            i += 1
        out, interp = _run([
            f'CX = {cx}: CY = {cy}',
            'MAXITER% = 24',
            'I% = 0: ZX = 0: ZY = 0',
            'WHILE (I% < MAXITER%) AND (ZX * ZX + ZY * ZY < 4)',
            'TEMP = ZX * ZX - ZY * ZY',
            'ZY = 2 * ZX * ZY + CY',
            'ZX = TEMP + CX',
            'I% = I% + 1',
            'WEND',
            'PRINT I%',
        ])
        self.assertNotIn('?', out)
        self.assertEqual(int(interp.int_variables['I']), i)

    def test_mixed_and_cont_form(self):
        out, interp = _run([
            'I%=0: CONT=-1: MAXITER%=10',
            'ZX=0: ZY=0: CX=-0.5: CY=0',
            'WHILE CONT AND (I% < MAXITER%)',
            'TEMP = ZX * ZX - ZY * ZY',
            'ZY = 2 * ZX * ZY + CY',
            'ZX = TEMP + CX',
            'I% = I% + 1',
            'CONT = (ZX * ZX + ZY * ZY < 4)',
            'ENDWHILE',
            'PRINT I%; CONT',
        ])
        self.assertNotIn('?', out)
        self.assertGreater(int(interp.int_variables['I']), 0)

    def test_opt0_matches_opt2(self):
        lines = [
            'S%=0',
            'K%=0',
            'WHILE K%<20',
            'S%=S%+K%',
            'K%=K%+1',
            'WEND',
            'PRINT S%',
        ]
        out0, i0 = _run(lines, opt=0)
        out2, i2 = _run(lines, opt=2)
        self.assertNotIn('?', out0)
        self.assertNotIn('?', out2)
        self.assertEqual(int(i0.int_variables['S']), int(i2.int_variables['S']))
        self.assertEqual(int(i0.int_variables['K']), 20)

    def test_accelerator_rejects_print_body(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.set_program_line(10, 'I=0')
        interp.set_program_line(20, 'WHILE I<2')
        interp.set_program_line(30, 'I=I+1')
        interp.set_program_line(40, 'PRINT I')
        interp.set_program_line(50, 'WEND')
        interp._prepare_run()
        parts = interp._stmt_parts_for_line(20)
        _, text = parts[0]
        _cmd, rest = interp._parse_command(text)
        result = interp._try_accelerate_while_assign_body(
            20, rest, interp._run_line_nums, 0, parts,
        )
        self.assertIsNone(result)

    def test_parenthesized_comparison_compiles(self):
        """CONT = (ZX*ZX+ZY*ZY < 4) must not fall back to _eval_numeric."""
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        ce = interp._get_compiled_expr('(ZX * ZX + ZY * ZY < 4)', False)
        self.assertFalse(ce.use_fallback)
        self.assertIsNotNone(ce.code)
        interp.variables['ZX'] = 0.5
        interp.variables['ZY'] = 0.5
        self.assertEqual(ce.eval_numeric(interp), -1.0)
        interp.variables['ZX'] = 2.0
        interp.variables['ZY'] = 2.0
        self.assertEqual(ce.eval_numeric(interp), 0.0)

    def test_cont_assign_while_body_accelerates(self):
        out, interp = _run([
            'I%=0 : ZX=0 : ZY=0 : CONT=-1 : MAXITER%=8',
            'WHILE CONT AND (I% < MAXITER%)',
            'TEMP = ZX * ZX - ZY * ZY',
            'ZY = 2 * ZX * ZY + 0.25',
            'ZX = TEMP + -0.5',
            'I% = I% + 1',
            'CONT = (ZX * ZX + ZY * ZY < 4)',
            'ENDWHILE',
            'PRINT I%;CONT',
        ])
        self.assertNotIn('?', out)
        self.assertEqual(interp._while_assign_accel.get(20) is not False, True)
        self.assertTrue(
            any(v not in (False, None) for v in interp._while_assign_accel.values())
        )

    def test_accelerator_accepts_assign_body(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.set_program_line(10, 'I%=0')
        interp.set_program_line(20, 'WHILE I%<3')
        interp.set_program_line(30, 'I%=I%+1')
        interp.set_program_line(40, 'WEND')
        interp.set_program_line(50, 'END')
        interp._prepare_run()
        parts = interp._stmt_parts_for_line(20)
        _, text = parts[0]
        _cmd, rest = interp._parse_command(text)
        result = interp._try_accelerate_while_assign_body(
            20, rest, interp._run_line_nums, 0, parts,
        )
        self.assertIsNotNone(result)
        self.assertEqual(int(interp.int_variables['I']), 3)

    def test_div0_assignment_uses_on_error(self):
        """Compiled LET must not swallow 1/0; ON ERROR / ERR still run."""
        out, _ = _run([
            'ON ERROR PRINT "E";ERR: END',
            'A=1/0',
            'PRINT "no"',
        ])
        self.assertNotIn('no', out.lower())
        self.assertIn('E', out)

    def test_assign_fast_path_skips_system_vars(self):
        """_bigint / _optimization_level must use _assign, not compiled LET."""
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        self.assertFalse(interp._try_fast_numeric_assignment('_optimization_level = 1'))
        self.assertFalse(interp._try_fast_numeric_assignment('LET _bigint = 0'))
        interp.execute_immediate('_optimization_level = 1')
        self.assertEqual(interp.config.optimization_level, 1)

    def test_assign_fast_path_simple_let(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.variables['ZX'] = 2.0
        self.assertTrue(interp._try_fast_numeric_assignment('TEMP = ZX * ZX'))
        self.assertAlmostEqual(float(interp.variables['TEMP']), 4.0)

    def test_four_scanline_compute_faster_than_opt0(self):
        """Small Mandelbrot WHILE nest: compiled path matches opt=0 and is faster."""
        src = [
            'XMIN=-2.25: XMAX=0.75',
            'YMIN=-1.35: YMAX=1.35',
            'MAXITER%=24',
            'NX%=80: NY%=8: ST%=4',
            'S%=0',
            'FOR PY%=0 TO NY%-ST% STEP ST%',
            'CY=YMIN+(PY%/(NY%-1))*(YMAX-YMIN)',
            'FOR PX%=0 TO NX%-ST% STEP ST%',
            'CX=XMIN+(PX%/(NX%-1))*(XMAX-XMIN)',
            'I%=0: ZX=0: ZY=0',
            'WHILE (I%<MAXITER%) AND (ZX*ZX+ZY*ZY<4)',
            'TEMP=ZX*ZX-ZY*ZY',
            'ZY=2*ZX*ZY+CY',
            'ZX=TEMP+CX',
            'I%=I%+1',
            'WEND',
            'S%=S%+I%',
            'NEXT PX%',
            'NEXT PY%',
            'PRINT S%',
        ]

        def timed(opt):
            t0 = time.perf_counter()
            out, interp = _run(src, opt=opt)
            dt = time.perf_counter() - t0
            self.assertNotIn('?', out)
            return dt, int(interp.int_variables['S'])

        dt0, s0 = timed(0)
        dt2, s2 = timed(2)
        self.assertEqual(s0, s2)
        # Dispatch leftover: opt=2 must not be slower than the interpreter path.
        self.assertLess(dt2, dt0 * 1.15)


if __name__ == '__main__':
    unittest.main()
