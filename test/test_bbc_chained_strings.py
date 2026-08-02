import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0]


class BbcChainedStringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))

    def test_adjacent_string_literals_decode(self) -> None:
        text = '"Please tell me a question that would"\'"distinguish "'
        self.assertEqual(
            self.interp._decode_bbc_adjacent_string_literals(text),
            'Please tell me a question that woulddistinguish ',
        )
        spaced = '"Please tell me a question that would "\'"distinguish "'
        self.assertEqual(
            self.interp._decode_bbc_adjacent_string_literals(spaced),
            'Please tell me a question that would distinguish ',
        )

    def test_adjacent_double_quoted_literals_decode(self) -> None:
        self.assertEqual(
            self.interp._decode_bbc_adjacent_string_literals('"Hello"" WORLD"'),
            'Hello WORLD',
        )

    def test_juxtaposed_string_expr_without_plus(self) -> None:
        self.assertEqual(
            self.interp._eval_string_expr('"Hello"STR$(10)'),
            'Hello10',
        )
        self.assertEqual(
            self.interp._eval_string_expr('"Hello"" WORLD"'),
            'Hello WORLD',
        )

    def test_print_juxtaposed_strings_without_plus(self) -> None:
        cases = {
            '"Hello"+STR$(10)': 'Hello10',
            '"Hello"STR$(10)': 'Hello10',
            '"Hello"" WORLD"': 'Hello WORLD',
        }
        for content, expected in cases.items():
            with self.subTest(content=content):
                text, _, _ = self.interp._render_print_content(content, '', 0)
                self.assertEqual(text, expected)


if __name__ == '__main__':
    unittest.main()