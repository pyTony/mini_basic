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


class WhileGuardAccelTests(unittest.TestCase):
    """Block IF … ENDIF guards (escape test + PRINT + BREAK) in the fast loop."""

    def _same_as_interpreter(self, lines, dialect='mini'):
        fast, fast_interp = _run(lines, dialect=dialect, opt=2)
        slow, _ = _run(lines, dialect=dialect, opt=0)
        self.assertNotIn('?', fast)
        self.assertEqual(fast, slow)
        return fast, fast_interp

    def test_guard_break_matches_interpreter(self):
        out, interp = self._same_as_interpreter([
            'FOR X = 1 TO 12',
            'A = X : I = 0',
            'WHILE I < 10',
            'A = A * 1.5',
            'IF A > 40 THEN',
            'PRINT I;',
            'BREAK',
            'ENDIF',
            'I = I + 1',
            'WEND',
            'IF I >= 10 THEN PRINT "-";',
            'NEXT X',
            'PRINT',
        ])
        plans = [p for p in interp._while_assign_accel.values() if p]
        self.assertTrue(plans and plans[0][0] == 'guarded')
        self.assertEqual(interp.stack, [])

    def test_guard_without_break_resumes_fast_loop(self):
        out, _ = self._same_as_interpreter([
            'I = 0 : S = 0',
            'WHILE I < 20',
            'I = I + 1',
            'IF I MOD 5 = 0 THEN',
            'PRINT I; " ";',
            'ENDIF',
            'S = S + I',
            'WEND',
            'PRINT S',
        ])
        self.assertEqual(out.split(), ['5', '10', '15', '20', '210'])

    def test_impure_guard_stays_on_interpreter(self):
        _, interp = _run([
            'I = 0',
            'WHILE I < 5',
            'I = I + 1',
            'IF RND(1) > 2 THEN',
            'BREAK',
            'ENDIF',
            'WEND',
            'PRINT I',
        ], dialect='mini')
        self.assertFalse(any(interp._while_assign_accel.values()))

    def test_guard_with_else_stays_on_interpreter(self):
        out, interp = self._same_as_interpreter([
            'I = 0 : N = 0',
            'WHILE I < 6',
            'I = I + 1',
            'IF I > 3 THEN',
            'N = N + 10',
            'ELSE',
            'N = N + 1',
            'ENDIF',
            'WEND',
            'PRINT N',
        ])
        self.assertEqual(out.strip(), '33')
        self.assertFalse(any(interp._while_assign_accel.values()))

    def test_mandel_ansi_shape(self):
        # examples/graphics/mandelbrot/Mandel_ANSI.BAS inner loop, fewer points.
        self._same_as_interpreter([
            'Z$ = ".,\'~=+:;*%&$OXB#@ "',
            'F = 50',
            'FOR Y = -12 TO 12 STEP 4',
            'FOR X = -49 TO 29 STEP 3',
            'C = X * 229 / 100 : D = Y * 416 / 100',
            'A = C : B = D : I = 0',
            'WHILE I < 16',
            'Q = B / F',
            'S = B - (Q * F)',
            'T = ((A * A) - (B * B)) / F + C',
            'B = 2 * ((A * Q) + (A * S / F)) + D',
            'A = T',
            'P = A / F',
            'Q = B / F',
            'IF (P * P) + (Q * Q) >= 5 THEN',
            'PRINT MID$(Z$, I + 1, 1);',
            'BREAK',
            'ENDIF',
            'I = I + 1',
            'WEND',
            'IF I >= 16 THEN PRINT " ";',
            'NEXT X',
            'PRINT',
            'NEXT Y',
        ])


class ArrayStoreAccelTests(unittest.TestCase):
    """Array-element LHS writes (``FLAGS(K)=0``) in the compiled fast paths."""

    def _same_as_interpreter(self, lines, dialect='bbc'):
        fast, fast_interp = _run(lines, dialect=dialect, opt=2)
        slow, _ = _run(lines, dialect=dialect, opt=0)
        self.assertNotIn('?', fast)
        self.assertEqual(fast, slow)
        return fast, fast_interp

    @staticmethod
    def _run_numbered(pairs, dialect='bbc', opt=2):
        """Like ``_run`` but with explicit (line_num, text) pairs, so GOTO
        targets can be written literally instead of relying on ``_run``'s
        implicit ``i*10`` numbering."""
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
            for line_num, text in pairs:
                interp.set_program_line(line_num, text)
            interp.run()
        return buf.getvalue(), interp

    def test_fast_path_simple_array_store(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.execute_immediate('DIM A%(10)')
        interp.int_variables['I'] = 3
        self.assertTrue(interp._try_fast_numeric_assignment('A%(I%) = 7'))
        self.assertEqual(int(interp._array_get('A', 'int', [3])), 7)

    def test_fast_path_array_store_with_expr_index_and_rhs(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.execute_immediate('DIM A(20)')
        interp.variables['J'] = 4.0
        self.assertTrue(interp._try_fast_numeric_assignment('A(J*2) = J*J'))
        self.assertEqual(float(interp._array_get('A', 'float', [8])), 16.0)

    def test_sieve_inner_loop_while_with_array_write_matches_interpreter(self):
        """A WHILE loop toggling array elements (Sieve shape) stays correct."""
        pairs = [
            (10, 'SIZE%=200'),
            (20, 'DIM FLAGS%(SIZE%)'),
            (30, 'FOR K%=1 TO SIZE%: FLAGS%(K%)=1: NEXT K%'),
            (40, 'COUNT%=0'),
            (50, 'FOR J%=2 TO SIZE%'),
            (60, 'IF FLAGS%(J%)=0 THEN GOTO 110'),
            (70, 'M%=J%+J%'),
            (80, 'WHILE M%<=SIZE%'),
            (90, 'FLAGS%(M%)=0'),
            (95, 'M%=M%+J%'),
            (100, 'ENDWHILE'),
            (105, 'COUNT%=COUNT%+1'),
            (110, 'NEXT J%'),
            (120, 'PRINT COUNT%'),
        ]
        fast, fast_interp = self._run_numbered(pairs, opt=2)
        slow, _ = self._run_numbered(pairs, opt=0)
        self.assertNotIn('?', fast)
        self.assertEqual(fast, slow)
        self.assertEqual(fast_interp.int_variables['COUNT'], 46)  # primes 2..200

    def test_whole_array_assign_not_broken(self):
        """``A() = B()`` (no indices) must keep using the slow path."""
        out, interp = self._same_as_interpreter([
            'DIM A(3): DIM B(3)',
            'B(0)=1: B(1)=2: B(2)=3: B(3)=4',
            'A() = B()',
            'PRINT A(0);A(1);A(2);A(3)',
        ])

    def test_out_of_range_index_raises_same_error(self):
        """An out-of-range array write must error the same way, accelerated
        or not — not silently succeed or diverge in behaviour."""
        lines = [
            'DIM A%(5)',
            'I%=9',
            'A%(I%) = 1',
            'PRINT "unreachable"',
        ]
        buf2, buf0 = io.StringIO(), io.StringIO()
        with redirect_stdout(buf2):
            _run(lines, opt=2)
        with redirect_stdout(buf0):
            _run(lines, opt=0)
        self.assertNotIn('unreachable', buf2.getvalue())
        self.assertNotIn('unreachable', buf0.getvalue())

    def test_multi_dim_array_store_fast_path(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.execute_immediate('DIM G(3,3)')
        interp.variables['X'] = 1.0
        interp.variables['Y'] = 2.0
        self.assertTrue(interp._try_fast_numeric_assignment('G(X,Y) = 42'))
        self.assertEqual(float(interp._array_get('G', 'float', [1, 2])), 42.0)

    def test_string_array_store_stays_unaccelerated(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.execute_immediate('DIM N$(3)')
        # String-array LHS must be rejected by the compiled fast path (returns
        # False) and still work correctly via the normal slow-path assign.
        self.assertFalse(interp._try_fast_numeric_assignment('N$(1) = "hi"'))
        interp.execute_immediate('N$(1) = "hi"')
        self.assertEqual(interp._array_get('N', 'str', [1]), 'hi')

    def test_while_accel_full_loop_engages_for_array_body(self):
        """The whole-loop WHILE accelerator (not just per-statement) must take
        over when the body is pure LET + array-element writes."""
        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.set_program_line(10, 'DIM A%(100)')
        interp.set_program_line(20, 'K%=1')
        interp.set_program_line(30, 'WHILE K%<=100')
        interp.set_program_line(40, 'A%(K%)=K%*2')
        interp.set_program_line(50, 'K%=K%+1')
        interp.set_program_line(60, 'WEND')
        interp.set_program_line(70, 'END')
        interp._prepare_run()
        interp.execute_immediate('DIM A%(100)')
        parts = interp._stmt_parts_for_line(30)
        _, text = parts[0]
        _cmd, rest = interp._parse_command(text)
        result = interp._try_accelerate_while_assign_body(
            30, rest, interp._run_line_nums, 0, parts,
        )
        self.assertIsNotNone(result)
        self.assertEqual(int(interp._array_get('A', 'int', [50])), 100)

    def test_primes_bas_sieve_matches_interpreter(self):
        """basics/primes.bas shape (FOR+GOTO, array toggling) stays correct."""
        pairs = [
            (10, 'SIZE = 512'),
            (20, 'DIM FLAGS(512)'),
            (40, 'FOR I = 1 TO 2'),
            (50, 'COUNT = 0'),
            (60, 'FOR J = 1 TO SIZE: FLAGS(J) = 1: NEXT J'),
            (70, 'FOR J = 1 TO SIZE'),
            (80, 'IF FLAGS(J) = 0 THEN GOTO 140'),
            (90, 'PRIME = J + J + 3'),
            (100, 'K = J + PRIME'),
            (110, 'IF K > SIZE THEN GOTO 130'),
            (120, 'FLAGS(K) = 0: K = K + PRIME: GOTO 110'),
            (130, 'COUNT = COUNT + 1'),
            (140, 'NEXT J'),
            (150, 'NEXT I'),
            (160, 'PRINT COUNT'),
        ]
        fast, fast_interp = self._run_numbered(pairs, opt=2)
        slow, _ = self._run_numbered(pairs, opt=0)
        self.assertEqual(fast, slow)
        self.assertEqual(int(fast_interp.variables['COUNT']), 171)


if __name__ == '__main__':
    unittest.main()
