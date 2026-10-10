"""welcome: VDU 23 user chars + PLOT 6 invert."""
from __future__ import annotations
import os, sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import patch
import pytest
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
from mini_basic import BASICInterpreter, InterpreterConfig
from mini_basic.bbc_graphics import apply_gcol
pytestmark = [pytest.mark.phase1]

def test_plot6_invert_is_beeb_nibble_not_ff():
    assert apply_gcol(7, 0, 4) == 0
    assert apply_gcol(1, 0, 4) == 6

def test_vdu_23_defines_chr255_solid_block():
    interp = BASICInterpreter(InterpreterConfig(dialect="bbc", display="pygame", display_locked=True, hold_display_open=False))
    interp._shutdown_display = lambda **k: None
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch("time.sleep"):
        for n, s in [
            (10, "MODE 5"), (20, "VDU 5"),
            (30, "VDU 23,255,255,255,255,255,255,255,255,255"),
            (40, "GCOL 0,1"), (50, "MOVE 200,600"), (60, "PRINT CHR$255;"), (70, "END"),
        ]:
            interp.program[n] = s
        interp.run()
    assert 255 in interp._display._user_chars
    interp._display.present(force=True)
    surf = interp._display._canvas
    red = sum(1 for y in range(surf.get_height()) for x in range(surf.get_width())
              if surf.get_at((x, y))[0] > 150 and surf.get_at((x, y))[1] < 80)
    assert red > 50


def test_welcome_letter_inside_red_block():
    """VDU 5 cursor is top-left of cell: CHR$255 fill + letter sit in PROCLETTER box."""
    interp = BASICInterpreter(
        InterpreterConfig(dialect="bbc", display="pygame", display_locked=True, hold_display_open=False)
    )
    interp._shutdown_display = lambda **k: None  # type: ignore[method-assign]
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch("time.sleep"):
        for n, s in [
            (10, "MODE 5"),
            (20, "VDU 5"),
            (30, "VDU 23,255,255,255,255,255,255,255,255,255"),
            (40, "GCOL 0,135:CLG"),
            (50, "M0=650:I%=500"),
            (60, "GCOL 0,1"),
            (70, "MOVE I%-4,M0+4:PRINT CHR$255;"),
            (80, "MOVE I%,M0-28:DRAW I%+56,M0-28"),
            (90, "MOVE I%,M0+8:DRAW I%+56,M0+8"),
            (100, "MOVE I%-8,M0+4:DRAW I%-8,M0-28"),
            (110, "MOVE I%,M0-32:DRAW I%+56,M0-32"),
            (120, "MOVE I%+64,M0+4:DRAW I%+64,M0-28"),
            (130, "GCOL 0,7"),
            (140, 'MOVE I%+6,M0+2:PRINT "B";'),
            (150, "END"),
        ]:
            interp.program[n] = s
        interp.run()
        interp._display.present(force=True)
    surf = interp._display._canvas
    # Solid fill + frame occupy roughly sx 54..70, sy 91..101 (MODE 5 OS→pixel).
    red = white = 0
    for y in range(91, 101):
        for x in range(54, 72):
            r, g, b = surf.get_at((x, y))[:3]
            if r > 150 and g < 80 and b < 80:
                red += 1
            elif r > 200 and g > 200 and b > 200:
                white += 1
    assert red >= 40, red
    # Letter B punches white into the red cell (GCOL 0,7).
    assert white >= 8, white
    # VDU 5 burns into the pixel buffer (not present-time layers).
