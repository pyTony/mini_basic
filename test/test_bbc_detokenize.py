"""BBC binary detokenize — Wilson + Russell (phase1 regression)."""
from __future__ import annotations

import os
import sys
import unittest

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from unittest.mock import patch

from mini_basic.bbc_detokenize import (
    bbc_binary_to_source,
    detect_bbc_binary_format,
    detokenize_line_body,
    parse_russell_program,
    parse_wilson_program,
)
from mini_basic import InterpreterConfig
from mini_basic.runtime import BASICInterpreter

_WHEEL_BBC = os.path.join(_ROOT, 'showcase', 'wheel.bbc')

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

    def test_russell_sys_token_is_not_a_tab(self):
        """Russell format: byte 0x09 is the SYS token (surks.bbc), not a tab."""
        sdl = b' "SDL_GetCurrentDisplayMode", 0, mode{}'
        self.assertEqual(
            detokenize_line_body(bytes([0x09]) + sdl, fmt='russell'),
            'SYS "SDL_GetCurrentDisplayMode", 0, mode{}',
        )
        self.assertEqual(
            detokenize_line_body(b'A%=1:' + bytes([0x09]) + b' "X",0', fmt='russell'),
            'A%=1:SYS "X",0',
        )
        # A star command is raw text: a tab after * is still skipped there only
        # for non-Russell files, and never eats a following SYS token.
        self.assertEqual(
            detokenize_line_body(b'*' + bytes([0x09]) + b' "X"', fmt='russell'),
            '*SYS "X"',
        )

    def test_wilson_tab_is_still_whitespace(self):
        self.assertEqual(detokenize_line_body(b'A%=1:\tB%=2', fmt='wilson'), 'A%=1:\tB%=2')

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

    def test_star_command_space_normalized(self):
        """``* PLAY"x"`` and ``*PLAY"x"`` tokenize to the same bytes on real

        BBC BASIC; mini_basic should always LIST the command name glued to
        the ``*``, regardless of whether a space was typed before it.
        """
        body = b'A%=1 : * PLAY"x",2\r'
        self.assertEqual(
            detokenize_line_body(body, fmt='russell'),
            'A%=1 : *PLAY"x",2',
        )
        body2 = b'*MUSIC OFF\r'
        self.assertEqual(detokenize_line_body(body2, fmt='russell'), '*MUSIC OFF')

    def test_star_command_space_not_confused_with_multiply(self):
        """A mid-expression ``*`` (multiply) must not be touched."""
        body = b'A%=1*2\r'
        self.assertEqual(detokenize_line_body(body, fmt='russell'), 'A%=1*2')

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


class TokenizedIntegerTruncationTests(unittest.TestCase):
    """Tokenized program ``a%=3.7 : PRINT a%`` (both lines numbered 0)."""

    PROGRAM = b'\n\x00\x00a%=3.7\r\x08\x00\x00\xf1 a%\r\x04\x00\x00\r\x00\xff\xff'

    def test_integer_assignment_truncates(self):
        import io
        import tempfile
        from contextlib import redirect_stderr, redirect_stdout

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'rounding.bbc')
            with open(path, 'wb') as handle:
                handle.write(self.PROGRAM)
            interp = BASICInterpreter(
                InterpreterConfig(dialect='bbc', display='none', display_locked=True)
            )
            interp.load(path, announce=False)
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                interp.run()
        self.assertEqual(out.getvalue().split(), ['3'], msg=err.getvalue())


class TestBBCBinaryToSource(unittest.TestCase):
    """PR #129: bbc_binary_to_source's format-dispatch/sanity-check orchestration."""

    def test_unrecognised_format(self):
        # Data shorter than 4 bytes
        with self.assertRaisesRegex(ValueError, 'unrecognised BBC BASIC binary format'):
            bbc_binary_to_source(b'\x00\x01\x02')

    @patch('mini_basic.bbc_detokenize.parse_wilson_program')
    @patch('mini_basic.bbc_detokenize.detect_bbc_binary_format')
    def test_wilson_format_success(self, mock_detect, mock_parse):
        mock_detect.return_value = 'wilson'
        mock_parse.return_value = [
            (10, 'PRINT "HELLO"'),
            (20, 'GOTO 10')
        ]
        result = bbc_binary_to_source(b'dummy')
        self.assertEqual(result, ['10 PRINT "HELLO"', '20 GOTO 10'])

    @patch('mini_basic.bbc_detokenize.parse_russell_program')
    @patch('mini_basic.bbc_detokenize.detect_bbc_binary_format')
    def test_russell_format_success(self, mock_detect, mock_parse):
        mock_detect.return_value = 'russell'
        mock_parse.return_value = [
            (100, 'REM Russell format'),
            (110, 'GOSUB 200')
        ]
        result = bbc_binary_to_source(b'dummy')
        self.assertEqual(result, ['100 REM Russell format', '110 GOSUB 200'])

    @patch('mini_basic.bbc_detokenize.parse_wilson_program')
    @patch('mini_basic.bbc_detokenize.detect_bbc_binary_format')
    def test_duplicate_line_numbers(self, mock_detect, mock_parse):
        mock_detect.return_value = 'wilson'
        mock_parse.return_value = [
            (10, 'PRINT "A"'),
            (10, 'PRINT "B"'),  # Duplicate line number
            (20, 'END')
        ]
        result = bbc_binary_to_source(b'dummy')
        # Function should tolerate and append normally
        self.assertEqual(result, ['10 PRINT "A"', '10 PRINT "B"', '20 END'])

    @patch('mini_basic.bbc_detokenize.parse_wilson_program')
    @patch('mini_basic.bbc_detokenize.detect_bbc_binary_format')
    def test_unnumbered_lines(self, mock_detect, mock_parse):
        mock_detect.return_value = 'wilson'
        mock_parse.return_value = [
            (0, 'INSTALL "LIB"'),
            (10, 'PRINT "START"')
        ]
        result = bbc_binary_to_source(b'dummy')
        self.assertEqual(result, ['INSTALL "LIB"', '10 PRINT "START"'])

    @patch('mini_basic.bbc_detokenize.parse_wilson_program')
    @patch('mini_basic.bbc_detokenize.detect_bbc_binary_format')
    def test_empty_line_skipped(self, mock_detect, mock_parse):
        mock_detect.return_value = 'wilson'
        mock_parse.return_value = [
            (0, ''), # both text and num are falsy
            (10, 'PRINT "HELLO"'),
        ]
        result = bbc_binary_to_source(b'dummy')
        self.assertEqual(result, ['10 PRINT "HELLO"'])

    @patch('mini_basic.bbc_detokenize.parse_wilson_program')
    @patch('mini_basic.bbc_detokenize.detect_bbc_binary_format')
    def test_sanity_check_valid_refs(self, mock_detect, mock_parse):
        mock_detect.return_value = 'wilson'
        # Test valid line numbers (1 - 65535)
        mock_parse.return_value = [
            (10, 'GOTO 1'),
            (20, 'GOSUB 65535'),
            (30, 'RESTORE 100'),
            (40, 'IF A=1 THEN 200'),
            (50, 'THEN 300')
        ]
        result = bbc_binary_to_source(b'dummy')
        self.assertEqual(len(result), 5)

    @patch('mini_basic.bbc_detokenize.parse_wilson_program')
    @patch('mini_basic.bbc_detokenize.detect_bbc_binary_format')
    def test_sanity_check_invalid_refs_zero(self, mock_detect, mock_parse):
        mock_detect.return_value = 'wilson'
        mock_parse.return_value = [
            (10, 'GOTO 0')
        ]
        with self.assertRaisesRegex(ValueError, "invalid GOTO/GOSUB target 0 in '10 GOTO 0'"):
            bbc_binary_to_source(b'dummy')

    @patch('mini_basic.bbc_detokenize.parse_wilson_program')
    @patch('mini_basic.bbc_detokenize.detect_bbc_binary_format')
    def test_sanity_check_invalid_refs_too_large(self, mock_detect, mock_parse):
        mock_detect.return_value = 'wilson'
        mock_parse.return_value = [
            (20, 'GOSUB 65536')
        ]
        with self.assertRaisesRegex(ValueError, "invalid GOTO/GOSUB target 65536 in '20 GOSUB 65536'"):
            bbc_binary_to_source(b'dummy')


class TestDetokenizeLineBody(unittest.TestCase):
    """PR #132: detokenize_line_body's byte-to-source conversion rules."""

    def test_ascii_string(self):
        body = b'PRINT "HELLO"'
        self.assertEqual(detokenize_line_body(body), 'PRINT "HELLO"')

    def test_strings_with_tokens(self):
        # 0xF1 is PRINT, but inside string it's just a byte.
        body = b'\xf1 "HELLO\xf1WORLD"'
        self.assertEqual(detokenize_line_body(body), 'PRINT "HELLO\xf1WORLD"')

    def test_simple_keywords(self):
        # 0xF1 is PRINT, 0xE3 is FOR, 0x88 is STEP, 0xB8 is TO, 0xED is NEXT
        body = b'\xe3I=1 \xb810 \x882:\xf1I:\xed'
        self.assertEqual(detokenize_line_body(body), 'FOR I=1 TO 10 STEP 2:PRINT I:NEXT')

    def test_oscli_star_commands(self):
        # 0x2A is *
        # Spaces after the * token are removed when it's at the start of a statement.
        body = b'*\x20\x20PLAY"X"'
        self.assertEqual(detokenize_line_body(body), '*PLAY"X"')

    def test_line_number_ref(self):
        # 0x8D is line ref, followed by 3 bytes
        body = b'\xe5 \x8d\x40\x0a\x00' # GOTO 74
        self.assertEqual(detokenize_line_body(body), 'GOTO 74')

        body2 = b'\x8d\x40\x14\x00' # Line ref for 84
        self.assertEqual(detokenize_line_body(body2), '84')

    def test_rem_statements(self):
        # 0xF4 is REM.
        # After REM, everything should be parsed as raw chars.
        body = b'\xf4\xf1\x00HELLO'
        self.assertEqual(detokenize_line_body(body), 'REM \xf1\x00HELLO')

    def test_spaces_after_keywords(self):
        body = b'\xf1A'
        self.assertEqual(detokenize_line_body(body), 'PRINT A')
        body = b'\xf1(A)'
        self.assertEqual(detokenize_line_body(body), 'PRINT(A)')

    def test_loop_until_false(self):
        body = b'\xfd.'
        self.assertEqual(detokenize_line_body(body), 'UNTIL FALSE')

    def test_compound_assignments(self):
        body = b'A -= 1'
        self.assertEqual(detokenize_line_body(body), 'A -= 1')
        body = b'B += 2'
        self.assertEqual(detokenize_line_body(body), 'B += 2')


class TestParseWilsonProgram(unittest.TestCase):
    """PR #133: parse_wilson_program's header/line/trailer edge cases."""

    def test_parse_wilson_program_empty(self):
        with self.assertRaisesRegex(ValueError, 'not Wilson-format BBC BASIC'):
            parse_wilson_program(b'')

    def test_parse_wilson_program_wrong_header(self):
        with self.assertRaisesRegex(ValueError, 'not Wilson-format BBC BASIC'):
            parse_wilson_program(b'\x0e\x00\x0a\x04')

    def test_parse_wilson_program_short_data(self):
        # 0x0D followed by less than 3 bytes
        self.assertEqual(parse_wilson_program(b'\x0d\x00\x00'), [])

    def test_parse_wilson_program_valid_empty_program(self):
        # Header is 0x0D, then two bytes for line num, one byte for line len (0)
        data = b'\x0d\x00\x00\x00'
        self.assertEqual(parse_wilson_program(data), [])

    def test_parse_wilson_program_single_line(self):
        # A valid single line:
        # 0x0D (header), 0x00 0x0A (line 10), 0x02 (line_len = body_len = 2 bytes)
        # body: 0xF1 (PRINT), 0x0D (terminator).
        data = b'\x0d\x00\x0a\x02\xf1\x0d'
        lines = parse_wilson_program(data)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], (10, 'PRINT'))

    def test_parse_wilson_program_multi_line(self):
        # Multi line program. The line_len for line 1 includes the trailer
        # (4 bytes: 0x0D, next_line_num_hi, next_line_num_lo, next_line_len).
        data = b'\x0d\x00\x0a\x05\xf1\x0d\x00\x14\x02\xe3\x0d'
        lines = parse_wilson_program(data)
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], (10, 'PRINT'))
        self.assertEqual(lines[1], (20, 'FOR'))

    def test_parse_wilson_program_no_trailer(self):
        # Token 0xF1 (PRINT), followed by 'A' (0x41)
        # The parser will consume the whole body (2 bytes) as text if no 0x0D terminator
        data = b'\x0d\x00\x0a\x02\xf1\x41'
        lines = parse_wilson_program(data)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], (10, 'PRINT A'))

    def test_parse_wilson_program_body_exceeds_data(self):
        # The line length indicates more data than is actually present
        data = b'\x0d\x00\x0a\x0a\xf1\x0d'
        lines = parse_wilson_program(data)
        self.assertEqual(lines, [])


if __name__ == '__main__':
    unittest.main()


class TestProgramBytesToSource(unittest.TestCase):
    """Shared .bbc/.bas loader: tokenised binary or plain text, as LOAD reads it."""

    def test_tokenised_binary_is_detokenised(self):
        with open(_WHEEL_BBC, 'rb') as handle:
            data = handle.read()
        from mini_basic.bbc_detokenize import program_bytes_to_source
        self.assertEqual(program_bytes_to_source(data), bbc_binary_to_source(data))

    def test_text_listing_with_bbc_extension(self):
        # A text listing saved as .bbc (as animal.bbc once was) still loads.
        from mini_basic.bbc_detokenize import program_bytes_to_source
        path = os.path.join(_ROOT, 'examples', 'games', 'animal.bas')
        with open(path, 'rb') as handle:
            data = handle.read()
        lines = program_bytes_to_source(data)
        self.assertEqual(lines, data.decode('utf-8').splitlines())

    def test_cp1252_text_fallback(self):
        from mini_basic.bbc_detokenize import program_bytes_to_source
        self.assertEqual(program_bytes_to_source(b'10 PRINT "caf\xe9"\r\n20 END\r\n'),
                         ['10 PRINT "café"', '20 END'])

    def test_nul_bytes_without_tokenised_format_are_rejected(self):
        from mini_basic.bbc_detokenize import program_bytes_to_source
        with self.assertRaises(UnicodeDecodeError):
            program_bytes_to_source(b'\x00\xff\xfe junk')
