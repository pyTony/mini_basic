"""Shared debug printing for modular runtime mixins.

``dprint`` used to live only on ``RuntimeIoMixin`` and wrote solely to
``mini_basic.log`` (often with a broken ``args[0]+\"\\n\"``). Mixins in
execution/expr/program need a core-level helper, and ``--debug`` must show
on the console.

Usage from any mixin method::

    self.dprint("EXEC:", line)          # prefers interpreter method
    from mini_basic.util.debug import dprint
    dprint(config, "MOVE args", x, y)   # free function when no self

``--debug`` → stderr + append ``mini_basic.log``
``--debug-filter substr`` → only lines containing substr
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional, TextIO

# Default log next to CWD (same as historical behaviour).
DEFAULT_LOG_NAME = 'mini_basic.log'

_announced: bool = False


def debug_enabled(config: Any) -> bool:
    return bool(getattr(config, 'DEBUG', False))


def debug_filter(config: Any) -> str:
    return str(getattr(config, 'DEBUG_FILTER', '') or '')


def debug_log_path(config: Any = None) -> Path:
    custom = getattr(config, 'DEBUG_LOG', None) if config is not None else None
    if custom:
        return Path(str(custom))
    return Path.cwd() / DEFAULT_LOG_NAME


def format_debug_line(*args: Any, sep: str = ' ') -> str:
    return sep.join(str(a) for a in args)


def should_emit(config: Any, *args: Any) -> bool:
    if not debug_enabled(config):
        return False
    filt = debug_filter(config)
    if not filt:
        return True
    return any(filt in str(a) for a in args)


def announce_debug(config: Any, *, stream: Optional[TextIO] = None) -> None:
    """One-time notice so ``--debug`` is not silent."""
    global _announced
    if not debug_enabled(config) or _announced:
        return
    _announced = True
    out = stream or sys.stderr
    path = debug_log_path(config)
    filt = debug_filter(config)
    extra = f' filter={filt!r}' if filt else ''
    try:
        out.write(f'[DEBUG] enabled{extra} → stderr and {path}\n')
        out.flush()
    except Exception:
        pass


def dprint(config: Any, *args: Any, sep: str = ' ', end: str = '\n') -> None:
    """Emit a debug line if ``config.DEBUG`` is set.

    Parameters
    ----------
    config:
        ``InterpreterConfig`` (or any object with DEBUG / DEBUG_FILTER).
    *args:
        Values joined like ``print``.
    """
    if not should_emit(config, *args):
        return
    announce_debug(config)
    line = format_debug_line(*args, sep=sep)
    text = line + (end if end is not None else '')
    # Console: stderr so BASIC PRINT on stdout stays clean
    try:
        sys.stderr.write(text)
        sys.stderr.flush()
    except Exception:
        pass
    # Persist for long runs / pygame windows that bury the terminal
    try:
        path = debug_log_path(config)
        with open(path, 'a', encoding='utf-8') as fh:
            fh.write(text if text.endswith('\n') else text + '\n')
    except Exception:
        pass


def reset_announce_for_tests() -> None:
    """Test helper: allow announce_debug to fire again."""
    global _announced
    _announced = False


__all__ = [
    'DEFAULT_LOG_NAME',
    'announce_debug',
    'debug_enabled',
    'debug_filter',
    'debug_log_path',
    'dprint',
    'format_debug_line',
    'reset_announce_for_tests',
    'should_emit',
]
