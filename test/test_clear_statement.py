"""CLEAR [stringspace[,stack]]: forget all variables and arrays.

MS BASIC (mits / commodore) and BBC BASIC both have it; Super Star Trek
starts with ``5 CLEAR 1000``. The size arguments only matter to a real
machine's memory map, so they are evaluated and ignored. DEF FN definitions
and the program survive; BBC BASIC keeps the resident integers A%..Z%.
"""
from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx, pytest.mark.timeout(15)]


def _run(dialect: str, src: str) -> tuple[str, str]:
    interp = BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )
    for raw in src.strip().splitlines():
        num, _, text = raw.partition(' ')
        interp.set_program_line(int(num), text)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        interp.run()
    return out.getvalue(), err.getvalue()


class ClearStatementTests(unittest.TestCase):

    def test_clear_forgets_variables_and_arrays_ms(self):
        for dialect in ('mits', 'commodore'):
            out, err = _run(
                dialect,
                '10 A=5:B$="X":DIM C(3):C(1)=7\n'
                '20 CLEAR 1000\n'
                '30 PRINT A;B$;"|";\n'
                '40 DIM C(2):PRINT C(1)\n',
            )
            self.assertEqual(err, '', msg=dialect)
            self.assertEqual(out.strip(), '0 | 0', msg=(dialect, out))

    def test_clear_without_and_with_size_arguments(self):
        for dialect in ('mits', 'commodore', 'mini', 'bbc'):
            for stmt in ('CLEAR', 'CLEAR 1000', 'CLEAR ,500', 'CLEAR 1000,100'):
                out, err = _run(dialect, f'10 {stmt}\n20 PRINT "OK"\n')
                self.assertEqual(err, '', msg=(dialect, stmt, err))
                self.assertIn('OK', out, msg=(dialect, stmt))

    def test_clear_keeps_program_and_def_fn(self):
        for dialect in ('mits', 'mini'):
            out, err = _run(
                dialect,
                '10 DEF FNA(X)=X*2\n20 CLEAR\n30 PRINT FNA(4)\n',
            )
            self.assertEqual(out.strip(), '8', msg=(dialect, err))

    def test_clear_as_first_line_then_normal_program(self):
        out, err = _run(
            'mits',
            '5 CLEAR 1000\n10 REM TEST\n20 DIM G(8,8):G(1,1)=3\n30 PRINT G(1,1)\n',
        )
        self.assertEqual((out.strip(), err), ('3', ''))

    def test_bbc_clear_keeps_resident_integers(self):
        out, err = _run(
            'bbc',
            '10 A%=5:B%=7:X=9:Y$="S"\n20 CLEAR\n30 PRINT A%;" ";B%;" ";X;" [";Y$;"]"\n',
        )
        self.assertEqual(err, '')
        self.assertEqual(out.split(), ['5', '7', '0', '[]'])

    def test_clear_is_not_a_variable_prefix(self):
        # CLEARANCE is an ordinary variable name in mini.
        out, err = _run('mini', '10 CLEARANCE=3\n20 PRINT CLEARANCE\n')
        self.assertEqual((out.strip(), err), ('3', ''))


if __name__ == '__main__':
    unittest.main()
