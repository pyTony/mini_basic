import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pytest

from mini_basic.bbc_font import glyph_rows

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


class BBCFontTests(unittest.TestCase):
    def test_acorn_capital_a_matches_mos_rom(self):
        self.assertEqual(glyph_rows('A'), (0x3C, 0x66, 0x66, 0x7E, 0x66, 0x66, 0x66, 0x00))

    def test_space_is_blank(self):
        self.assertEqual(glyph_rows(' '), (0,) * 8)


if __name__ == '__main__':
    unittest.main()
