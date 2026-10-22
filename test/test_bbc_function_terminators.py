"""END DEF is a mini extension, never a BBC FN terminator."""
import io
from contextlib import redirect_stdout, redirect_stderr
import pytest
from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase1, pytest.mark.non_gfx]

SOURCE = ['DEF FNdouble(n)', '=n*2', 'END DEF', 'PRINT FNdouble(21)']

def interpreter(dialect='bbc', strict=False):
    return BASICInterpreter(InterpreterConfig(dialect=dialect, strict_dialect=strict, display='none', display_locked=True))

@pytest.mark.parametrize('strict', [False, True])
def test_bbc_load_rejects_end_def_even_without_strict_dialect(tmp_path, strict):
    path = tmp_path/'function.bas'
    path.write_text('\n'.join(f'{n*10} {line}' for n,line in enumerate(SOURCE,1)))
    runtime = interpreter(strict=strict); output = io.StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        ok = runtime.load(str(path), announce=False)
    assert not ok
    assert 'line 30' in output.getvalue().lower()
    assert 'END DEF' in output.getvalue()
    assert 'mini' in output.getvalue()

def run(lines, dialect='bbc'):
    runtime = interpreter(dialect); output = io.StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        for n,line in enumerate(lines,1): runtime.set_program_line(n*10, line)
        runtime.run()
    return output.getvalue(), runtime

def test_programmatic_bbc_run_rejects_terminator_before_any_output():
    output, _ = run(['PRINT "must not run"']+SOURCE)
    assert 'must not run' not in output
    assert 'END DEF' in output and 'mini' in output

def test_mini_keeps_its_explicit_terminator():
    output, _ = run(SOURCE, 'mini')
    assert output.strip() == '42'

def test_bbc_function_with_native_equals_return_works():
    output, _ = run(['PRINT FNdouble(21)', 'END', 'DEF FNdouble(n)', '=n*2'])
    assert output.strip() == '42'

def test_text_and_comments_are_not_terminators():
    output, _ = run(['REM END DEF', 'PRINT "END DEF"'])
    assert output.strip() == 'END DEF'

def test_switch_to_bbc_refuses_mini_program():
    _, runtime = run(SOURCE, 'mini')
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert not runtime.set_dialect('bbc', announce=False)
    assert runtime.config.dialect == 'mini'

def test_immediate_bbc_end_def_reports_extension_error():
    runtime = interpreter(); output = io.StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        runtime.execute_line(0, 'END DEF', [])
    assert 'END DEF' in output.getvalue() and 'mini' in output.getvalue()


def test_bbc_multiline_proc_without_endproc_reports_error():
    output, _ = run(['PRINT "before"', 'PROCtest', 'PRINT "after"', 'END',
                     'DEF PROCtest', 'PRINT "body"'])
    assert 'missing ENDPROC' in output
    assert 'after' not in output

def test_mini_retains_implicit_return_at_proc_eof():
    output, _ = run(['PRINT "before"', 'PROCtest', 'PRINT "after"', 'END',
                     'DEF PROCtest', 'PRINT "body"'], 'mini')
    assert output.splitlines() == ['before', 'body', 'after']

def test_bbc_endproc_returns_to_caller():
    output, _ = run(['PRINT "before"', 'PROCtest', 'PRINT "after"', 'END',
                     'DEF PROCtest', 'PRINT "body"', 'ENDPROC'])
    assert output.splitlines() == ['before', 'body', 'after']

def test_bbc_endproc_returns_even_with_later_function_definition():
    output, _ = run(['PROCtest', 'PRINT "after"', 'END',
                     'DEF PROCtest', 'PRINT "body"', 'ENDPROC', 'DEF FNother(n)=n'])
    assert output.splitlines() == ['body', 'after']


@pytest.mark.parametrize('definition', ['DEF PROCtest PRINT "body"', 'DEF PROCtest:PRINT "body"'])
def test_bbc_single_line_proc_may_omit_endproc(definition):
    output, _ = run(['PROCtest', 'PRINT "after"', 'END', definition])
    assert output.splitlines() == ['body', 'after']


def test_bbc_single_line_omission_before_other_definitions():
    output, _ = run(['DEF PROCfirst:PRINT "one"', 'PROCfirst', 'PRINT "after"', 'END',
                     'DEF PROCsecond', 'PRINT "two"', 'ENDPROC'])
    assert output.splitlines() == ['one', 'after']

@pytest.mark.parametrize('hint,locked', [('bbc', False), ('mini', True)])
def test_effective_bbc_hint_or_locked_selection_rejects_end_def(tmp_path, hint, locked):
    runtime = interpreter('mini' if hint == 'bbc' else 'bbc')
    runtime.config.dialect_locked = locked
    path = tmp_path/'hinted.bas'
    path.write_text('1 REM dialect: '+hint+'\n'+
                    '\n'.join(f'{n*10} {line}' for n,line in enumerate(SOURCE,1)))
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        assert not runtime.load(str(path), announce=False)
    assert runtime.config.dialect == 'bbc'


@pytest.mark.parametrize('n,result', [(0, 1), (5, 120)])
def test_bbc_multiline_fn_keeps_both_returning_if_branches(n, result):
    output, _ = run([f'PRINT FNfact({n})', 'END', 'DEF FNfact(n)', 'IF n<1 THEN',
                     '=1', 'ELSE', '=n*FNfact(n-1)', 'ENDIF'])
    assert output.strip() == str(result)
