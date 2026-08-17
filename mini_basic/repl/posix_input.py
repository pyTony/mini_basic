"""POSIX TTY line editor for EDIT/AUTO (Termux, WSL, Linux).

Reuses the Windows line-edit keymap (arrows, Home/End, word keys) with a
termios cbreak ``getwch``. GNU readline's insert_text + redisplay doubles the
prefilled line on WSL; this path draws the buffer once.
"""
from __future__ import annotations

import sys
from typing import Callable, Optional

from .windows_input import LineEditCancelled, windows_line_edit


def posix_getwch() -> str:
    """Read one Unicode character from a raw TTY (full UTF-8, not one byte)."""
    buf = getattr(sys.stdin, 'buffer', None)
    if buf is None:
        ch = sys.stdin.read(1)
        if ch == '':
            raise EOFError
        return ch
    first = buf.read(1)
    if not first:
        raise EOFError
    lead = first[0]
    if lead < 0x80:
        return first.decode('ascii')
    if 0xC2 <= lead <= 0xDF:
        need = 1
    elif 0xE0 <= lead <= 0xEF:
        need = 2
    elif 0xF0 <= lead <= 0xF7:
        need = 3
    else:
        return first.decode('latin-1')
    rest = buf.read(need)
    raw = first + rest
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('latin-1', errors='replace')


def posix_editing_input(
    prompt: str,
    default: str = '',
    getwch: Optional[Callable[[], str]] = None,
) -> str:
    """Prefill *default* and allow arrow-key editing on a POSIX TTY."""
    if getwch is not None:
        return windows_line_edit(
            prompt,
            default=default,
            getwch=getwch,
            use_history=False,
            use_completion=False,
            escape_cancels=True,
        )

    if not sys.stdin.isatty():
        raise OSError('stdin is not a TTY')

    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        # Raw so Ctrl+C is a character (\\x03), not SIGINT / REPL Goodbye.
        tty.setraw(fd)
        try:
            return windows_line_edit(
                prompt,
                default=default,
                getwch=posix_getwch,
                use_history=False,
                use_completion=False,
                escape_cancels=True,
            )
        except KeyboardInterrupt:
            sys.stdout.write('\n')
            sys.stdout.flush()
            raise LineEditCancelled()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


__all__ = ['posix_editing_input', 'posix_getwch']
