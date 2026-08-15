import io
import os
import re
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]

_CORPUS_DIR = os.path.join(_ROOT, 'test', 'corpus', 'agon')


def _load_numbered_program(path: str):
    program = {}
    with open(path, encoding='utf-8', errors='replace') as handle:
        for raw in handle:
            line = raw.rstrip('\n\r')
            match = re.match(r'^\s*(\d+)\s+(.*)$', line)
            if match:
                program[int(match.group(1))] = match.group(2)
    return program


def _run_bas_file(path: str, *, working_dir: str | None = None) -> str:
    interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none', display_locked=True))
    if working_dir:
        interp.working_dir = working_dir
    interp.program = _load_numbered_program(path)
    buf = io.StringIO()
    interp._program_stdout = buf
    interp.run()
    return buf.getvalue()


class AgonCorpusTests(unittest.TestCase):
    def test_benchm_regression(self):
        for index in range(1, 10):
            path = os.path.join(_CORPUS_DIR, f'benchm{index}.bas')
            print(f'  agon corpus: benchm{index}.bas', flush=True)
            with self.subTest(bench=f'benchm{index}'):
                self.assertTrue(os.path.isfile(path), msg=path)
                with tempfile.TemporaryDirectory() as tmp:
                    out = _run_bas_file(path, working_dir=tmp)
                if index == 9:
                    self.assertIn('Write:', out)
                    self.assertIn('Read:', out)
                    self.assertNotIn('? CLOSE# channel', out)
                    self.assertNotIn('? INPUT# channel', out)
                    self.assertFalse(os.path.exists(os.path.join(tmp, 'file.txt')))
                else:
                    self.assertIn('S', out)
                    self.assertIn('E', out)

    def test_life_runs_one_generation(self):
        path = os.path.join(_CORPUS_DIR, 'life.bas')
        self.assertTrue(os.path.isfile(path))
        program = _load_numbered_program(path)
        program[490] = 'END'
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none', display_locked=True))
        interp.program = program
        buf = io.StringIO()
        interp._program_stdout = buf
        interp.run()
        out = buf.getvalue()
        self.assertIn('Generation:', out)
        self.assertNotIn('? Unknown:', out)
        self.assertNotIn('? IF error', out)

    def test_life_runs_three_generations(self):
        path = os.path.join(_CORPUS_DIR, 'life.bas')
        program = _load_numbered_program(path)
        program[490] = 'IF G%>=3 THEN END ELSE GOTO 250'
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none', display_locked=True))
        interp.program = program
        buf = io.StringIO()
        interp._program_stdout = buf
        interp.run()
        out = buf.getvalue()
        plain = re.sub(r'\x1b\[[0-9;?]*[A-Za-z]', '', out)
        self.assertIn('Generation:', plain)
        self.assertNotIn('? ', plain)


class AgonFeatureTests(unittest.TestCase):
    def run_lines(self, lines):
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none', display_locked=True))
        for line_num, statement in lines:
            interp.program[line_num] = statement
        buf = io.StringIO()
        interp._program_stdout = buf
        interp.run()
        return buf.getvalue()

    def test_power_operator(self):
        out = self.run_lines([
            (10, 'PRINT 5^2'),
            (20, 'END'),
        ])
        self.assertIn('25', out)

    def test_negative_base_power_then_sqr(self):
        """x^2 with x=-1 must be (-1)**2, not Python -1**2 (world.bbc SQR)."""
        out = self.run_lines([
            (10, 'X=-1: Y=0'),
            (20, 'PRINT SQR(X^2+Y^2)'),
            (30, 'END'),
        ])
        self.assertNotIn('nonnegative', out)
        self.assertIn('1', out.strip().split()[0])

    def test_str_dollar(self):
        out = self.run_lines([
            (10, 'PRINT STR$(42)'),
            (20, 'END'),
        ])
        self.assertIn('42', out)

    def test_hex_and_bin_strings(self):
        """STR$~ (BBC) / HEX$ (MS/QB64) / BIN$ (Locomotive/QB64)."""
        out = self.run_lines([
            (10, 'PRINT HEX$(255);" ";BIN$(255)'),
            (20, 'PRINT HEX$(255, 4);" ";BIN$(7, 8)'),
            (30, 'END'),
        ])
        self.assertIn('FF', out)
        self.assertIn('11111111', out)
        self.assertIn('00FF', out)
        self.assertIn('00000111', out)
        bare = self.run_lines([
            (10, 'PRINT HEX$255;" ";BIN$15'),
            (20, 'END'),
        ])
        self.assertIn('FF', bare)
        self.assertIn('1111', bare)

    def test_print_tilde_hex(self):
        """BBC PRINT ~n prints hex; later numeric items stay hex."""
        out = self.run_lines([
            (10, 'PRINT ~255'),
            (20, 'PRINT ~10, 11'),
            (30, 'END'),
        ])
        lines = [ln.strip() for ln in out.replace('\r', '').split('\n') if ln.strip()]
        self.assertTrue(any(ln == 'FF' or ln.endswith('FF') for ln in lines), out)
        self.assertIn('A', out)
        self.assertIn('B', out)
        bbc = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
        bbc.set_program_line(10, 'PRINT STR$~(255);" ";HEX$(255)')
        bbc.set_program_line(20, 'END')
        buf = io.StringIO()
        bbc._program_stdout = buf
        bbc.run()
        self.assertEqual(buf.getvalue().strip().split(), ['FF', 'FF'])

    def test_compact_if_vdu(self):
        out = self.run_lines([
            (10, 'C%=1'),
            (20, 'IF C% VDU 42 ELSE VDU 32'),
            (30, 'END'),
        ])
        self.assertIn('*', out)

    def test_compact_if_array_element_assignment(self):
        """life.bas: IF RND(1)>=.7 N%(I%,J%)=1 ELSE N%(I%,J%)=0"""
        out = self.run_lines([
            (10, 'DIM N%(2,2)'),
            (20, 'I%=1:J%=1'),
            (30, 'IF RND(1)>=.7 N%(I%,J%)=1 ELSE N%(I%,J%)=0'),
            (40, 'PRINT N%(1,1)'),
            (50, 'END'),
        ])
        self.assertIn('0', out)
        self.assertNotIn('? IF error', out)

    def test_on_error_off(self):
        out = self.run_lines([
            (10, 'ON ERROR GOTO 100'),
            (20, 'ON ERROR OFF'),
            (30, 'END'),
            (100, 'PRINT "trap"'),
        ])
        self.assertNotIn('trap', out)

    def test_oscli_erase(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, 'file.txt')
            with open(target, 'w', encoding='utf-8') as handle:
                handle.write('x')
            interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none', display_locked=True))
            interp.working_dir = tmp
            interp.program = {10: 'OSCLI("ERASE file.txt")', 20: 'END'}
            buf = io.StringIO()
            interp._program_stdout = buf
            interp.run()
            self.assertFalse(os.path.isfile(target))

    def test_tab_xy_emits_ansi(self):
        out = self.run_lines([
            (10, 'PRINT TAB(3,2);"X"'),
            (20, 'END'),
        ])
        self.assertIn('\033[3;4H', out)
        self.assertIn('X', out)

    def test_mode_silent(self):
        out = self.run_lines([
            (10, 'MODE 8'),
            (20, 'PRINT "ok"'),
            (30, 'END'),
        ])
        self.assertIn('ok', out)
        self.assertNotIn('? Unknown', out)

    def test_cls_emits_clear_sequence(self):
        out = self.run_lines([
            (10, 'CLS'),
            (20, 'PRINT "ok"'),
            (30, 'END'),
        ])
        self.assertIn('\x1b[2J\x1b[H', out)
        self.assertIn('ok', out)

    def test_rnd_one_is_fraction(self):
        out = self.run_lines([
            (10, 'PRINT RND(1) < 1'),
            (20, 'END'),
        ])
        self.assertIn('-1', out)

    def test_life_init_is_sparse(self):
        path = os.path.join(_CORPUS_DIR, 'life.bas')
        program = _load_numbered_program(path)
        program[140] = 'END'
        program = {k: v for k, v in program.items() if k <= 140}
        interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none', display_locked=True))
        interp.program = program
        buf = io.StringIO()
        interp._program_stdout = buf
        interp.run()
        storage = interp.array_storage.get(('N', 'int'))
        self.assertIsNotNone(storage)
        _, _, data = storage
        if data and isinstance(data[0], list):
            live = sum(1 for row in data for value in row if value)
            total = sum(len(row) for row in data)
        else:
            live = sum(1 for value in data if value)
            total = len(data)
        self.assertGreater(total, 100)
        self.assertLess(live, total * 0.6)

    def test_wait_pauses(self):
        start = time.perf_counter()
        out = self.run_lines([
            (10, 'WAIT 50'),
            (20, 'PRINT "done"'),
            (30, 'END'),
        ])
        elapsed = time.perf_counter() - start
        self.assertGreaterEqual(elapsed, 0.04)
        self.assertIn('done', out)

    def test_wait_zero_is_instant(self):
        start = time.perf_counter()
        self.run_lines([
            (10, 'WAIT 0'),
            (20, 'END'),
        ])
        self.assertLess(time.perf_counter() - start, 0.05)

    def test_vdu_12_clears(self):
        out = self.run_lines([
            (10, 'VDU 12'),
            (20, 'PRINT "ok"'),
            (30, 'END'),
        ])
        self.assertIn('\x1b[2J\x1b[H', out)
        self.assertIn('ok', out)



    def test_bbc_file_variable_syntax(self):
        with tempfile.TemporaryDirectory() as tmp:
            interp = BASICInterpreter(InterpreterConfig(dialect='mini', display='none', display_locked=True))
            interp.working_dir = tmp
            interp.program = {
                10: 'f=OPENOUT "data.txt"',
                20: 'PRINT #f, "Hello World " + STR$(1)',
                30: 'CLOSE#f',
                40: 'f=OPENIN "data.txt"',
                50: 'INPUT#f, S$',
                60: 'CLOSE#f',
                70: 'PRINT S$',
                80: 'END',
            }
            buf = io.StringIO()
            interp._program_stdout = buf
            interp.run()
            out = buf.getvalue()
            self.assertIn('Hello World 1', out)
            self.assertNotIn('? CLOSE# channel', out)
            self.assertNotIn('? INPUT# channel', out)


if __name__ == '__main__':
    unittest.main()