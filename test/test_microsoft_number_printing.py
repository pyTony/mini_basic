"""Microsoft PRINT numeric spacing must not use BBC formatting."""
import io
from contextlib import redirect_stdout
import pytest
import os
import subprocess
import sys
from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


def run(source, dialect, optimization_level=2):
    interpreter = BASICInterpreter(InterpreterConfig(dialect=dialect, display='none', display_locked=True,
        optimization_level=optimization_level))
    output = io.StringIO()
    with redirect_stdout(output):
        for number, statement in enumerate(source.splitlines(), 1):
            interpreter.set_program_line(number*10, statement)
        interpreter.run()
    return output.getvalue()


@pytest.mark.parametrize('dialect', ['mits', 'commodore'])
def test_positive_zero_and_negative_print_spaces(dialect):
    assert run('PRINT "[";1;0;-2;"]"', dialect) == '[ 1  0 -2 ]\n'


@pytest.mark.parametrize('dialect', ['mits', 'commodore'])
def test_words_arrays_comparisons_and_repeated_print(dialect):
    source = 'DIM A(2)\nA(1)=3\nPRINT "THERE ARE";A(1);" SHIPS"\nPRINT 1;\nPRINT -1;\nPRINT (1=1)'
    assert run(source, dialect) == 'THERE ARE 3  SHIPS\n 1 -1 -1 \n'


@pytest.mark.parametrize('dialect', ['mits', 'commodore'])
def test_comma_zones_start_with_sign_space_not_right_justification(dialect):
    assert run('PRINT 1,2', dialect) == ' 1         2 \n'


@pytest.mark.parametrize('dialect', ['mits', 'commodore'])
def test_strings_and_explicit_using_are_not_padded(dialect):
    assert run('PRINT "[";STR$(1);"]"', dialect) == '[1]\n'
    assert run('PRINT USING "##.##";1.5', dialect) == ' 1.50\n'


def test_bbc_and_mini_output_is_unchanged():
    assert run('PRINT "[";1;0;-2;"]"', 'bbc') == '[10-2]\n'
    assert run('PRINT "[";1;0;-2;"]"', 'mini') == '[10-2]\n'


@pytest.mark.parametrize('dialect', ['mits', 'commodore'])
@pytest.mark.parametrize('optimization_level', [0, 1, 2])
def test_float_expression_and_string_comparison_spacing(dialect, optimization_level):
    assert run('PRINT "[";1.5;-2.5;2+3;("A"="A");"]"', dialect, optimization_level) == '[ 1.5 -2.5  5 -1 ]\n'


@pytest.mark.parametrize('dialect', ['mits', 'commodore'])
def test_cli_uses_microsoft_numeric_spacing(dialect):
    result = subprocess.run([sys.executable, '-m', 'mini_basic', '-q', '--display', 'none',
        '--dialect', dialect, '-c', 'PRINT "[";1;0;-2;"]"'],
        capture_output=True, text=True, timeout=15,
        env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
    assert result.returncode == 0, result.stderr
    assert result.stdout == '[ 1  0 -2 ]\n'
