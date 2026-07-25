"""Step-by-step animal.txt verifier (policy: one program, display=none, no hang)."""
from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout
from unittest.mock import patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig  # noqa: E402

_ANIMAL = os.path.join(_ROOT, 'test', 'corpus', 'bbcsdl', 'games', 'animal.txt')


def _errors(out: str) -> list[str]:
    return [line for line in out.splitlines() if line.startswith('?')]


def step_startup_dim() -> tuple[bool, str]:
    interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
    for line_num, stmt in [
        (10, 'MAX=(HIMEM-LOMEM)/40'),
        (11, 'DIM A$(MAX)'),
        (12, 'PRINT MAX'),
        (13, 'END'),
    ]:
        interp.program[line_num] = stmt
    buf = io.StringIO()
    with redirect_stdout(buf):
        interp.run()
    out = buf.getvalue()
    ok = not _errors(out) and '10000' in out
    return ok, out.strip() or '(no output)'


def step_startup_read_fallback() -> tuple[bool, str]:
    interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
    for line_num, stmt in [
        (10, 'MAX=10'),
        (11, 'DIM A$(MAX)'),
        (15, 'X=0'),
        (16, 'IF X<>0 PROCskip'),
        (17, 'IF A$(0)="" OR LEFT$(A$(1),2)<>"\\Q" THEN FOR I=0 TO 3:READ A$(I):NEXT I'),
        (20, 'PRINT A$(2)'),
        (30, 'END'),
        (100, 'DATA 4,\\Qfly\\N2\\Y3\\,\\Agoldfish,\\Asparrow,'),
        (200, 'DEF PROCskip'),
        (210, 'ENDPROC'),
    ]:
        interp.program[line_num] = stmt
    buf = io.StringIO()
    with redirect_stdout(buf):
        interp.run()
    out = buf.getvalue()
    ok = not _errors(out) and 'goldfish' in out
    return ok, out.strip() or '(no output)'


def _user_fn(interp: BASICInterpreter, name: str):
    """Resolve DEF FN by case-insensitive name (BBC is not case-sensitive)."""
    key = name.strip()
    table = interp.user_functions
    if key in table:
        return table[key]
    lower = key.lower()
    for stored, fn in table.items():
        if stored.lower() == lower:
            return fn
    raise KeyError(key)


def step_fn_strip() -> tuple[bool, str]:
    interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
    interp.load(_ANIMAL)
    interp._prepare_run()
    fn = _user_fn(interp, 'STRIP')
    alba = interp._eval_user_function(fn, ['"albatross"'])
    sparrow = interp._eval_user_function(fn, ['"a sparrow"'])
    ok = alba == 'albatross' and sparrow == 'sparrow'
    return ok, f'STRIP albatross={alba!r} a sparrow={sparrow!r}'


def step_fn_art() -> tuple[bool, str]:
    interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
    interp.load(_ANIMAL)
    interp._prepare_run()
    fn = _user_fn(interp, 'ART')
    elephant = interp._eval_user_function(fn, ['"elephant"'])
    cat = interp._eval_user_function(fn, ['"cat"'])
    ok = elephant == 'an elephant' and cat == 'a cat'
    return ok, f'ART elephant={elephant!r} cat={cat!r}'


def step_fn_query() -> tuple[bool, str]:
    interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
    interp.load(_ANIMAL)
    interp._prepare_run()
    line_nums = sorted(interp.program)
    for ln in line_nums:
        if ln < 200:
            interp.execute_line(ln, interp.program[ln], line_nums)
    errors: list[str] = []

    def traced(msg, line_num, stmt_index=0):
        errors.append(str(msg))

    interp._runtime_error = traced
    with patch.object(interp, '_read_program_input', return_value='y'):
        result = interp._eval_user_function(
            _user_fn(interp, 'QUERY'),
            ['"Are you thinking of an animal ? "'],
        )
    ok = not errors and result == 'Y'
    return ok, f'QUERY={result!r} errors={errors}'


def step_if_main_n_exit() -> tuple[bool, str]:
    interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
    interp.load(_ANIMAL)
    interp._prepare_run()
    errors: list[str] = []

    def traced(msg, line_num, stmt_index=0):
        errors.append(str(msg))

    interp._runtime_error = traced
    line_nums = sorted(interp.program)
    for ln in line_nums:
        if ln < 200:
            with redirect_stdout(io.StringIO()):
                interp.execute_line(ln, interp.program[ln], line_nums)
    main_loop = next(
        ln
        for ln, text in interp.program.items()
        if 'Are you thinking of an animal' in text and 'PROCexit' in text
    )
    inputs = iter(['n', 'n'])

    def read_input(*_a, **_k):
        return next(inputs)

    def stop_wait(*_a, **_k):
        raise KeyboardInterrupt

    buf = io.StringIO()
    with patch.object(interp, '_read_program_input', side_effect=read_input), patch.object(
        interp, '_execute_wait', side_effect=stop_wait,
    ):
        try:
            with redirect_stdout(buf):
                interp.execute_line(main_loop, interp.program[main_loop], line_nums)
        except KeyboardInterrupt:
            pass
    out = buf.getvalue()
    ok = not errors and 'Animals I already know' in out
    return ok, f'errors={errors} has_list={"Animals I already know" in out}'


def step_corpus_style_probe() -> tuple[bool, str]:
    """Like corpus_audit_probe but animal only, loops shortened."""
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', optimization_level=0),
    )
    interp.load(_ANIMAL)
    for line_num in sorted(interp.program):
        upper = interp.program[line_num].strip().upper()
        if upper.startswith('REPEAT'):
            interp.program[line_num] = 'REM audit-once'
        elif upper.startswith('UNTIL'):
            interp.program[line_num] = 'REM audit-end'
        elif upper.startswith('WAIT'):
            interp.program[line_num] = 'REM audit-wait'
    errors: list[str] = []

    def track(msg, *a, **k):
        text = str(msg)
        if text.startswith('?'):
            errors.append(text.split(' at line')[0])

    buf = io.StringIO()
    with patch.object(interp, '_runtime_error', track), patch('time.sleep'), patch.object(
        interp, '_read_program_input', return_value='3',
    ), patch.object(interp, '_read_get_char', return_value=32):
        with redirect_stdout(buf):
            interp.run()
    unique = sorted(set(errors))
    ok = not unique
    return ok, '; '.join(unique) if unique else 'no errors'


STEPS = [
    ('1 startup DIM A$(MAX)', step_startup_dim),
    ('2 IF/READ fallback', step_startup_read_fallback),
    ('3 FNstrip', step_fn_strip),
    ('4 FNart', step_fn_art),
    ('5 FNquery', step_fn_query),
    ('6 IF main N -> PROCexit', step_if_main_n_exit),
    ('7 corpus-style probe', step_corpus_style_probe),
]


def main() -> int:
    failed = 0
    for label, fn in STEPS:
        try:
            ok, detail = fn()
        except Exception as exc:
            ok, detail = False, str(exc)
        mark = 'OK' if ok else 'FAIL'
        print(f'{mark} {label}: {detail}')
        if not ok:
            failed += 1
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())