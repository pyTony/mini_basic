import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest
from mini_basic.bbc_detokenize import parse_wilson_program

pytestmark = [pytest.mark.phase0]

class BBCDetokenizeTests(unittest.TestCase):
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
        # A valid single line
        # First 4 bytes: 0x0D (header), 0x00 0x0A (line 10), 0x02 (line_len = body_len = 2 bytes)
        # body: 0xF1 (PRINT), 0x0D (terminator).
        # So total body length = 2.
        # Wait, if line_len is 2, body is body[index:index+2].
        # In parse_wilson_program:
        # index = 4, body is data[4:6].
        # Then we check body[-1] == 0x0D.
        # So yes, 0x0D 0x00 0x0A 0x02 0xF1 0x0D is correct.
        data = b'\x0d\x00\x0a\x02\xf1\x0d'
        lines = parse_wilson_program(data)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], (10, 'PRINT'))

    def test_parse_wilson_program_multi_line(self):
        # Multi line program
        # The line_len for line 1 includes the trailer 0x0D, next_line_num(2), next_line_len(1).
        # Wait, trailer is 4 bytes: 0x0D, next_line_num_hi, next_line_num_lo, next_line_len.
        # So line 1 text is 0xF1 (length 1).
        # Trailer is 4 bytes. Total body length is 5.
        # First header: 0x0D 0x00 0x0A 0x05
        # Line 1 body: 0xF1 0x0D 0x00 0x14 0x02
        # where 0x14 is 20 (next line num), 0x02 is next line length.
        # Next line is body of length 2: 0xE3 0x0D
        # So total data:
        # 0x0D 0x00 0x0A 0x05 (header for 1st line)
        # 0xF1 0x0D 0x00 0x14 0x02 (body for 1st line)
        # 0xE3 0x0D (body for 2nd line)
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
