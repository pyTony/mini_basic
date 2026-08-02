"""Step-by-step soccerball.txt verifier (policy: display=none, no hang)."""
from __future__ import annotations

import os
import sys
from unittest.mock import patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig  # noqa: E402

_SOCCER = os.path.join(_ROOT, 'test', 'corpus', 'bbcsdl', 'graphics', 'soccerball.txt')


def _load_once() -> BASICInterpreter:
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', optimization_level=0),
    )
    interp.load(_SOCCER)
    for line_num in sorted(interp.program):
        upper = interp.program[line_num].strip().upper()
        if upper.startswith('REPEAT'):
            interp.program[line_num] = 'REM audit-once'
        elif upper.startswith('UNTIL'):
            interp.program[line_num] = 'REM audit-end'
        elif upper.startswith('WAIT'):
            interp.program[line_num] = 'REM audit-wait'
    return interp


def step_load_and_read() -> tuple[bool, str]:
    """DATA read loop from soccerball.txt leaves xyz populated."""
    interp = _load_once()
    errors: list[str] = []

    def track(msg, *a, **k):
        text = str(msg)
        if text.startswith('?'):
            errors.append(text.split(' at line')[0])

    with patch.object(interp, '_runtime_error', track), patch('time.sleep'):
        interp.run()
    xyz = interp.array_storage.get(('XYZ', 'float'))
    if xyz is None:
        return False, 'xyz array missing'
    data = xyz[2]
    ok = not errors and len(data) == 3 and len(data[0]) == 60
    sample = float(data[0][0])
    return ok, f'errors={errors} planes={len(data)} points={len(data[0])} xyz(0,0)={sample}'


def step_rotation_changes_tmp() -> tuple[bool, str]:
    """Matrix multiply rotates xyz into tmp (unit test parity)."""
    interp = _load_once()
    errors: list[str] = []

    def track(msg, *a, **k):
        text = str(msg)
        if text.startswith('?'):
            errors.append(text.split(' at line')[0])

    with patch.object(interp, '_runtime_error', track), patch('time.sleep'):
        interp.run()
    xyz = interp.array_storage.get(('XYZ', 'float'))
    tmp = interp.array_storage.get(('TMP', 'float'))
    if xyz is None or tmp is None:
        return False, 'missing xyz/tmp arrays'
    xyz_data = xyz[2]
    tmp_data = tmp[2]
    y_same = abs(float(tmp_data[1][0]) - float(xyz_data[1][0])) < 0.0001
    x_rot = abs(float(tmp_data[0][0]) - float(xyz_data[0][0])) > 0.01
    x_mag = abs(float(tmp_data[0][0])) > 0.01
    ok = not errors and y_same and x_rot and x_mag
    return (
        ok,
        f'errors={errors} y_same={y_same} x_rot={x_rot} '
        f'tmp(0,0)={float(tmp_data[0][0]):.4f} xyz(0,0)={float(xyz_data[0][0]):.4f}',
    )


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
    ('1 load + READ xyz', step_load_and_read),
    ('2 rotation tmp vs xyz', step_rotation_changes_tmp),
    ('3 corpus-style probe', step_corpus_style_probe),
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