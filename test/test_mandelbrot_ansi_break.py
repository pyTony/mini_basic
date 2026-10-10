"""mandelbrot_color.bas: EXIT FOR inside WHILE skipped the rest of each row."""
from __future__ import annotations

import io
import os
import re
import sys
import unittest
from contextlib import redirect_stdout

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


def _run(lines, dialect='mini'):
    interp = BASICInterpreter(
        InterpreterConfig(
            dialect=dialect,
            display='none',
            display_locked=True,
        )
    )
    buf = io.StringIO()
    with redirect_stdout(buf):
        for i, line in enumerate(lines, 1):
            interp.set_program_line(i * 10, line)
        interp.run()
    return buf.getvalue()


def _plain(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', text)


class MandelbrotAnsiBreakTests(unittest.TestCase):
    def test_exit_for_inside_while_ends_the_for(self):
        """EXIT FOR leaves FOR X, so only the first pixel of each row prints."""
        out = _run([
            'FOR Y=1 TO 3',
            '  FOR X=1 TO 5',
            '    I=0',
            '    WHILE I<8',
            '      PRINT ".";',
            '      EXIT FOR',
            '      I=I+1',
            '    WEND',
            '    PRINT "X";',
            '  NEXT X',
            '  PRINT',
            'NEXT Y',
        ])
        self.assertNotIn('?', out)
        rows = [ln for ln in _plain(out).splitlines() if ln.strip() != '']
        self.assertEqual(rows, ['.', '.', '.'])

    def test_break_inside_while_continues_the_for(self):
        """BREAK leaves WHILE only; FOR X still visits every X."""
        out = _run([
            'FOR Y=1 TO 2',
            '  FOR X=1 TO 4',
            '    I=0',
            '    WHILE I<8',
            '      PRINT ".";',
            '      BREAK',
            '      I=I+1',
            '    WEND',
            '  NEXT X',
            '  PRINT',
            'NEXT Y',
        ])
        self.assertNotIn('?', out)
        rows = [ln for ln in _plain(out).splitlines() if ln.strip() != '']
        self.assertEqual(rows, ['....', '....'])

    def test_color_listing_declares_mini_dialect(self):
        """BREAK / FG$ are mini, not bbc (Beeb + V)."""
        path = os.path.join(
            _ROOT, 'examples', 'graphics', 'mandelbrot', 'mandelbrot_color.bas',
        )
        with open(path, encoding='utf-8') as handle:
            head = handle.read(200)
        self.assertRegex(head, r'(?i)REM\s+dialect:\s*mini')

    def test_color_listing_row_is_full_width(self):
        """Charset Mandelbrot row is X=-49..29 (79 cells), not one '.'."""
        path = os.path.join(
            _ROOT, 'examples', 'graphics', 'mandelbrot', 'mandelbrot_color.bas',
        )
        interp = BASICInterpreter(
            InterpreterConfig(dialect='mini', display='none', display_locked=True)
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            interp.load(path)
            interp.run()
        plain = _plain(buf.getvalue())
        self.assertNotIn('?', plain)
        rows = [
            ln for ln in plain.splitlines()
            if ln and not ln.startswith('Mandelbrot')
            and ln not in ('Start', 'Finished')
            and 'Time:' not in ln
            and 'Loaded' not in ln
            and 'Program cleared' not in ln
            and 'Graphics' not in ln
            and 'Dialect:' not in ln
        ]
        self.assertGreaterEqual(len(rows), 20)
        widths = [len(ln) for ln in rows]
        self.assertGreaterEqual(min(widths), 70, widths[:3])
        self.assertTrue(any(ch not in ' .' for ln in rows for ch in ln))


if __name__ == '__main__':
    unittest.main()
