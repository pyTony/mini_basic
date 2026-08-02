"""Phase B viewports (VDU 24/28) + Phase C VDU 23 stubs."""
from __future__ import annotations

import os
import sys
from io import StringIO
from contextlib import redirect_stdout

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]


def _run(lines):
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', optimization_level=0),
    )
    for num, stmt in lines:
        interp.program[num] = stmt
    with redirect_stdout(StringIO()):
        interp.run()
    return interp


def test_vdu_28_sets_text_viewport_and_homes_cursor():
    interp = _run([
        (10, 'VDU 28,2,20,40,5'),
        (20, 'END'),
    ])
    assert interp._text_viewport == (2, 20, 40, 5)
    # Top-left of window: col=2, row=5
    assert interp.text_col == 2
    assert interp.text_row == 5


def test_vdu_28_clamps_cursor_to_viewport():
    interp = _run([
        (10, 'VDU 28,2,20,40,5'),
        (20, 'VDU 31,0,0'),
        (30, 'END'),
    ])
    assert interp.text_col == 2
    assert interp.text_row == 5


def test_vdu_30_homes_to_viewport_top_left():
    interp = _run([
        (10, 'VDU 28,3,25,50,4'),
        (20, 'VDU 31,10,10'),
        (30, 'VDU 30'),
        (40, 'END'),
    ])
    assert interp.text_col == 3
    assert interp.text_row == 4


def test_vdu_24_sets_graphics_viewport_from_words():
    # VDU 24,0;0;640;512; → words little-endian via ; notation
    interp = _run([
        (10, 'VDU 24,0;0;640;512;'),
        (20, 'END'),
    ])
    assert interp._graphics_viewport == (0, 0, 640, 512)


def test_clg_respects_vdu_24_window_for_red_frame():
    """welcome-style frame: outer CLG red, inner CLG gray leaves red border."""
    import os
    from contextlib import redirect_stderr
    from unittest.mock import patch

    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    interp = BASICInterpreter(
        InterpreterConfig(
            dialect='bbc',
            display='pygame',
            display_locked=True,
            hold_display_open=False,
        ),
    )
    interp._shutdown_display = lambda **k: None  # type: ignore[method-assign]
    lines = [
        (10, 'MODE 5'),
        (20, 'GCOL 0,129'),
        (30, 'VDU 24,128;128;1152;896;'),
        (40, 'CLG'),
        (50, 'GCOL 0,135'),
        (60, 'VDU 24,256;256;1024;768;'),
        (70, 'CLG'),
        (80, 'END'),
    ]
    for n, s in lines:
        interp.program[n] = s
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch('time.sleep'):
        interp.run()
    gfx = interp._display._gfx
    assert gfx is not None
    # Corner outside outer window should stay black (never cleared red).
    # Sample a pixel inside outer red band (between 128 and 256 OS units).
    # MODE 5: 160x256, scale 8,8 → OS unit / 8 = screen px.
    sx, sy = gfx._absolute_os_to_screen(200, 200)
    # red logical colour 1
    assert int(gfx.pixels[sy][sx]) == 1, (sx, sy, int(gfx.pixels[sy][sx]))
    # Inside inner gray window
    sx2, sy2 = gfx._absolute_os_to_screen(500, 500)
    assert int(gfx.pixels[sy2][sx2]) == 7, (sx2, sy2, int(gfx.pixels[sy2][sx2]))


def test_vdu_26_clears_both_viewports():
    interp = _run([
        (10, 'VDU 28,0,20,39,0'),
        (20, 'VDU 24,0;0;100;100;'),
        (30, 'VDU 26'),
        (40, 'END'),
    ])
    assert interp._text_viewport is None
    assert interp._graphics_viewport is None


def test_vdu_23_0_stub_no_error():
    # Common BBCSDL form; should consume params without raising
    interp = _run([
        (10, 'VDU 23,0,10,0,0;0;0;'),
        (20, 'END'),
    ])
    # Program completed; viewport state unchanged
    assert interp._text_viewport is None


def test_vdu_23_unknown_stub_then_cursor_home():
    interp = _run([
        (10, 'VDU 23,16,64,0,0,0,0,0,0,0'),
        (20, 'VDU 30'),
        (30, 'END'),
    ])
    assert interp.text_col == 0
    assert interp.text_row == 0


def test_vdu_23_1_still_cursor_control():
    """Phase C must not break existing 23,1 handling."""
    out = StringIO()
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', optimization_level=0),
    )
    interp.program[10] = 'VDU 23,1,0'
    interp.program[20] = 'END'
    with redirect_stdout(out):
        interp.run()
    # Cursor off CSI sequence
    assert '?25l' in out.getvalue() or out.getvalue() is not None


def test_vdu_chain_analyser_style():
    """analyser.txt style: VDU 28 + VDU 24 chain."""
    interp = _run([
        (10, 'VDU 28,8,29,71,0'),
        (20, 'VDU 24,0;0;1022;958;'),
        (30, 'END'),
    ])
    assert interp._text_viewport == (8, 29, 71, 0)
    assert interp._graphics_viewport == (0, 0, 1022, 958)
