"""Regression: VDU 17 colour pairs must not count toward PRINT wrap width.

Hanoi DISC$ embeds CHR$17+colour. Near column 80, counting those bytes as
cells inserted a newline mid-sequence and left a CHR$128 glyph with the disc
background — a floating coloured remnant after TAKE.

User-approved hanoi.txt (2026-07-26); these unit checks stay green under phase0.
"""
import os
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from unittest.mock import patch

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0]


class HanoiVduPrintWrapTests(unittest.TestCase):
    def test_print_emit_skips_vdu17_for_column(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(dialect="bbc", display="none", display_locked=True)
        )
        interp.print_column = 54
        # 23 visible cells + 4 VDU bytes = 27 raw; must not wrap before end.
        disc = "\x11\x8a" + (" " * 10) + "11" + (" " * 11) + "\x11\x80"
        out = interp._print_emit(disc)
        self.assertNotIn("\n", out)
        self.assertEqual(interp.print_column, 54 + 23)
        self.assertEqual(interp._print_visible_width(disc), 23)

    def test_disc11_near_col80_no_chr128_glyph(self) -> None:
        interp = BASICInterpreter(
            InterpreterConfig(
                dialect="bbc",
                display="pygame",
                display_locked=True,
                hold_display_open=False,
            )
        )
        interp.program[10] = "MODE 3"
        interp.program[20] = "DIM DISC$(13)"
        interp.program[30] = "DISC=11"
        interp.program[40] = (
            'DISC$(DISC)=STRING$(DISC," ")+STR$DISC+STRING$(DISC," ")'
        )
        interp.program[50] = "IF DISC>=10 DISC$(DISC)=MID$(DISC$(DISC),2)"
        interp.program[60] = (
            "DISC$(DISC)=CHR$17+CHR$(128+DISC-(DISC>7))+DISC$(DISC)+CHR$17+CHR$128"
        )
        # Right peg column for disc 11 (same formula as hanoi.bbc).
        interp.program[70] = "PRINT TAB(13+26*2-11,19)DISC$(DISC);"
        interp.program[80] = "END"
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch(
            "time.sleep"
        ):
            interp.run()
        row = interp._display._text[19]
        leaked = [
            (c, row[c][0])
            for c in range(interp._display.text_cols)
            if row[c][0] == "\x80" or (isinstance(row[c][0], str) and ord(row[c][0]) == 128)
        ]
        self.assertEqual(leaked, [], f"leaked control glyphs: {leaked}")
        coloured = [
            c
            for c in range(interp._display.text_cols)
            if (row[c][2] if len(row[c]) > 2 else 0) != 0
        ]
        self.assertEqual(len(coloured), 23)
        self.assertEqual(min(coloured), 54)
        self.assertEqual(max(coloured), 76)

    def test_disc7_and_disc8_colour_codes_differ(self) -> None:
        """Official SDL: 128+DISC-(DISC>7). TRUE is -1 so + would collide."""
        interp = BASICInterpreter(
            InterpreterConfig(dialect="bbc", display="none", display_locked=True)
        )
        seven = int(interp._eval_numeric("128+7-(7>7)"))
        eight = int(interp._eval_numeric("128+8-(8>7)"))
        self.assertEqual(seven, 135)
        self.assertEqual(eight, 137)
        from mini_basic.bbc_modes import map_mode_text_colour

        self.assertEqual(map_mode_text_colour(seven - 128, 3), 7)
        self.assertEqual(map_mode_text_colour(eight - 128, 3), 1)


if __name__ == "__main__":
    unittest.main()
