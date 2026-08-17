"""Consistent dialect gates: case, commands, line numbers.

Locks the structure grid (mits / commodore / tiny / bbc / mini).
SDL extras are mini-only. bbc is traditional BBC (Beeb + BASIC V).
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]

DIALECTS = ('mits', 'commodore', 'tiny', 'bbc', 'mini')
NUMBERED_GOTO = ('mits', 'commodore', 'tiny')
BBC_FAMILY = ('bbc', 'mini')


def _interp(dialect: str, *, strict: bool = True) -> BASICInterpreter:
    return BASICInterpreter(
        InterpreterConfig(
            dialect=dialect,
            strict_dialect=strict,
            display='none',
            display_locked=True,
        )
    )


def _load_text(dialect: str, text: str, *, strict: bool = True) -> tuple[bool, str, BASICInterpreter]:
    interp = _interp(dialect, strict=strict)
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'p.bas')
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(text)
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(io.StringIO()):
            ok = interp.load(path, announce=True)
        return bool(ok), buf.getvalue(), interp


def _run_lines(dialect: str, lines: list[tuple[int, str]]) -> tuple[str, BASICInterpreter]:
    interp = _interp(dialect, strict=False)
    for num, stmt in lines:
        interp.set_program_line(num, stmt)
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(io.StringIO()):
        interp.run()
    return buf.getvalue(), interp


@pytest.mark.parametrize('dialect', DIALECTS)
def test_default_case_mode(dialect: str) -> None:
    interp = _interp(dialect)
    if dialect in BBC_FAMILY:
        assert interp._identifiers_case_sensitive()
    else:
        assert not interp._identifiers_case_sensitive()


@pytest.mark.parametrize('dialect', BBC_FAMILY)
def test_case_on_rejects_lowercase_print(dialect: str) -> None:
    out, interp = _run_lines(dialect, [(10, 'print 1'), (20, 'END')])
    assert interp._identifiers_case_sensitive()
    assert '?' in out or '1' not in out.splitlines()[0] if out else True
    assert '1\n' not in out


@pytest.mark.parametrize('dialect', NUMBERED_GOTO)
def test_case_off_default_accepts_lowercase_print(dialect: str) -> None:
    out, _ = _run_lines(dialect, [(10, 'print 1'), (20, 'END')])
    assert '1' in out


def test_case_off_on_mini_allows_lowercase_print() -> None:
    interp = _interp('mini', strict=False)
    interp.set_case_sensitivity(False, announce=False)
    buf = io.StringIO()
    interp.set_program_line(10, 'print 1')
    interp.set_program_line(20, 'END')
    with redirect_stdout(buf), redirect_stderr(io.StringIO()):
        interp.run()
    assert '1' in buf.getvalue()


@pytest.mark.parametrize('dialect', DIALECTS)
def test_numbered_program_loads(dialect: str) -> None:
    ok, out, interp = _load_text(dialect, '10 PRINT 1\n20 END\n', strict=True)
    assert ok, out
    assert 10 in interp.program


@pytest.mark.parametrize('dialect', NUMBERED_GOTO)
def test_unnumbered_program_rejected_strict(dialect: str) -> None:
    ok, out, interp = _load_text(dialect, 'PRINT 1\nEND\n', strict=True)
    assert not ok, out
    assert not interp.program
    assert 'unnumbered' in out.lower()


@pytest.mark.parametrize('dialect', BBC_FAMILY)
def test_unnumbered_program_loads(dialect: str) -> None:
    ok, out, interp = _load_text(dialect, 'PRINT 1\nEND\n', strict=True)
    assert ok, out
    assert interp.program


@pytest.mark.parametrize('dialect', NUMBERED_GOTO)
@pytest.mark.parametrize(
    'source,token',
    [
        ('10 WHILE 1\n20 WEND\n30 END\n', 'WHILE'),
        ('10 REPEAT\n20 UNTIL 1\n30 END\n', 'REPEAT'),
        ('10 DEF PROCx\n20 ENDPROC\n30 END\n', 'PROC'),
        ('10 CASE X OF\n20 ENDCASE\n30 END\n', 'CASE'),
        ('10 BREAK\n20 END\n', 'BREAK'),
    ],
)
def test_structured_rejected_on_numbered_goto_dialects(
    dialect: str, source: str, token: str
) -> None:
    ok, out, interp = _load_text(dialect, source, strict=True)
    assert not ok, out
    assert not interp.program
    assert token.lower() in out.lower() or 'not allowed' in out.lower()


@pytest.mark.parametrize('dialect', BBC_FAMILY)
def test_while_allowed_on_bbc_family(dialect: str) -> None:
    ok, out, _ = _load_text(
        dialect, '10 WHILE FALSE\n20 ENDWHILE\n30 END\n', strict=True
    )
    assert ok, out


def test_break_rejected_on_bbc_allowed_on_mini() -> None:
    ok_bbc, out_bbc, _ = _load_text('bbc', '10 BREAK\n20 END\n', strict=True)
    assert not ok_bbc, out_bbc
    ok_mini, out_mini, _ = _load_text('mini', '10 BREAK\n20 END\n', strict=True)
    assert ok_mini, out_mini


def test_exit_for_is_mini_sdl_only() -> None:
    ok_bbc, out_bbc, _ = _load_text(
        'bbc', '10 FOR I=1 TO 3\n20 EXIT FOR\n30 NEXT\n40 END\n', strict=True
    )
    assert not ok_bbc, out_bbc
    ok_mini, out_mini, _ = _load_text(
        'mini', '10 FOR I=1 TO 3\n20 EXIT FOR\n30 NEXT\n40 END\n', strict=True
    )
    assert ok_mini, out_mini


def test_on_close_is_mini_sdl_only() -> None:
    ok_bbc, out_bbc, _ = _load_text('bbc', '10 ON CLOSE QUIT\n20 END\n', strict=True)
    assert not ok_bbc, out_bbc
    ok_mini, out_mini, _ = _load_text('mini', '10 ON CLOSE QUIT\n20 END\n', strict=True)
    assert ok_mini, out_mini


def test_if_goto_rejected_on_bbc_and_tiny() -> None:
    src = '10 IF 1 GOTO 30\n20 PRINT 0\n30 END\n'
    ok_bbc, out_bbc, _ = _load_text('bbc', src, strict=True)
    assert not ok_bbc, out_bbc
    ok_tiny, out_tiny, _ = _load_text('tiny', src, strict=True)
    assert not ok_tiny, out_tiny
    ok_mits, _, _ = _load_text('mits', src, strict=True)
    assert ok_mits
    ok_mini, _, _ = _load_text('mini', src, strict=True)
    assert ok_mini


def test_if_then_line_rejected_only_on_tiny() -> None:
    src = '10 IF 1 THEN 30\n20 PRINT 0\n30 END\n'
    ok_tiny, out_tiny, _ = _load_text('tiny', src, strict=True)
    assert not ok_tiny, out_tiny
    for dialect in ('mits', 'commodore', 'bbc', 'mini'):
        ok, out, _ = _load_text(dialect, src, strict=True)
        assert ok, f'{dialect}: {out}'


def test_instr_allowed_on_bbc_not_mits() -> None:
    src = '10 PRINT INSTR("AB","B")\n20 END\n'
    ok_bbc, out_bbc, _ = _load_text('bbc', src, strict=True)
    assert ok_bbc, out_bbc
    ok_mits, out_mits, _ = _load_text('mits', src, strict=True)
    assert not ok_mits, out_mits


def test_arg_rejected_on_bbc_allowed_on_mini() -> None:
    src = '10 PRINT ARG(1)\n20 END\n'
    ok_bbc, out_bbc, _ = _load_text('bbc', src, strict=True)
    assert not ok_bbc, out_bbc
    ok_mini, out_mini, _ = _load_text('mini', src, strict=True)
    assert ok_mini, out_mini


def test_dialect_allows_table() -> None:
    checks = {
        'WHILE': {'mits': False, 'commodore': False, 'tiny': False, 'bbc': True, 'mini': True},
        'CASE': {'mits': False, 'commodore': False, 'tiny': False, 'bbc': True, 'mini': True},
        'EXIT': {'mits': False, 'commodore': False, 'tiny': False, 'bbc': False, 'mini': True},
        'BREAK': {'mits': False, 'commodore': False, 'tiny': False, 'bbc': False, 'mini': True},
        'on_close': {'mits': False, 'commodore': False, 'tiny': False, 'bbc': False, 'mini': True},
        'inkey_scan': {'mits': False, 'commodore': False, 'tiny': False, 'bbc': False, 'mini': True},
        'INSTR': {'mits': False, 'commodore': False, 'tiny': False, 'bbc': True, 'mini': True},
        'unnumbered_program': {
            'mits': False,
            'commodore': False,
            'tiny': False,
            'bbc': True,
            'mini': True,
        },
        'numbered_program': {
            'mits': True,
            'commodore': True,
            'tiny': True,
            'bbc': True,
            'mini': True,
        },
        'if_goto': {'mits': True, 'commodore': True, 'tiny': False, 'bbc': False, 'mini': True},
        'if_then_line': {
            'mits': True,
            'commodore': True,
            'tiny': False,
            'bbc': True,
            'mini': True,
        },
    }
    for feature, expect in checks.items():
        for dialect, allowed in expect.items():
            interp = _interp(dialect)
            assert interp._dialect_allows(feature) is allowed, f'{dialect} {feature}'
