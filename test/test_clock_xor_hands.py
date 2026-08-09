"""Clock hands: GCOL 3 XOR undraw must clear previous second hand."""
from __future__ import annotations

import os
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase2, pytest.mark.graphics]


def _count_colour(pixels, colour: int) -> int:
    if hasattr(pixels, 'ravel'):
        import numpy as np

        return int(np.sum(np.asarray(pixels) == colour))
    n = 0
    for row in pixels:
        for v in row:
            if int(v) == colour:
                n += 1
    return n


def test_xor_second_hand_undraws():
    """Draw second hand twice with GCOL 3 → net zero ink (XOR erase)."""
    interp = BASICInterpreter(
        InterpreterConfig(
            dialect='bbc',
            display='pygame',
            display_locked=True,
            hold_display_open=False,
        ),
    )
    # MODE 8 for easier pixel counts; same GCOL 3 semantics as Clock.bas
    lines = [
        (10, 'MODE 8'),
        (20, 'ORIGIN 640,512'),
        (30, 'GCOL 0,7: CIRCLE 0,0,300'),
        (40, 'GCOL 3,4'),
        (50, 'MOVE 0,0: DRAW 0,240'),
        (60, 'GCOL 3,4'),
        (70, 'MOVE 0,0: DRAW 0,240'),
        (80, 'END'),
    ]
    for n, s in lines:
        interp.program[n] = s
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch('time.sleep'):
        interp.run()
    pixels = interp._display._gfx.pixels
    blue = _count_colour(pixels, 4)
    # After XOR draw+undraw, pure blue hand pixels should be gone (ticks may remain 7)
    assert blue == 0, f'expected XOR erase of colour 4 hand, got {blue} pixels'


def test_clock_bas_loads_and_one_second_update():
    path = os.path.join(_ROOT, 'basics', 'Clock.bas')
    if not os.path.isfile(path):
        pytest.skip('basics/Clock.bas missing')
    interp = BASICInterpreter(
        InterpreterConfig(
            dialect='bbc',
            display='pygame',
            display_locked=True,
            hold_display_open=False,
        ),
    )
    interp.load(path, announce=False)
    # Expect MODE 8 (square pixels) — MODE 2 @ 4x used non-square PAR scale
    mode_line = next(
        (interp.program[n] for n in sorted(interp.program) if 'MODE' in interp.program[n].upper()),
        '',
    )
    assert 'MODE 8' in mode_line.upper() or 'MODE8' in mode_line.upper().replace(' ', '')
    for n, s in list(interp.program.items()):
        u = s.strip().upper()
        if u.startswith('REPEAT'):
            interp.program[n] = 'REM'
        if u.startswith('UNTIL'):
            interp.program[n] = 'REM'
        if u.startswith('WAIT'):
            interp.program[n] = 'REM'
        if u.startswith('T$=') or 'RIGHT$(TIME$' in u.replace(' ', ''):
            interp.program[n] = 'REM time'
    max_line = max(interp.program)
    n1, n2, n3 = max_line + 10, max_line + 20, max_line + 30
    interp.program[n1] = 'HOUR24%=12:HOUR%=0:MINUTE%=0:SECOND%=0:PROCupdate'
    interp.program[n2] = 'SECOND%=1:PROCupdate'
    interp.program[n3] = 'END'
    errors: list[str] = []
    orig = interp._runtime_error

    def track(msg, *a, **k):
        errors.append(str(msg))
        return orig(msg, *a, **k)

    interp._runtime_error = track  # type: ignore[method-assign]
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch('time.sleep'):
        interp.run()
    assert not any(e.startswith('?') for e in errors), errors
    # Digital PROCdigital must leave glyphs on the composed canvas (not only the text grid).
    disp = interp._display
    assert disp is not None
    interp._shutdown_display = lambda **k: None  # type: ignore[method-assign]
    # Keep canvas: re-present if shutdown already ran before we patched
    if disp._canvas is None:
        disp.present(force=True)
    row1 = disp._text[1]
    digits = ''.join(
        (c[0] if isinstance(c, tuple) else ' ') for c in row1
    ).replace(' ', '')
    assert any(ch.isdigit() for ch in digits), f'expected digital digits in text row 1, got {digits!r}'


def test_graphics_print_not_skipped_by_dirty_patch():
    """PRINT after a dirty plot must still compose text (Clock digital regression)."""
    interp = BASICInterpreter(
        InterpreterConfig(
            dialect='bbc',
            display='pygame',
            display_locked=True,
            hold_display_open=False,
        ),
    )
    lines = [
        (10, 'MODE 8'),
        (20, 'ORIGIN 640,512'),
        (30, 'GCOL 0,7'),
        (40, 'MOVE 0,0:DRAW 0,200'),
        (50, 'COLOUR 7'),
        (60, 'PRINT TAB(0,0);"12:34:56"'),
        (70, 'WAIT 1'),
        (80, 'END'),
    ]
    for n, s in lines:
        interp.program[n] = s
    interp._shutdown_display = lambda **k: None  # type: ignore[method-assign]
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch('time.sleep'):
        interp.run()
    disp = interp._display
    assert disp is not None
    cell0 = disp._text[0][0]
    ch0 = cell0[0] if isinstance(cell0, tuple) else cell0
    assert ch0 == '1', cell0
    surf = disp._canvas
    assert surf is not None
    ink = 0
    for y in range(min(20, surf.get_height())):
        for x in range(min(200, surf.get_width())):
            r, g, b = surf.get_at((x, y))[:3]
            if r + g + b > 40:
                ink += 1
    assert ink > 5, f'PRINT text missing from canvas after dirty plot present (ink={ink})'


def test_print_compose_not_rate_limited_after_hand_draw():
    """Hands present first; digital PRINT within 50ms must still compose (Clock)."""
    interp = BASICInterpreter(
        InterpreterConfig(
            dialect='bbc',
            display='pygame',
            display_locked=True,
            hold_display_open=False,
        ),
    )
    lines = [
        (10, 'MODE 8'),
        (20, 'ORIGIN 640,512'),
        (30, 'GCOL 0,7'),
        (40, 'MOVE 0,0:DRAW 0,200'),
        (50, 'COLOUR 7'),
        (60, 'PRINT TAB(0,0);"99:88:77"'),
        (70, 'WAIT 1'),
        (80, 'END'),
    ]
    for n, s in lines:
        interp.program[n] = s
    interp._shutdown_display = lambda **k: None  # type: ignore[method-assign]
    # Simulate recent hand present so rate limit would skip a normal flush
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch('time.sleep'):
        interp._ensure_display()
        interp._last_present_time = __import__('time').monotonic()
        interp.run()
    surf = interp._display._canvas
    assert surf is not None
    ink = 0
    for y in range(min(20, surf.get_height())):
        for x in range(min(200, surf.get_width())):
            r, g, b = surf.get_at((x, y))[:3]
            if r + g + b > 40:
                ink += 1
    assert ink > 5, f'rate-limited PRINT left text off canvas (ink={ink})'
