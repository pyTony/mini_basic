"""Dialect mbasic (mits + WHILE/WEND, INSTR) and `_single` single precision."""
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


def _run(lines, dialect='mbasic'):
    interp = BASICInterpreter(
        InterpreterConfig(dialect=dialect, display='none', display_locked=True)
    )
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        for num, text in enumerate(lines, start=1):
            interp.set_program_line(num * 10, text)
        interp.run()
    return interp, out.getvalue(), err.getvalue()


def test_mbasic_runs_while_wend_and_instr():
    _, out, err = _run([
        'I = 0',
        'WHILE I < 3',
        'I = I + 1',
        'WEND',
        'PRINT I; INSTR("ABCDEF", "CD")',
    ])
    assert 'not allowed' not in err
    assert out.split() == ['3', '3']


@pytest.mark.parametrize('feature', ['WHILE', 'WEND', 'INSTR'])
def test_release5_features_are_mbasic_not_mits(feature):
    mits, _, _ = _run([], dialect='mits')
    mbasic, _, _ = _run([], dialect='mbasic')
    assert not mits._dialect_allows(feature)
    assert mbasic._dialect_allows(feature)


@pytest.mark.parametrize('dialect', ['mits', 'mbasic'])
def test_single_print_six_digits(dialect):
    _, out, _ = _run(['PRINT 1/3; 22/7; -0.5; 1E20; 1E-10; 1234567'], dialect)
    assert out.split() == ['.333333', '3.14286', '-.5', '1E+20', '1E-10', '1234567']


def test_single_print_keeps_doubles():
    _, out, _ = _run(['A# = 123.456789012345', 'PRINT A#; 1/3'])
    assert out.split() == ['123.456789012345', '.333333']


def test_bang_store_rounds_to_single():
    interp, _, _ = _run(['A! = 0.1', 'B = 0.1'], dialect='mini')
    assert interp.variables['A'] == pytest.approx(0.100000001490116, abs=1e-15)
    assert interp.variables['A'] != 0.1
    assert interp.variables['B'] == 0.1


def test_single_off_restores_doubles():
    interp, out, _ = _run(['_single = 0', 'A! = 0.1', 'PRINT 1/3; A!'])
    assert interp.variables['A'] == 0.1
    assert out.split() == ['.333333333333333', '.1']


def test_single_system_variable_default_on():
    _, out, _ = _run(['PRINT _single'])
    assert out.split() == ['1']


def test_mini_print_unchanged():
    _, out, _ = _run(['PRINT 1/3'], dialect='mini')
    assert out.strip() == '0.333333333333333'
