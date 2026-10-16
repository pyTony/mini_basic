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

# Keep short: agent/resource-safe. Thread timeouts cannot force-kill work, so
# executor is shut down with wait=False after a timeout (see probe_one).
_PROBE_TIMEOUT_S = 20

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
    """Neutralize common hang sources for a one-shot audit run."""
    for line_num in sorted(interp.program):
        stmt = interp.program[line_num]
        upper = stmt.strip().upper()
        if upper.startswith('REPEAT'):
            interp.program[line_num] = 'REM audit-once'
        elif upper.startswith('UNTIL'):
            interp.program[line_num] = 'REM audit-end'
        elif upper.startswith('WHILE'):
            interp.program[line_num] = 'REM audit-while'
        elif upper.startswith('WEND') or upper.startswith('ENDWHILE'):
            interp.program[line_num] = 'REM audit-wend'
        elif upper.startswith('WAIT'):
            interp.program[line_num] = 'REM audit-wait'
        elif upper.startswith('FOR ') and ' TO ' in upper:
            # Collapse *delay-like* FORs only (large plain numeric TO, no STEP).
            # Preserve same-line colon tail: FOR Z=1 TO 1000:NEXT → FOR Z=1 TO 1:NEXT
            # Do not rewrite geometric loops (FOR X=0 TO A STEP XS:S=X*X) — that
            # broke saucer by setting X=1 while still using I=-P as init guard.
            head, tail = stmt, ''
            depth = 0
            in_string = False
            for i, ch in enumerate(stmt):
                if ch == '"':
                    in_string = not in_string
                elif not in_string:
                    if ch == '(':
                        depth += 1
                    elif ch == ')':
                        depth = max(0, depth - 1)
                    elif ch == ':' and depth == 0:
                        head, tail = stmt[:i], stmt[i:]  # tail includes leading :
                        break
            m = re.match(
                r'^(\s*FOR\s+)([A-Za-z_][\w%]*)(\s*=\s*)(.+?)(\s+TO\s+)(.+?)(\s+STEP\s+(.+))?\s*$',
                head,
                flags=re.IGNORECASE,
            )
            if not m:
                continue
            var = m.group(2)
            to_expr = m.group(6).strip()
            step_part = m.group(7)  # includes leading " STEP …" or None
            step_expr = (m.group(8) or '').strip()
            # Delay-like: FOR Z=1 TO 1000 (no STEP)
            if step_part is None and re.fullmatch(r'\d{3,}', to_expr):
                interp.program[line_num] = (
                    f'{m.group(1)}{var}{m.group(3)}1{m.group(5)}1{tail}'
                )
                continue
            # Pixel-fill loops: FOR X%=0 TO W%-1 / TO 511 (squares.txt).
            # Do *not* match nSlices%-1 / long names (piechart).
            short_wm1 = re.fullmatch(
                r'([A-Za-z_]\w{0,2})%?\s*-\s*1', to_expr, flags=re.IGNORECASE
            )
            if step_part is None and (
                short_wm1 is not None
                or re.fullmatch(r'\d{3,}', to_expr)
                or re.fullmatch(r'\d{3,}\s*-\s*1', to_expr)
            ):
                interp.program[line_num] = (
                    f'{m.group(1)}{var}{m.group(3)}0{m.group(5)}31{tail}'
                )
                continue
            # Saucer outer: FOR X=0 TO A STEP XS (simple STEP id/number only).
            # Skip FOR I=-P TO P STEP 6*YS (complex STEP / signed range).
            if (
                step_part is not None
                and re.fullmatch(r'[A-Za-z_][\w%]*', to_expr)
                and re.fullmatch(r'[A-Za-z_][\w%]*|\d+', step_expr)
                and re.fullmatch(r'0', m.group(4).strip())
            ):
                interp.program[line_num] = (
                    f'{m.group(1)}{var}{m.group(3)}0{m.group(5)}48{step_part}{tail}'
                )


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

    pool = ThreadPoolExecutor(max_workers=1)
    try:
        future = pool.submit(_run)
        try:
            future.result(timeout=_PROBE_TIMEOUT_S)
        except FuturesTimeout:
            errors.append(f'? audit timeout ({_PROBE_TIMEOUT_S}s)')
            # Do not wait for the stuck worker (threads cannot be force-killed).
            pool.shutdown(wait=False, cancel_futures=True)
            pool = None
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
        if pool is not None:
            pool.shutdown(wait=False, cancel_futures=True)
    unique = sorted(set(errors))
    return len(unique) == 0, unique


def main() -> int:
    text = _LIST.read_text(encoding='utf-8')
    entries = _parse_all_entries(text)
    ok: list[str] = []
    fail: list[tuple[str, list[str]]] = []
    for name, folder in entries:
        print(f'… {folder}/{name}', flush=True)
        passed, errs = probe_one(name, folder)
        status = 'OK' if passed else 'FAIL'
        detail = '' if passed else f'  ({"; ".join(errs[:2])})'
        print(f'  {status}{detail}', flush=True)
        if passed:
            ok.append(f'{name} {folder}')
        else:
            fail.append((f'{name} {folder}', errs))
        gc.collect()

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
