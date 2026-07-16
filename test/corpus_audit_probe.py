"""Probe CORPUS_RUNNABLE ALL list; write audit results (no infinite loops)."""
from __future__ import annotations

import test_logging
test_logging.setup_logging()

import gc
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from pathlib import Path
from unittest.mock import patch

_PROBE_TIMEOUT_S = 45

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

from mini_basic import BASICInterpreter, InterpreterConfig  # noqa: E402

_CORPUS = _ROOT / 'test' / 'corpus' / 'bbcsdl'
_LIST = _ROOT / 'CORPUS_RUNNABLE.txt'
_AUDIT = _ROOT / 'CORPUS_AUDIT.txt'


def _parse_all_entries(text: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    in_all = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.upper().startswith('ALL '):
            in_all = True
            continue
        if line.upper().startswith('NOT '):
            in_all = False
            continue
        if not in_all:
            continue
        parts = line.split(None, 1)
        name = parts[0]
        folder = parts[1].split()[0] if len(parts) > 1 else ''
        if name.lower().endswith('.txt'):
            entries.append((name, folder))
    return entries


def _shorten_loops(interp: BASICInterpreter) -> None:
    for line_num in sorted(interp.program):
        upper = interp.program[line_num].strip().upper()
        if upper.startswith('REPEAT'):
            interp.program[line_num] = 'REM audit-once'
        elif upper.startswith('UNTIL'):
            interp.program[line_num] = 'REM audit-end'
        elif upper.startswith('WAIT'):
            interp.program[line_num] = 'REM audit-wait'


def _release_probe(interp: BASICInterpreter | None) -> None:
    if interp is None:
        return
    try:
        interp._shutdown_display(hold=False)
    except Exception:
        pass
    try:
        display = getattr(interp, '_display', None)
        if display is not None and hasattr(display, 'end_run'):
            display.end_run()
    except Exception:
        pass
    try:
        from mini_basic.display import ensure_no_pygame_leftovers
        ensure_no_pygame_leftovers()
    except Exception:
        pass
    gc.collect()


def probe_one(name: str, folder: str) -> tuple[bool, list[str]]:
    path = _CORPUS / folder / name
    if not path.is_file():
        return False, ['? missing file']
    interp: BASICInterpreter | None = None
    errors: list[str] = []

    def track(msg, *a, **k):
        text = str(msg)
        if text.startswith('?'):
            errors.append(text.split(' at line')[0])

    def _run() -> None:
        nonlocal interp
        interp = BASICInterpreter(
            InterpreterConfig(
                dialect='bbc',
                display='none',
                optimization_level=0,
                hold_display_open=False,
            )
        )
        interp.load(str(path))
        _shorten_loops(interp)
        with patch.object(interp, '_runtime_error', track), patch('time.sleep'), patch.object(
            interp, '_read_program_input', return_value='3',
        ), patch.object(interp, '_read_get_char', return_value=32):
            interp.run()

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_run)
            future.result(timeout=_PROBE_TIMEOUT_S)
    except FuturesTimeout:
        errors.append(f'? audit timeout ({_PROBE_TIMEOUT_S}s)')
    except MemoryError:
        errors.append('? Out of memory')
    except Exception as exc:
        text = str(exc)
        if 'memory' in text.lower():
            errors.append('? Out of memory')
        else:
            errors.append(f'? {exc}')
    finally:
        _release_probe(interp)
    unique = sorted(set(errors))
    return len(unique) == 0, unique


def main() -> int:
    text = _LIST.read_text(encoding='utf-8')
    entries = _parse_all_entries(text)
    ok: list[str] = []
    fail: list[tuple[str, list[str]]] = []
    for name, folder in entries:
        passed, errs = probe_one(name, folder)
        if passed:
            ok.append(f'{name} {folder}')
        else:
            fail.append((f'{name} {folder}', errs))

    lines = [
        f'# Corpus audit {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        f'# Probed {len(entries)} programs from ALL runnable section (display=none, gc after each)',
        f'OK ({len(ok)})',
        *ok,
        f'FAIL ({len(fail)})',
    ]
    for label, errs in fail:
        lines.append(f'{label} :: {"; ".join(errs[:2])}')
    _AUDIT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines[:20]))
    if len(lines) > 20:
        print(f'... see {_AUDIT}')
    return 0 if not fail else 1


if __name__ == '__main__':
    raise SystemExit(main())
