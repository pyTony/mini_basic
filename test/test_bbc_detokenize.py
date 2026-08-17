"""BBC binary detokenize — Wilson + Russell (phase1 regression)."""
from __future__ import annotations

import os
import sys
import unittest

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic.bbc_detokenize import (
    bbc_binary_to_source,
    detect_bbc_binary_format,
    detokenize_line_body,
    parse_russell_program,
)
from mini_basic import InterpreterConfig
from mini_basic.runtime import BASICInterpreter

_WHEEL_BBC = os.path.join(_ROOT, 'examples', 'graphics', 'wheel.bbc')

pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]


def _russell_record(line_num: int, body: bytes) -> bytes:
    """One Russell line record: [len][lo][hi][body...][0x0D]."""
    inner = bytes([line_num & 0xFF, (line_num >> 8) & 0xFF]) + body + b'\r'
    return bytes([len(inner) + 1]) + inner


# Synthetic program: CASE/WHEN + CIRCLE FILL + ORIGIN (Russell tokens)
# CASE=0xC8 WHEN=0xC9 OF=0xCA ENDCASE=0xCB OTHERWISE=0xCC
# DIV=0x81 MOD=0x83 CIRCLE=0x01 FILL=0x03 ORIGIN=0x05 MODE=0xEB OFF=0x87
def _synthetic_russell_wheel_snippet() -> bytes:
    lines = [
        _russell_record(70, bytes([0xEB, 0x20, 0x38, 0x3A, 0x87, 0x3A, 0x05, 0x20]) + b'640,512'),
        _russell_record(180, bytes([0x01, 0x03, 0x20]) + b'x1%,y1%,80'),
        _russell_record(350, bytes([0xC8, 0x20]) + b'N% ' + bytes([0x81]) + b' 256 ' + bytes([0xCA])),
        _russell_record(360, bytes([0xC9, 0x20]) + b'0: r%=255'),
        _russell_record(420, bytes([0xCC, 0x20]) + b'r%=128'),
        _russell_record(430, bytes([0xCB])),
    ]
    return b''.join(lines) + b'\r\x00\xff\xff'


class BBCTokenizedLoadTests(unittest.TestCase):
    def test_detect_wilson_format(self):
        data = b'\r\x00\n\x1b\xf4 test\r\x00\x14!\xf4 x\r\xff'
        self.assertEqual(detect_bbc_binary_format(data), 'wilson')

    def test_detect_russell_trailer(self):
        data = _synthetic_russell_wheel_snippet()
        self.assertEqual(detect_bbc_binary_format(data), 'russell')

    def test_detokenize_rem(self):
        body = bytes([0xF4]) + b' hello' + bytes([0x0D])
        self.assertEqual(detokenize_line_body(body), 'REM hello')

    def test_russell_case_and_circle_fill_detokenize(self):
        """Russell table: CASE/WHEN not LOAD/LIST; CIRCLE FILL; ORIGIN."""
        data = _synthetic_russell_wheel_snippet()
        self.assertEqual(detect_bbc_binary_format(data), 'russell')
        joined = '\n'.join(text for _, text in parse_russell_program(data))
        self.assertIn('CASE N% DIV 256 OF', joined)
        self.assertIn('WHEN 0:', joined)
        self.assertIn('OTHERWISE', joined)
        self.assertIn('ENDCASE', joined)
        self.assertNotIn('LOAD N%', joined)
        self.assertIn('CIRCLE FILL x1%,y1%,80', joined)
        self.assertIn('MODE 8:OFF:ORIGIN 640,512', joined)

    def test_load_wheel_bbc_if_present(self):
        """Text or binary wheel.bbc must load; binary must show CASE not LOAD."""
        if not os.path.isfile(_WHEEL_BBC):
            self.skipTest('wheel.bbc not present')
        with open(_WHEEL_BBC, 'rb') as f:
            data = f.read()
        fmt = detect_bbc_binary_format(data)
        interp = BASICInterpreter()
        interp.load(_WHEEL_BBC, announce=False)
        self.assertTrue(interp.program, 'program should load')
        joined = '\n'.join(interp.program[n] for n in sorted(interp.program)).upper()
        if fmt == 'russell':
            self.assertIn('CASE', joined)
            self.assertNotIn('LOAD N%', joined)
        else:
            # Current tree may ship plain-text .bbc; still must load.
            self.assertTrue(
                'MODE' in joined or 'CIRCLE' in joined or 'PROC' in joined,
                joined[:200],
            )

    def test_load_calcexe_if_present(self):
        path = os.path.join(os.path.expanduser('~'), 'Downloads', 'calcexe', 'CalcEXE')
        if not os.path.isfile(path):
            self.skipTest('CalcEXE not installed')
        with open(path, 'rb') as f:
            data = f.read()
        lines = bbc_binary_to_source(data)
        self.assertGreater(len(lines), 100)
        self.assertTrue(lines[0].startswith('10 REM'))
        interp = BASICInterpreter()
        interp.load(path, announce=False)
        self.assertIn(10, interp.program)
        self.assertIn('REM', interp.program[10].upper())

    def test_until_dot_is_until_false(self):
        """BBCSDL sine.bbc stores forever-loops as UNTIL. (period, not FALSE)."""
        body = bytes([0xF5, 0x20, 0x0B, 0x20, 0x31, 0x20, 0x3A, 0x20, 0xFD, 0x2E])
        self.assertEqual(detokenize_line_body(body, fmt='russell'), 'REPEAT WAIT 1 : UNTIL FALSE')

    def test_load_sine_bbc_until_false(self):
        path = os.path.join(_ROOT, 'examples', 'graphics', 'sine.bbc')
        if not os.path.isfile(path):
            self.skipTest('sine.bbc not present')
        interp = BASICInterpreter()
        interp.load(path, announce=False)
        joined = '\n'.join(interp.program[n] for n in sorted(interp.program)).upper()
        self.assertIn('UNTIL FALSE', joined)
        self.assertNotIn('UNTIL.', joined.replace(' ', ''))

    def test_until_dot_source_is_not_syntax_error(self):
        """Typed ``UNTIL.`` (SDL listing) is a forever test, not ``invalid syntax``."""
        import io
        from contextlib import redirect_stdout, redirect_stderr

        interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none', display_locked=True)
        )
        interp.set_program_line(10, 'C=0')
        interp.set_program_line(20, 'REPEAT')
        interp.set_program_line(30, 'C=C+1: IF C>=3 THEN STOP')
        interp.set_program_line(40, 'UNTIL.')
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(io.StringIO()):
            interp.run()
        out = buf.getvalue()
        self.assertNotIn('UNTIL error', out)
        self.assertNotIn('<string>', out)
        self.assertEqual(float(interp.variables.get('C', 0)), 3.0)


if __name__ == '__main__':
    unittest.main()
