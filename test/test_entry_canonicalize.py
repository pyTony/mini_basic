"""Phase 1 entry-time line canonicalize (dual-normalize with runtime unglue)."""
from __future__ import annotations

import os
import sys
import unittest

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0]


class EntryCanonicalizeTests(unittest.TestCase):
    def _bbc(self) -> BASICInterpreter:
        return BASICInterpreter(
            InterpreterConfig(
                dialect='bbc',
                display='none',
                display_locked=True,
                hold_display_open=False,
                optimization_level=2,
            )
        )

    def test_idempotent(self):
        i = self._bbc()
        samples = [
            'PRINTTAB(0);"x"',
            'FORI%=1TO10STEP2',
            'A=TAN10+ABS-3',
            'D%=INKEY1',
            'DEFPROC4',
            'MODE5',
            'PRINT "Original"',
            "REM TAN10 stays comment",
            "A$ = \"TAN10\"",
        ]
        for s in samples:
            once = i.canonicalize_program_line(s)
            twice = i.canonicalize_program_line(once)
            self.assertEqual(once, twice, msg=repr(s))

    def test_set_program_line_stores_printtab_split(self):
        i = self._bbc()
        i.set_program_line(10, 'PRINTTAB(5);"hi"')
        self.assertIn('PRINT TAB', i.program[10].upper())
        self.assertNotIn('PRINTTAB', i.program[10].upper().replace('PRINT TAB', ''))

    def test_set_program_line_monadic_glue(self):
        i = self._bbc()
        i.set_program_line(10, 'X=TAN10')
        self.assertIn('TAN(10)', i.program[10])
        i.set_program_line(20, 'Y=ABS-3')
        self.assertIn('ABS(-3)', i.program[20])

    def test_rem_not_unglued(self):
        i = self._bbc()
        i.set_program_line(10, 'REM TAN10 is note')
        self.assertIn('TAN10', i.program[10])
        self.assertNotIn('TAN(10)', i.program[10])

    def test_string_literal_not_unglued(self):
        i = self._bbc()
        i.set_program_line(10, 'A$="TAN10"')
        self.assertIn('"TAN10"', i.program[10])

    def test_load_path_uses_set_program_line(self):
        """LOAD goes through set_program_line → canonicalize."""
        import tempfile

        i = self._bbc()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 't.bas')
            with open(path, 'w', encoding='utf-8') as f:
                f.write('10 PRINTTAB(0);"z"\n20 END\n')
            i.working_dir = tmp
            self.assertTrue(i.load('t.bas', announce=False))
            self.assertIn('PRINT TAB', i.program[10].upper())

    def test_phase2_monadic_fast_reject(self):
        """Already-parenthesized monadic forms skip full unglue work."""
        i = self._bbc()
        self.assertFalse(i._expr_may_need_monadic_unglue('TAN(10)+ABS(-3)'))
        self.assertFalse(i._expr_may_need_monadic_unglue('I% < MAXITER%'))
        self.assertTrue(i._expr_may_need_monadic_unglue('TAN10'))
        self.assertTrue(i._expr_may_need_monadic_unglue('NOT0'))
        # Direct eval still works (safety net when glue remains).
        import math
        self.assertAlmostEqual(float(i._eval_numeric('TAN10')), math.tan(10.0), places=5)

    def test_phase2b_bbc_dialect_fast_reject(self):
        """Stored canonical forms skip _normalize_bbc_dialect_line; glue still peels."""
        i = self._bbc()
        self.assertFalse(i._line_may_need_bbc_dialect_normalize('PRINT TAB(0);"x"'))
        self.assertFalse(i._line_may_need_bbc_dialect_normalize('FOR I%=1 TO 10 STEP 2'))
        self.assertFalse(i._line_may_need_bbc_dialect_normalize('MODE 5'))
        self.assertTrue(i._line_may_need_bbc_dialect_normalize('PRINTTAB(0);"x"'))
        self.assertTrue(i._line_may_need_bbc_dialect_normalize('FORI%=1TO10'))
        self.assertTrue(i._line_may_need_bbc_dialect_normalize('MODE5'))
        self.assertTrue(i._line_may_need_bbc_dialect_normalize('DEFPROC4'))
        # Digit inside an identifier is not FOR glue (a0to+1 ≠ a0 TO +1).
        self.assertFalse(i._line_may_need_bbc_dialect_normalize('a0to=a0to+1'))
        self.assertFalse(i._line_may_need_bbc_dialect_normalize('i00to=i00to+1'))
        # Safety net: _parse_command still unglues residual PRINTTAB.
        cmd, rest = i._parse_command('PRINTTAB(5);"hi"')
        self.assertEqual(cmd, 'PRINT')
        self.assertTrue(rest.upper().startswith('TAB'))

    def test_ident_digit_to_not_split(self):
        """Hypothesis vars like a0to must increment; 1TO10 still unglues."""
        i = self._bbc()
        self.assertEqual(i.canonicalize_program_line('a0to=a0to+1'), 'a0to=a0to+1')
        self.assertEqual(i.canonicalize_program_line('i00to=i00to+1'), 'i00to=i00to+1')
        self.assertIn(' TO ', i.canonicalize_program_line('FOR I=1TO10'))
        self.assertIn(' TO ', i.canonicalize_program_line('FOR I%=0TO20'))
        # welcome.bbc detokenize: FOR J0%=1TO M8
        self.assertIn(' TO ', i.canonicalize_program_line('FOR J0%=1TO M8'))
        self.assertIsNotNone(i._match_for_clause('J0%=1TO M8'))

    def test_phase2c_operator_normalize_fast_reject(self):
        """Pure arithmetic skips AND/MOD rewrite; glued/word ops still translate."""
        i = self._bbc()
        self.assertFalse(i._expr_may_need_operator_normalize('ZX*ZX+ZY*ZY<4'))
        self.assertFalse(i._expr_may_need_operator_normalize('I%+1'))
        self.assertFalse(i._expr_may_need_operator_normalize('(1+2)*3'))
        self.assertTrue(i._expr_may_need_operator_normalize('A%AND1'))
        self.assertTrue(i._expr_may_need_operator_normalize('10MOD3'))
        self.assertTrue(i._expr_may_need_operator_normalize('CONT AND 1'))
        self.assertTrue(i._expr_may_need_operator_normalize('X^2'))
        self.assertEqual(int(i._eval_numeric('10MOD3')), 1)
        self.assertEqual(int(i._eval_numeric('5AND1')), 1)
        self.assertEqual(int(i._eval_numeric('2^3')), 8)

    def test_load_and_repl_numbered_store_the_same_text(self):
        """LOAD and REPL ``10 …`` both go through set_program_line."""
        import tempfile

        glued = 'PRINTTAB(0);"x":FOR I%=1TO10:X=TAN10'
        loaded = self._bbc()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 't.bas')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write(f'10 {glued}\n20 END\n')
            loaded.working_dir = tmp
            self.assertTrue(loaded.load('t.bas', announce=False))
        typed = self._bbc()
        typed.set_program_line(10, glued)
        self.assertEqual(loaded.program[10], typed.program[10])
        self.assertIn('PRINT TAB', typed.program[10].upper())
        self.assertIn(' TO ', typed.program[10])
        self.assertIn('TAN(10)', typed.program[10])

    def test_immediate_uses_same_canonicalize_as_program_entry(self):
        """Direct-mode statements run the same canonicalize as LOAD."""
        i = self._bbc()
        glued = 'X=TAN10+ABS-3'
        i.execute_immediate(glued)
        stored = i.canonicalize_program_line(glued)
        self.assertIn('TAN(10)', stored)
        self.assertIn('ABS(-3)', stored)
        j = self._bbc()
        j.set_program_line(10, glued)
        j.set_program_line(20, 'END')
        import math

        expected = math.tan(10.0) + abs(-3)
        self.assertAlmostEqual(float(i.variables.get('X', i.int_variables.get('X', 0))), expected, places=5)
        buf_run = __import__('io').StringIO()
        from contextlib import redirect_stdout

        with redirect_stdout(buf_run):
            j.run()
        self.assertAlmostEqual(float(j.variables.get('X', j.int_variables.get('X', 0))), expected, places=5)

    def test_wend_stored_as_endwhile_folded_at_parse(self):
        """Entry stores BBCSDL ENDWHILE; execute still folds to WEND."""
        i = self._bbc()
        i.set_program_line(10, 'WEND')
        self.assertEqual(i.program[10].strip().upper(), 'ENDWHILE')
        cmd, _rest = i._parse_command(i.program[10])
        self.assertEqual(cmd, 'WEND')

    def test_and_keyword_stays_basic_in_store(self):
        """AND→& is eval translation, not entry glue — cannot peel from RUN."""
        i = self._bbc()
        stored = i.canonicalize_program_line('IF A% AND 1 THEN END')
        self.assertIn('AND', stored.upper())
        self.assertNotIn('&', stored)
        i.int_variables['A'] = 5
        self.assertEqual(int(i._eval_numeric('A% AND 1')), 1)

    def test_operator_normalize_after_int_suffix_substitution(self):
        """A%AND1 becomes 5AND1 after subst; eval must still split (welcome/Clock)."""
        i = self._bbc()
        i.int_variables['A'] = 5
        self.assertEqual(int(i._eval_numeric('A%AND1')), 1)
        self.assertTrue(i._expr_may_need_operator_normalize('A%AND1'))
        # Spaced AND still needs eval translation (AND → &), so peel is blocked.
        self.assertTrue(i._expr_may_need_operator_normalize('A% AND 1'))


if __name__ == '__main__':
    unittest.main()
