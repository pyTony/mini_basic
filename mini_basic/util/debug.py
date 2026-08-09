"""Shared debug printing for the whole mini_basic package.

``dprint`` is available everywhere::

    from mini_basic.util.debug import dprint   # preferred free form
    from mini_basic import dprint               # package re-export

    dprint("EXEC:", line)                     # uses active config / env
    dprint(config, "MOVE", x, y)              # explicit config (legacy)
    self.dprint("ON CORE MIXIN")              # interpreter method

Enable with CLI ``--debug`` / ``--debug-filter`` (sets ``InterpreterConfig`` and
active context), or env ``MINI_BASIC_DEBUG=1`` (optional
``MINI_BASIC_DEBUG_FILTER=substr``).

``--debug`` → stderr + append ``mini_basic.log``
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional, TextIO

# Default log next to CWD (same as historical behaviour).
DEFAULT_LOG_NAME = 'mini_basic.log'

_announced: bool = False
# Last interpreter / CLI config so free modules can dprint without threading config.
_active_config: Any = None


def set_active_debug_config(config: Any) -> None:
    """Register config for bare ``dprint(...)`` calls (no leading config arg)."""
    global _active_config
    _active_config = config


def get_active_debug_config() -> Any:
    return _active_config


def clear_active_debug_config() -> None:
    global _active_config
    _active_config = None


def _env_debug_config() -> Optional[Any]:
    flag = os.environ.get('MINI_BASIC_DEBUG', '').strip().lower()
    if flag not in ('1', 'true', 'yes', 'on'):
        return None
    return SimpleNamespace(
        DEBUG=True,
        DEBUG_FILTER=os.environ.get('MINI_BASIC_DEBUG_FILTER', '') or '',
        DEBUG_LOG=os.environ.get('MINI_BASIC_DEBUG_LOG') or None,
    )


def _looks_like_config(obj: Any) -> bool:
    return (
        obj is not None
        and hasattr(obj, 'DEBUG')
        and (hasattr(obj, 'DEBUG_FILTER') or hasattr(obj, 'dialect'))
    )


def resolve_debug_config(config: Any = None) -> Any:
    if config is not None:
        return config
    if _active_config is not None:
        return _active_config
    return _env_debug_config()


def debug_enabled(config: Any = None) -> bool:
    cfg = resolve_debug_config(config)
    if cfg is None:
        return False
    return bool(getattr(cfg, 'DEBUG', False))


def debug_filter(config: Any = None) -> str:
    cfg = resolve_debug_config(config)
    if cfg is None:
        return ''
    return str(getattr(cfg, 'DEBUG_FILTER', '') or '')


def debug_log_path(config: Any = None) -> Path:
    cfg = resolve_debug_config(config)
    custom = getattr(cfg, 'DEBUG_LOG', None) if cfg is not None else None
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


def announce_debug(config: Any = None, *, stream: Optional[TextIO] = None) -> None:
    """One-time notice so ``--debug`` is not silent."""
    global _announced
    cfg = resolve_debug_config(config)
    if cfg is None or not debug_enabled(cfg) or _announced:
        return
    _announced = True
    out = stream or sys.stderr
    path = debug_log_path(cfg)
    filt = debug_filter(cfg)
    extra = f' filter={filt!r}' if filt else ''
    try:
        out.write(f'[DEBUG] enabled{extra} → stderr and {path}\n')
        out.flush()
    except Exception:
        pass


def dprint(*args: Any, config: Any = None, sep: str = ' ', end: str = '\n') -> None:
    """Emit a debug line when debug is enabled.

    Forms::

        dprint("a", 1)                 # active config or MINI_BASIC_DEBUG
        dprint(config, "a", 1)         # legacy positional config
        dprint("a", config=config)     # keyword config
    """
    cfg = config
    payload = args
    if cfg is None and args and _looks_like_config(args[0]):
        cfg = args[0]
        payload = args[1:]
    cfg = resolve_debug_config(cfg)
    if cfg is None or not should_emit(cfg, *payload):
        return
    announce_debug(cfg)
    line = format_debug_line(*payload, sep=sep)
    text = line + (end if end is not None else '')
    try:
        sys.stderr.write(text)
        sys.stderr.flush()
    except Exception:
        pass
    try:
        path = debug_log_path(cfg)
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
    'clear_active_debug_config',
    'debug_enabled',
    'debug_filter',
    'debug_log_path',
    'dprint',
    'format_debug_line',
    'get_active_debug_config',
    'reset_announce_for_tests',
    'resolve_debug_config',
    'set_active_debug_config',
    'should_emit',
]
