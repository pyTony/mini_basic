"""Detect whether this process can open a GUI window (pygame/SDL).

Used to avoid auto-enabling pygame on pure text sessions (Linux console,
SSH without X11/Wayland, or explicit env overrides).
"""
from __future__ import annotations

import os
import sys
from typing import Optional


def session_supports_gui() -> bool:
    """Return True if auto-opening a pygame window is appropriate.

    Explicit ``--display pygame`` still works via ``display_locked``; this only
    gates *automatic* upgrades from terminal → pygame.

    Rules:
    - ``MINIBASIC_NO_GRAPHICS=1`` or ``MINIBASIC_DISPLAY=terminal`` → no GUI
    - Linux/BSD without ``DISPLAY`` and without ``WAYLAND_DISPLAY`` → no GUI
    - ``SDL_VIDEODRIVER=dummy`` is *not* treated as no-GUI (tests use dummy + pygame)
    - Windows / macOS default to GUI available unless env override
    """
    if _env_forces_text_only():
        return False
    platform = sys.platform
    if platform.startswith('linux') or platform.startswith('freebsd') or platform == 'openbsd':
        if not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'):
            return False
    return True


def _env_forces_text_only() -> bool:
    no_gfx = os.environ.get('MINIBASIC_NO_GRAPHICS', '').strip().lower()
    if no_gfx in ('1', 'true', 'yes', 'on'):
        return True
    display = os.environ.get('MINIBASIC_DISPLAY', '').strip().lower()
    if display in ('terminal', 'text', 'none', 'null'):
        return True
    return False


def terminal_interrupt_pending() -> Optional[str]:
    """Non-blocking check of the launching terminal for Ctrl+C or ESC.

    Returns ``'ctrl-c'``, ``'esc'``, or ``None`` if no interrupt key is waiting.
    Safe to call when stdin is not a TTY (always returns None).
    """
    try:
        if not sys.stdin.isatty():
            return None
    except Exception:
        return None

    if sys.platform == 'win32':
        return _windows_interrupt_pending()
    return _posix_interrupt_pending()


def _windows_interrupt_pending() -> Optional[str]:
    try:
        import msvcrt
    except ImportError:
        return None
    try:
        while msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch in ('\x00', '\xe0'):
                # Arrow / function key prefix — discard second half
                if msvcrt.kbhit():
                    msvcrt.getwch()
                continue
            if ch == '\x03':
                return 'ctrl-c'
            if ch == '\x1b':
                return 'esc'
            # Other keys: leave them discarded so animation loops do not buffer junk
        return None
    except Exception:
        return None


def _posix_interrupt_pending() -> Optional[str]:
    try:
        import select
    except ImportError:
        return None
    try:
        fd = sys.stdin.fileno()
    except Exception:
        return None
    try:
        ready, _, _ = select.select([sys.stdin], [], [], 0)
        if not ready:
            return None
        # Read one byte without blocking the rest of the stream too aggressively
        data = os.read(fd, 1)
        if not data:
            return None
        if data == b'\x03':
            return 'ctrl-c'
        if data == b'\x1b':
            return 'esc'
        return None
    except Exception:
        return None
