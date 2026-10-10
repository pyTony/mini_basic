"""Step-by-step wheel.txt verifier (policy: display=none, no hang)."""
from __future__ import annotations

import os
import sys
from unittest.mock import patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig  # noqa: E402

_WHEEL = os.path.join(_ROOT, 'test', 'corpus', 'bbcsdl', 'graphics', 'wheel.txt')


def _load_once() -> BASICInterpreter:
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', optimization_level=0),
    )
    interp.load(_WHEEL)
    for line_num in sorted(interp.program):
        upper = interp.program[line_num].strip().upper()
        if upper.startswith('REPEAT') and 'WAIT' not in upper:
            interp.program[line_num] = 'REM audit-once'
        elif upper.startswith('UNTIL FALSE'):
            interp.program[line_num] = 'REM audit-end'
        elif 'REPEAT WAIT' in upper:
            interp.program[line_num] = 'REM audit-wait'
    return interp


def step_spoke_coordinates() -> tuple[bool, str]:
    """FOR loop leaves non-zero SIN/COS coordinates for the disc positions. ('spoke' here is historical name for the radial positions; actual program draws coloured discs/circles, no spokes.)"""
    interp = _load_once()
    errors: list[str] = []

    def track(msg, *a, **k):
        text = str(msg)
        if text.startswith('?'):
            errors.append(text.split(' at line')[0])

    with patch.object(interp, '_runtime_error', track), patch('time.sleep'):
        interp.run()
    x1 = interp.int_variables.get('X1') or interp.int_variables.get('x1%')
    y1 = interp.int_variables.get('Y1') or interp.int_variables.get('y1%')
    if x1 is None or y1 is None:
        return False, f'errors={errors} x1/y1 missing'
    ok = not errors and abs(int(y1)) > 50
    return ok, f'errors={errors} x1%={int(x1)} y1%={int(y1)}'


def step_corpus_style_probe() -> tuple[bool, str]:
    interp = _load_once()
    errors: list[str] = []

    def track(msg, *a, **k):
        text = str(msg)
        if text.startswith('?'):
            errors.append(text.split(' at line')[0])

    with patch.object(interp, '_runtime_error', track), patch('time.sleep'):
        interp.run()
    unique = sorted(set(errors))
    ok = not unique
    return ok, '; '.join(unique) if unique else 'no errors'


STEPS = [
    ('1 spoke SINRAD/COSRAD loop', step_spoke_coordinates),
    ('2 corpus-style probe', step_corpus_style_probe),
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