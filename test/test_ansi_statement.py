"""Raw ANSI output is separate from BBC VDU decoding."""
import io
from contextlib import redirect_stdout
import pytest
from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]


def run(lines, dialect='bbc', optimization=0):
    interp = BASICInterpreter(InterpreterConfig(dialect=dialect, display='none', display_locked=True, optimization_level=optimization))
    output = io.StringIO()
    with redirect_stdout(output):
        for n, line in enumerate(lines, 1):
            interp.set_program_line(n*10, line)
        interp.run()
    return output.getvalue(), interp


def test_reset_bytes_and_strings_emit_without_newline():
    output, _ = run(['ANSI 27,"[0m"'])
    assert output == '\x1b[0m'


def test_string_variables_numeric_expressions_and_byte_wrapping():
    output, _ = run(['S$="[32m"', 'ANSI 256+27,S$,-1,65.9'])
    assert output == '\x1b[32m'+chr(255)+'A'


def test_print_order_and_column_are_unchanged():
    output, interp = run(['PRINT "X";', 'ANSI 27,"[0m"', 'PRINT "Y";'])
    assert output == 'X\x1b[0mY'
    assert interp.print_column == 2


def test_mini_accepts_lowercase_keyword():
    output, _ = run(['ansi 27,"[0m"'], dialect='mini')
    assert output == '\x1b[0m'


@pytest.mark.parametrize('optimization', [0, 2])
def test_fn_terminal_effects_are_not_memoized(optimization):
    output, _ = run(['DEF FNf(n)', 'ANSI 27,"[0m"', '=n', 'PRINT FNf(1);FNf(1)'], optimization=optimization)
    assert '?' not in output
    assert output.count('\x1b[0m') == 2


def test_bad_operand_reports_ansi_error_before_emitting_partial_controls():
    output, _ = run(['ANSI 27,MISSING$+'])
    assert '? ANSI error' in output
    assert '\x1b' not in output
