"""mini deliberately does NOT inherit BBC's INPUT/PRINT quirks (Tony, 2026-11-01).

Real BBC BASIC (see test_bbc_input_print_reference.py) is unintuitive in two
ways: a trailing PRINT ',' still ends the line (only ';' keeps packing), and
an INPUT prompt shows '? ' for *both* ',' and ';' separators. mini is meant
to read as "logical" BASIC rather than lock onto those BBC-specific rules,
so it follows the more common MBASIC/MS BASIC convention instead (see
test_ms_input_prompt.py): a trailing PRINT ',' suppresses the newline, and
an INPUT prompt shows '? ' only for ';' (',' suppresses it).

These tests exist specifically to make that choice visible and intentional,
not an oversight -- if one of them breaks, that's a dialect-policy change
to confirm with the user, not a bug to silently "fix" back to BBC's rules.
"""
import io
from contextlib import redirect_stderr, redirect_stdout

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


def run_program(source, replies=()):
    interp = BASICInterpreter(InterpreterConfig(
        dialect='mini', display='none', display_locked=True))
    for number, statement in enumerate(source, 1):
        interp.set_program_line(number * 10, statement)
    answers = iter(replies)
    transcript, errors = io.StringIO(), io.StringIO()

    def read(prompt=''):
        reply = next(answers)
        print(prompt + reply)
        return reply

    interp._read_program_input = read
    with redirect_stdout(transcript), redirect_stderr(errors):
        interp.run()
    return transcript.getvalue(), errors.getvalue(), interp


def test_comma_prompt_suppresses_question_mark():
    """mini, unlike bbc: INPUT "Name:",X$ shows no '? ' before reading."""
    out, err, _ = run_program(['INPUT "Name:",X$'], ['Tony'])
    assert not err
    assert out == 'Name:Tony\n'


def test_semicolon_prompt_adds_question_mark():
    """mini matches bbc here only because MBASIC's own rule also says so."""
    out, err, _ = run_program(['INPUT "Name:";X$'], ['Tony'])
    assert not err
    assert out == 'Name:? Tony\n'


def test_empty_prompt_comma_shows_no_question_mark():
    """mini, unlike bbc: INPUT "",X$ with a comma reads with no '? ' at all."""
    out, err, _ = run_program(['INPUT "",X$'], ['Tony'])
    assert not err
    assert out == 'Tony\n'


def test_trailing_print_comma_keeps_packing_the_line():
    """mini, unlike bbc, suppresses the newline on a trailing PRINT ','."""
    out, err, _ = run_program(['FOR I%=1 TO 3:PRINT I%,:NEXT'])
    assert not err
    assert out == ''.join(str(i).rjust(10) for i in range(1, 4))
