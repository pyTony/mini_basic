"""Microsoft PRINT numeric spacing must not use BBC formatting."""
import io
from contextlib import redirect_stdout
import pytest
from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


def run(source, dialect):
    interpreter = BASICInterpreter(InterpreterConfig(dialect=dialect, display='none', display_locked=True))
    output = io.StringIO()
    with redirect_stdout(output):
        for number, statement in enumerate(source.splitlines(), 1):
            interpreter.set_program_line(number*10, statement)
        interpreter.run()
    return output.getvalue()


@pytest.mark.parametrize('dialect', ['mits', 'commodore'])
def test_positive_zero_and_negative_print_spaces(dialect):
    assert run('PRINT "[";1;0;-2;"]"', dialect) == '[ 1  0 -2 ]\n'
