"""CLI --slow / config.run_slow_ms: delay after each BASIC line."""
from __future__ import annotations

import os
import sys
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig
from mini_basic.runtime import _parse_main_args

pytestmark = [pytest.mark.phase1]


def test_parse_slow_default_and_ms():
    _t, _a, _i, _q, _tr, _lm, cfg = _parse_main_args(['--slow', 'prog.bas'])
    assert cfg.run_slow_ms == 50.0
    assert _t == 'prog.bas'
    _t, _a, _i, _q, _tr, _lm, cfg = _parse_main_args(['--slow', '200', 'prog.bas'])
    assert cfg.run_slow_ms == 200.0
    assert _t == 'prog.bas'


def test_run_slow_ms_sleeps_per_line():
    sleeps: list[float] = []

    def fake_sleep(s: float) -> None:
        sleeps.append(float(s))

    interp = BASICInterpreter(
        InterpreterConfig(
            dialect='mini',
            display='none',
            display_locked=True,
            run_slow_ms=40,
        )
    )
    with redirect_stdout(StringIO()), patch('time.sleep', fake_sleep):
        interp.program = {10: 'A=1', 20: 'A=2', 30: 'END'}
        interp.run()
    assert sleeps == [0.04, 0.04]


def test_run_slow_zero_no_sleep():
    sleeps: list[float] = []

    def fake_sleep(s: float) -> None:
        sleeps.append(float(s))

    interp = BASICInterpreter(
        InterpreterConfig(
            dialect='mini',
            display='none',
            display_locked=True,
            run_slow_ms=0,
        )
    )
    with redirect_stdout(StringIO()), patch('time.sleep', fake_sleep):
        interp.program = {10: 'A=1', 20: 'END'}
        interp.run()
    assert sleeps == []
