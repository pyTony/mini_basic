import unittest
from unittest.mock import patch
from mini_basic.bbc_detokenize import bbc_binary_to_source, detect_bbc_binary_format

class TestBBCBinaryToSource(unittest.TestCase):
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

if __name__ == '__main__':
    unittest.main()
