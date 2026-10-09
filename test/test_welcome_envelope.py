"""welcome.bbc: ENVELOPE no-op + glued AND/DIV after int substitution."""
from __future__ import annotations

import os
import sys
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from unittest.mock import patch

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase1]


def test_envelope_is_noop_not_on_error():
    """ENVELOPE must not raise — welcome ON ERROR would MODE 7:END (black screen)."""
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', display_locked=True),
    )
    lines = [
        (10, 'ON ERROR MODE 7:PRINT "TRAP":END'),
        (20, 'ENVELOPE 1,1,-RND(50),-RND(50),-RND(45),255,255,255,127,0,0,-127,127,0'),
        (30, 'PRINT "OK"'),
        (40, 'END'),
    ]
    for n, s in lines:
        interp.program[n] = s
    buf = StringIO()
    with redirect_stdout(buf), redirect_stderr(StringIO()), patch('time.sleep'):
        interp.run()
    out = buf.getvalue()
    assert 'TRAP' not in out
    assert 'OK' in out


def test_and_div_after_int_substitution():
    """welcome: K%=68+(A%AND1) and A%=A%DIV2 after A% becomes a digit."""
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', display_locked=True),
    )
    out = StringIO()
    with redirect_stdout(out), redirect_stderr(StringIO()), patch('time.sleep'):
        for n, s in [
            (10, 'A%=3'),
            (20, 'K%=68+(A%AND1)'),
            (30, 'A%=A%DIV2'),
            (40, 'PRINT K%;",";A%'),
            (50, 'END'),
        ]:
            interp.program[n] = s
        interp.run()
    text = out.getvalue().replace(' ', '')
    # 3 AND 1 = 1 → K%=69; 3 DIV 2 = 1
    assert '69' in text
    assert '1' in text


def test_inkey_digit_glue_assign():
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', display_locked=True),
    )
    out = StringIO()
    errs: list[str] = []
    orig = interp._runtime_error

    def track(msg, *a, **k):
        errs.append(str(msg))
        return orig(msg, *a, **k)

    interp._runtime_error = track  # type: ignore[method-assign]
    with redirect_stdout(out), redirect_stderr(StringIO()), patch('time.sleep'):
        for n, s in [
            (10, 'D%=INKEY1'),
            (20, 'PRINT D%'),
            (30, 'END'),
        ]:
            interp.program[n] = s
        interp.run()
    assert not any('INKEY' in e for e in errs), errs


def test_for_plot_next_same_line_not_pure_delay():
    """welcome: FOR J%:… / PLOT K%,…:NEXT must plot every J, not collapse."""
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
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch('time.sleep'):
        for n, s in [
            (10, 'MODE 5'),
            (20, 'GCOL 0,135:CLG'),
            (30, 'VDU 29,720;450;'),
            (40, 'GCOL 0,0'),
            (50, 'A%=255'),
            (60, 'FOR J%=0 TO 7:K%=68+(A%AND1):A%=A%DIV2'),
            (70, 'PLOT K%,-J%*32,0:NEXT'),
            (80, 'END'),
        ]:
            interp.program[n] = s
        interp.run()
    import numpy as np

    px = np.asarray(interp._display._gfx.pixels)
    ys, xs = np.where(px == 0)
    assert len(xs) >= 8, len(xs)
    assert xs.max() - xs.min() + 1 >= 20, (xs.min(), xs.max())


def test_repeat_until_time_glued():
    """welcome: TI%=TIME:REPEATUNTILTIME-TI%>… must wait, not ON ERROR."""
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', display_locked=True),
    )
    raw = 'TI%=TIME:REPEATUNTILTIME-TI%>5*V%'
    norm = interp._normalize_bbc_dialect_line(raw)
    assert 'REPEAT UNTIL' in norm.upper()
    assert 'UNTIL TIME' in norm.upper()
    assert 'REPEATUNTILTIME' not in raw.upper().replace(' ', '') or 'REPEAT UNTIL' in norm
    out = StringIO()
    errs: list[str] = []
    orig = interp._runtime_error

    def track(msg, *a, **k):
        errs.append(str(msg))
        return orig(msg, *a, **k)

    interp._runtime_error = track  # type: ignore[method-assign]
    with redirect_stdout(out), redirect_stderr(StringIO()), patch('time.sleep'):
        for n, s in [
            (10, 'V%=1'),
            (20, norm),
            (30, 'PRINT "OK"'),
            (40, 'END'),
        ]:
            interp.program[n] = s
        interp.run()
    assert not any('REPEAT' in e or 'missing UNTIL' in e for e in errs), errs
    assert 'OK' in out.getvalue()


def test_if_and1_eq0_colon_plot_body():
    """welcome: IF(I%AND1)=0:PLOT… — body after colon, no THEN."""
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', display_locked=True),
    )
    out = StringIO()
    errs: list[str] = []
    orig = interp._runtime_error

    def track(msg, *a, **k):
        errs.append(str(msg))
        return orig(msg, *a, **k)

    interp._runtime_error = track  # type: ignore[method-assign]
    with redirect_stdout(out), redirect_stderr(StringIO()), patch('time.sleep'):
        for n, s in [
            (10, 'I%=0'),
            (20, 'IF(I%AND1)=0:PRINT "EVEN"'),
            (30, 'I%=1'),
            (40, 'IF(I%AND1)=0:PRINT "ODD_SKIP"'),
            (50, 'PRINT "DONE"'),
            (60, 'END'),
        ]:
            interp.program[n] = s
        interp.run()
    assert not errs, errs
    text = out.getvalue()
    assert 'EVEN' in text
    assert 'ODD_SKIP' not in text
    assert 'DONE' in text


def test_asc_glued_string_literal():
    """welcome: CHR$(ASC\"B\"-(I%=M2)) must not ON ERROR to MODE 7."""
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', display_locked=True),
    )
    assert int(interp._eval_numeric('ASC"B"')) == 66
    out = StringIO()
    errs: list[str] = []
    orig = interp._runtime_error

    def track(msg, *a, **k):
        errs.append(str(msg))
        return orig(msg, *a, **k)

    interp._runtime_error = track  # type: ignore[method-assign]
    with redirect_stdout(out), redirect_stderr(StringIO()), patch('time.sleep'):
        for n, s in [
            (10, 'I%=500'),
            (20, 'M2=708'),
            (30, 'PRINT CHR$(ASC"B"-(I%=M2));'),
            (40, 'END'),
        ]:
            interp.program[n] = s
        interp.run()
    assert not errs, errs
    # I%<>M2 → -0 comparison? BBC (I%=M2) is 0 if false; ASC B=66; CHR$66='B'
    assert 'B' in out.getvalue()


def test_for_j0_one_to_m8_spaced_after_to():
    """welcome PROCSWOOSH: detokenize ``FOR J0%=1TO M8`` must not ON ERROR."""
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', display_locked=True),
    )
    errs: list[str] = []
    orig = interp._runtime_error

    def track(msg, *a, **k):
        errs.append(str(msg))
        return orig(msg, *a, **k)

    interp._runtime_error = track  # type: ignore[method-assign]
    out = StringIO()
    with redirect_stdout(out), redirect_stderr(StringIO()), patch('time.sleep'):
        for n, s in [
            (10, 'M8=5'),
            (20, 'N%=0'),
            (30, 'FOR J0%=1TO M8'),
            (40, 'N%=N%+1'),
            (50, 'NEXT'),
            (60, 'PRINT N%'),
            (70, 'END'),
        ]:
            interp.program[n] = s
        interp.run()
    assert not errs, errs
    assert '5' in out.getvalue().replace(' ', '')


def test_div_glued_to_identifier_after_paren():
    """welcome PROCSWOOSH: U1%=(I%+32-XL%)DIVM8 after XL%→0."""
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', display_locked=True),
    )
    # Normalize alone must split )DIVM8 (was SyntaxError invalid syntax)
    norm = interp._normalize_operators('(500+32-0)DIVM8')
    assert 'DIV' in norm.upper() or '//' in norm
    assert 'DIVM8' not in norm.upper().replace(' ', '')

    out = StringIO()
    with redirect_stdout(out), redirect_stderr(StringIO()), patch('time.sleep'):
        for n, s in [
            (10, 'M8=5'),
            (20, 'I%=500'),
            (30, 'XL%=0'),
            (40, 'U1%=(I%+32-XL%)DIVM8'),
            (50, 'PRINT U1%'),
            (60, 'END'),
        ]:
            interp.program[n] = s
        interp.run()
    assert '106' in out.getvalue().replace(' ', '')  # 532//5
