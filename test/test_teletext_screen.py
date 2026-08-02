"""MODE 7 teletext test screen — current behaviour + future SAA5050 targets.

Visual companion: examples/teletext/mode7_test_screen.bas

Current (assert): alpha/gfx colours, mosaics, flash, separated, bg, hold flags.
Future (xfail until implemented): double-height 140/141, conceal 152.
"""
from __future__ import annotations

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

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

from mini_basic import BASICInterpreter, InterpreterConfig
from mini_basic.bbc_modes import teletext_mosaic_pattern
from mini_basic.display import PygameDisplay

pytestmark = [pytest.mark.phase0]

_SCREEN = os.path.join(
    _ROOT, 'examples', 'teletext', 'mode7_test_screen.bas',
)


def _mode7_display() -> PygameDisplay:
    display = PygameDisplay(scale=1)
    display.set_mode(7)
    return display


class TeletextCurrentBehaviourTests(unittest.TestCase):
    """Features already implemented — must stay green."""

    def test_alpha_fg_colours_129_to_135(self):
        d = _mode7_display()
        # CHR$129 RED at col 0 (control), then 'A' at col 1 with fg=1
        d.write(chr(129) + 'A')
        self.assertEqual(d._text[0][1][1], 1)
        d.goto(0, 0)
        d.write(chr(135) + 'W')
        self.assertEqual(d._text[0][1][1], 7)

    def test_graphics_colour_and_mosaic(self):
        d = _mode7_display()
        d.write(chr(145) + chr(185))
        # control at 0; mosaic at 1 with pattern from code 185
        cell = d._text[0][1]
        self.assertEqual(cell[1], 1)  # gfx fg red
        self.assertEqual(cell[3], teletext_mosaic_pattern(185))

    def test_separated_and_contiguous_flags(self):
        d = _mode7_display()
        d.write(chr(145) + chr(154) + chr(185))
        # col0=145, col1=154, col2=mosaic separated
        self.assertTrue(d._text[0][2][4])
        d.goto(1, 0)
        d.write(chr(145) + chr(155) + chr(185))
        self.assertFalse(d._text[1][2][4])

    def test_new_background_157(self):
        d = _mode7_display()
        d.write(chr(131) + chr(157) + 'X')
        # after 131,157: 'X' should use bg = yellow (3)
        self.assertEqual(d._text[0][2][2], 3)

    def test_flash_toggle_136_137(self):
        d = _mode7_display()
        d.write(chr(136) + chr(129) + 'F')
        self.assertTrue(d._text[0][2][5])
        d.goto(1, 0)
        d.write(chr(137) + chr(130) + 'S')
        self.assertFalse(d._text[1][2][5])

    def test_hold_graphics_sets_state(self):
        d = _mode7_display()
        d.write(chr(145) + chr(185) + chr(158))
        state = d._teletext_lines[0]
        self.assertTrue(state.hold)

    def test_mode7_test_screen_program_loads_and_runs(self):
        if not os.path.isfile(_SCREEN):
            self.skipTest('mode7_test_screen.bas missing')
        interp = BASICInterpreter(
            InterpreterConfig(
                dialect='bbc',
                display='pygame',
                display_locked=True,
                hold_display_open=False,
            ),
        )
        interp.load(_SCREEN, announce=False)
        # Avoid long WAIT at end
        for n, stmt in list(interp.program.items()):
            if stmt.strip().upper().startswith('WAIT'):
                interp.program[n] = 'WAIT 0'
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch(
            'time.sleep',
        ):
            interp.run()
        self.assertTrue(interp._display is not None)
        self.assertEqual(interp._graphics_mode, 7)


class TeletextFutureSaa5050Tests(unittest.TestCase):
    """Targets for full SAA5050 — xfail until implemented.

    When these pass without xfail, remove the mark and update the demo [F] rows.
    """

    @pytest.mark.xfail(
        reason='double-height CHR$141 not implemented (cursor advance only)',
        strict=False,
    )
    def test_future_double_height_141_marks_tall_cells(self):
        d = _mode7_display()
        d.write(chr(141) + chr(130) + 'Hi')
        # Desired: row 0 and/or pairing row carry double-height attribute
        state = d._teletext_lines[0]
        # Placeholder API: once implemented, expose double_height on line state
        self.assertTrue(
            getattr(state, 'double_height', False),
            'line state should record double-height after CHR$141',
        )

    @pytest.mark.xfail(
        reason='conceal CHR$152 not implemented (text still written)',
        strict=False,
    )
    def test_future_conceal_152_hides_following_alpha(self):
        d = _mode7_display()
        d.write(chr(152) + chr(129) + 'SECRET')
        # Desired: cells after 152 are blank/concealed, not visible 'S'
        ch = d._text[0][2][0]
        self.assertIn(ch, (' ', '\0', ''), f'concealed cell should be blank, got {ch!r}')


if __name__ == '__main__':
    unittest.main()
