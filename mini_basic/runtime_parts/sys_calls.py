"""SYS statement: a small table of known BBCSDL / BB4W calls.

BBCSDL programs call SDL (and BB4W programs call Windows) through ``SYS``.
mini_basic has no BBCSDL window or address space, so instead of a general
foreign-function bridge it implements the handful of calls demos use for
timing and screen size. Any other name reports ``? Out of scope``.

    SYS "SDL_GetTicks" TO t%
    SYS name$ TO t%
    SYS "SDL_GetCurrentDisplayMode", 0, mode{}
"""
from __future__ import annotations

import re
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

_START = time.monotonic()

# Trailing ``TO var`` (canonicalized entry may glue it: ``GetTicks$TO T0%``).
_RE_SYS_TO = re.compile(
    r'(?<![A-Za-z0-9_])TO\s*([A-Za-z_@][A-Za-z0-9_@.]*(?:%%|%|\$|&|#|!)?)\s*$'
)

_DEFAULT_DESKTOP = (1920, 1080)


def _ticks_ms(interp: Any, args: List[str]) -> int:
    return int((time.monotonic() - _START) * 1000) & 0xFFFFFFFF


def _perf_counter(interp: Any, args: List[str]) -> int:
    return time.perf_counter_ns()


def _perf_frequency(interp: Any, args: List[str]) -> int:
    return 1_000_000_000


def _delay(interp: Any, args: List[str]) -> int:
    if args:
        ms = float(interp._eval_numeric(args[0]))
        if ms > 0:
            time.sleep(ms / 1000.0)
    return 0


def _desktop_size() -> Tuple[int, int]:
    # Only ask SDL when the pygame display is already in use (no import banner).
    pygame = sys.modules.get('pygame')
    if pygame is None:
        return _DEFAULT_DESKTOP
    try:
        if not pygame.display.get_init():
            pygame.display.init()
        sizes = pygame.display.get_desktop_sizes()
        if sizes and sizes[0][0] > 0 and sizes[0][1] > 0:
            return int(sizes[0][0]), int(sizes[0][1])
    except Exception:
        pass
    return _DEFAULT_DESKTOP


def _display_mode(interp: Any, args: List[str]) -> int:
    """SDL_DisplayMode {format, w, h, refresh_rate, driverdata} into a struct."""
    if len(args) < 2:
        raise ValueError('SYS display mode needs a structure argument')
    match = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\{\s*\}\s*$', args[1])
    if not match:
        raise ValueError('SYS display mode needs a structure argument')
    sname = interp._normalize_identifier(match.group(1))
    members = list(interp.struct_defs.get(sname, {}))
    if not members:
        raise ValueError(f'unknown structure {sname}{{}}')
    width, height = _desktop_size()
    values = [0, width, height, 60, 0]
    for mkey, value in zip(members, values):
        kind = interp.struct_defs[sname][mkey]
        interp.struct_members[f'{sname}.{mkey}'] = (
            '' if kind == 'str' else (int(value) if kind == 'int' else float(value))
        )
    return 0


SYS_CALLS: Dict[str, Callable[[Any, List[str]], int]] = {
    'SDL_GETTICKS': _ticks_ms,
    'SDL_GETTICKS64': _ticks_ms,
    'TIMEGETTIME': _ticks_ms,
    'GETTICKCOUNT': _ticks_ms,
    'SDL_GETPERFORMANCECOUNTER': _perf_counter,
    'SDL_GETPERFORMANCEFREQUENCY': _perf_frequency,
    'SDL_DELAY': _delay,
    'SLEEP': _delay,
    'SDL_GETCURRENTDISPLAYMODE': _display_mode,
    'SDL_GETDESKTOPDISPLAYMODE': _display_mode,
}


def split_sys_statement(rest: str) -> Tuple[str, List[str], Optional[str]]:
    """``"name", a, b TO v`` → (name expression, [a, b], 'v')."""
    target: Optional[str] = None
    match = _RE_SYS_TO.search(rest)
    if match and rest.count('"', 0, match.start()) % 2 == 0:
        target = match.group(1)
        rest = rest[: match.start()]
    parts = [p.strip() for p in _split_top_level(rest)]
    if not parts or not parts[0]:
        raise ValueError('SYS needs a function name')
    return parts[0], parts[1:], target


def _split_top_level(text: str) -> List[str]:
    out: List[str] = []
    depth = 0
    in_str = False
    start = 0
    for i, ch in enumerate(text):
        if ch == '"':
            in_str = not in_str
        elif in_str:
            continue
        elif ch in '({[':
            depth += 1
        elif ch in ')}]':
            depth -= 1
        elif ch == ',' and depth == 0:
            out.append(text[start:i])
            start = i + 1
    out.append(text[start:])
    return out


def execute_sys(interp: Any, rest: str) -> Optional[str]:
    """Run ``SYS``; return an error message for an unsupported call, else None."""
    name_expr, args, target = split_sys_statement(rest)
    name = str(interp._eval_string_expr(name_expr)).strip()
    handler = SYS_CALLS.get(name.upper())
    if handler is None:
        return f'? Out of scope: SYS (RISC OS / OS call): "{name}" not supported'
    result = handler(interp, args)
    if target:
        interp._assign(target, str(int(result)))
    return None
