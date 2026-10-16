import unittest

from mini_basic.bbc_detokenize import detokenize_line_body

class TestBBCDetokenize(unittest.TestCase):
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

if __name__ == "__main__":
    unittest.main()
