"""Regression: rgb_dirty stores (sx, sy); present must not swap axes."""
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

pytestmark = [pytest.mark.phase0]


def test_colour_rgb_then_refresh_no_index_error():
    """COLOR n,r,g,b + CIRCLEFILL + *REFRESH must not IndexError on rgb_dirty."""
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
        (30, '* REFRESH OFF'),
        (40, 'COLOR 1,255,0,0'),
        (50, 'GCOL 1'),
        (60, 'CIRCLE FILL 200,100,40'),
        (70, '* REFRESH'),
        (80, 'END'),
    ]
    for n, s in lines:
        interp.program[n] = s
    errors: list[str] = []
    orig = interp._runtime_error

    def track(msg, *a, **k):
        errors.append(str(msg))
        return orig(msg, *a, **k)

    interp._runtime_error = track  # type: ignore[method-assign]
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch('time.sleep'):
        interp.run()
    assert not any('OSCLI' in e or 'list index' in e for e in errors), errors


def test_soccerball_present_not_blanked_by_colour_bg_text_grid():
    """COLOR 130 + CLS must not overpaint PLOT/CIRCLE with text-cell fills."""
    path = os.path.join(_ROOT, 'examples', 'graphics', 'soccerball.bas')
    if not os.path.isfile(path):
        pytest.skip('soccerball.bas missing')
    interp = BASICInterpreter(
        InterpreterConfig(
            dialect='bbc',
            display='pygame',
            display_locked=True,
            hold_display_open=False,
        ),
    )
    interp.load(path, announce=False)
    for n, stmt in list(interp.program.items()):
        u = stmt.strip().upper()
        if u == 'UNTIL FALSE':
            interp.program[n] = 'UNTIL TRUE'
        if u.startswith('WAIT'):
            interp.program[n] = 'REM'
    # Keep window alive to inspect canvas after RUN
    interp._shutdown_display = lambda **k: None  # type: ignore[method-assign]
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch('time.sleep'):
        interp.run()
    disp = interp._display
    assert disp is not None
    disp.present(force=True)
    surf = disp._canvas
    assert surf is not None
    # Yellow ball (GCOL 3) at centre; green (COLOUR 130) in corner
    w, h = surf.get_width(), surf.get_height()
    centre = surf.get_at((w // 2, h // 2))[:3]
    corner = surf.get_at((10, 10))[:3]
    assert centre != corner, (centre, corner)
    assert centre[0] > 100 and centre[1] > 100  # yellow-ish
    assert corner[1] > corner[0]  # green-ish


def test_wheel_bbc_one_frame_refresh():
    path = os.path.join(_ROOT, 'examples', 'graphics', 'wheel.bbc')
    if not os.path.isfile(path):
        pytest.skip('wheel.bbc missing')
    interp = BASICInterpreter(
        InterpreterConfig(
            dialect='bbc',
            display='pygame',
            display_locked=True,
            hold_display_open=False,
        ),
    )
    interp.load(path, announce=False)
    # One outer iteration: replace forever loop with END (keep wait structure valid).
    for n, stmt in list(interp.program.items()):
        if stmt.strip().upper() == 'UNTIL FALSE':
            interp.program[n] = 'UNTIL TRUE'
    frames = {'n': 0}
    real_flush = interp._flush_display

    def count_flush(force: bool = False):
        frames['n'] += 1
        return real_flush(force=force)

    interp._flush_display = count_flush  # type: ignore[method-assign]
    errors: list[str] = []
    orig = interp._runtime_error

    def track(msg, *a, **k):
        errors.append(str(msg))
        return orig(msg, *a, **k)

    interp._runtime_error = track  # type: ignore[method-assign]
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch('time.sleep'):
        # TIME may not advance under dummy; force wait loop exit by patching TIME read
        with patch.object(interp, '_check_user_interrupt', lambda: None):
            # After first *REFRESH, break out of spin-wait by bumping a counter clock
            t = {'v': 0}

            def fake_time_prop():
                t['v'] += 1
                return float(t['v'])

            # Prefer runtime TIME evaluation if available
            if hasattr(interp, '_get_time'):
                with patch.object(interp, '_get_time', side_effect=fake_time_prop):
                    interp.run()
            else:
                interp.run()
    assert not any('OSCLI' in e or 'list index' in e for e in errors), errors
    assert frames['n'] >= 1
