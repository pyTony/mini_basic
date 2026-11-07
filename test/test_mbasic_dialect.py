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


def test_quoted_data_is_not_evaluated_as_an_expression():
    i, out, err = _run(['X=42', 'DATA "Non-empty","X","1+2"',
                         'READ A$,B$,C$', 'PRINT A$;"|";B$;"|";C$'])
    assert not err
    assert out == 'Non-empty|X|1+2\n'


def test_numeric_string_functions_print_with_numeric_padding():
    _, out, err = _run(['PRINT LEN("abc");ASC("A");VAL("12");INSTR("abc","b")'])
    assert not err
    assert out == ' 3  65  12  2 \n'


def test_mbasic_str_has_sign_space():
    _, out, err = _run(['PRINT "[";STR$(42);"][";STR$(-42);"]"'])
    assert not err
    assert out == '[ 42][-42]\n'


@pytest.mark.parametrize('pack,unpack,value', [('MKI$', 'CVI', -500), ('MKS$', 'CVS', -2.5), ('MKD$', 'CVD', 123.456789012345)])
def test_binary_conversion_accepts_string_argument(pack, unpack, value):
    i, _, err = _run([f'S$={pack}({value})', f'X#={unpack}(S$)'])
    assert not err
    assert i.variables['X'] == pytest.approx(value)


@pytest.mark.parametrize('body', [
    ['FOR I=10 TO 1', 'N=N+1', 'NEXT I', 'PRINT N;I'],
    ['FOR I=10 TO 1:N=N+1:NEXT I:PRINT N;I'],
    ['FOR I=10 TO 1', 'FOR J=1 TO 2', 'N=N+1', 'NEXT J:NEXT I:PRINT N;I'],
    ['FOR I=10 TO 1', 'FOR J=1 TO 2', 'N=N+1', 'NEXT J,I:PRINT N;I'],
    ['FOR I=1 TO 10 STEP -1', 'N=N+1', 'NEXT I', 'PRINT N;I+9'],
])
def test_mbasic_exhausted_for_skips_body_and_preserves_start(body):
    _, out, err = _run(body)
    assert not err
    assert out == ' 0  10 \n'


@pytest.mark.parametrize('dialect', ['mini', 'bbc'])
def test_bbc_style_exhausted_for_still_runs_once(dialect):
    i, _, err = _run(['FOR I=10 TO 1', 'N=N+1', 'NEXT I'], dialect)
    assert not err
    assert i.variables['N'] == 1


def test_mbasic_tron_troff_trace_goes_to_program_output():
    _, out, err = _run(['TRON', 'A=1', 'PRINT A', 'TROFF', 'PRINT "done"'])
    assert not err
    assert out == '[20][30] 1 \n[40]done\n'
    _, out, err = _run(['TRON', 'GOSUB 50:PRINT "back"', 'TROFF', 'END', 'RETURN'])
    assert not err
    assert out == '[20][50]back\n[30]'


def test_mbasic_input_file_reads_fields(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'VALUES.TXT').write_text('"Alice, A",25,1250.5\n"Bob",30,1500.75\n')
    i, out, err = _run(['OPEN "I",1,"VALUES.TXT"', 'INPUT #1,N$,A,S',
                         'PRINT N$;A;S', 'INPUT #1,N$,A,S', 'PRINT N$;A;S', 'CLOSE 1'])
    assert not err
    assert out == 'Alice, A 25  1250.5 \nBob 30  1500.75 \n'
