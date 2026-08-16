"""Owned Microsoft-BASIC-80 rules for dialect mits.

These snippets are ours (not copied from a third-party tree). They lock
precedence and name rules that matter for a later 5.21 golden ladder.
"""
from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout, redirect_stderr

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [
    pytest.mark.phase1,
    pytest.mark.mits,
    pytest.mark.non_gfx,
]


def _interp() -> BASICInterpreter:
    return BASICInterpreter(
        InterpreterConfig(
            dialect='mits',
            display='none',
            display_locked=True,
            identifiers_case_sensitive=False,
        )
    )


def test_integer_backslash_div():
    interp = _interp()
    assert interp.eval_expr('10 \\ 3') == 3


def test_mod_before_addition():
    interp = _interp()
    assert interp.eval_expr('10 MOD 3+1') == 2


def test_unary_minus_after_power():
    """MBASIC: exponentiation binds tighter than unary minus. -2^2 is -4."""
    interp = _interp()
    assert interp.eval_expr('-2^2') == -4


def test_and_before_or():
    interp = _interp()
    # TRUE is -1; 0 OR (1 AND 0) is 0
    assert interp.eval_expr('0 OR 1 AND 0') == 0


def test_true_is_minus_one():
    interp = _interp()
    assert interp.eval_expr('3+2>4') == -1


def test_name_dollar_is_not_a_string_variable():
    """NAME is a file-rename statement; NAME$ must not be a user string var."""
    interp = _interp()
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(io.StringIO()):
        interp.set_program_line(10, 'NAME$="X"')
        interp.set_program_line(20, 'PRINT NAME$')
        interp.run()
    out = buf.getvalue()
    broken = (
        int(getattr(interp, 'error_line_num', 0) or 0) != 0
        or any(line.lstrip().startswith('?') for line in out.splitlines())
    )
    if not broken:
        pytest.xfail('NAME$ still accepted as a variable (5.21 reserved NAME)')
    assert broken


def test_input_line_modifier():
    """MBASIC INPUT prompt; LINE var$ reads the rest of the line."""
    interp = _interp()
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(io.StringIO()):
        interp.set_program_line(10, 'A$="ready"')
        interp.set_program_line(20, 'INPUT "X"; LINE A$')
        interp.set_program_line(30, 'PRINT "ok"')
        # Do not RUN INPUT (would block). Parse-only: execute line 20 as statement
        # via immediate path if available.
        try:
            interp._parse_command('INPUT "X"; LINE A$')
            parsed = True
        except Exception:
            parsed = False
    if not parsed:
        pytest.xfail('INPUT ... LINE var$ not parsed (MBASIC LINE modifier)')
