"""INPUT/PRINT reference cases from the user's 2026-10-31 BBCSDL screenshots."""
import io
from contextlib import redirect_stderr, redirect_stdout

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


def run_program(source, dialect, replies=()):
    interp = BASICInterpreter(InterpreterConfig(
        dialect=dialect, display='none', display_locked=True))
    for number, statement in enumerate(source, 1):
        interp.set_program_line(number * 10, statement)
    answers = iter(replies)
    transcript, errors = io.StringIO(), io.StringIO()

    def read(prompt=''):
        # Record the prompt and echo as an interactive terminal would.
        reply = next(answers)
        print(prompt + reply)
        return reply

    interp._read_program_input = read
    with redirect_stdout(transcript), redirect_stderr(errors):
        interp.run()
    return transcript.getvalue(), errors.getvalue(), interp


@pytest.mark.parametrize('separator,question', [(',', '? '), (';', '? '), ('', '')])
def test_sdl_prompt_separators(separator, question):
    out, err, _ = run_program([
        f'INPUT "Name:"{separator}NAME$',
        'PRINT "HI, ";NAME$;"!"',
        'PRINT "HI, "NAME$"!"',
    ], 'bbc', ['Tony'])
    assert not err
    assert out == f'Name:{question}Tony\nHI, Tony!\nHI, Tony!\n'


def test_empty_prompt_comma_still_prints_question():
    out, err, _ = run_program(['INPUT "",X$'], 'bbc', ['Tony'])
    assert not err
    assert out == '? Tony\n'


def test_print_semicolon_then_input_continues_same_line():
    out, err, _ = run_program(['PRINT "Name:";:INPUT "",NAME$'], 'bbc', ['Tony'])
    assert not err
    assert out == 'Name:? Tony\n'


def test_bbc_ordinary_input_splits_commas():
    _, err, interp = run_program(['INPUT ""A$'], 'bbc', ['Hello, world'])
    assert not err
    assert interp.str_variables['A'] == 'Hello'


def test_bbc_input_line_preserves_entire_reply():
    _, err, interp = run_program(['INPUT LINE ">"A$'], 'bbc', ['  Hello, "world"  '])
    assert not err
    assert interp.str_variables['A'] == '  Hello, "world"  '


def test_numeric_comma_semicolon_fields():
    out, err, _ = run_program(['FOR I%=1 TO 16:PRINT I%,;:NEXT'], 'bbc')
    assert not err
    assert out == ''.join(str(i).rjust(10) for i in range(1, 9)) + '\n' + ''.join(
        str(i).rjust(10) for i in range(9, 17))


def test_numeric_trailing_comma_without_semicolon_ends_line():
    out, err, _ = run_program(['FOR I%=1 TO 3:PRINT I%,:NEXT'], 'bbc')
    assert not err
    assert out == ''.join(str(i).rjust(10) + '\n' for i in range(1, 4))
