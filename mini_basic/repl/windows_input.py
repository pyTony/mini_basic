"""Windows console REPL / line input with history, Tab completion, and word editing.

Editing keys (Windows console + common VT sequences):
  Left/Right, Up/Down history
  Home / End (or Ctrl+A / Ctrl+E)
  Ctrl+Left / Ctrl+Right — move by word
  Ctrl+Backspace / Ctrl+W — delete previous word
  Delete / Ctrl+Delete — delete char / next word
  Ctrl+K — kill to end of line
  Ctrl+U — kill to start of line

Paste: console paste injects characters; multi-line pastes submit on each CR
so numbered BASIC lines enter one per line (standard interactive BASIC).
"""
from __future__ import annotations

import sys
import time
from typing import Callable, List, Optional, Tuple

from ..type_system import ProgramExit


class LineEditCancelled(Exception):
    """Esc or Ctrl+C abandoned an EDIT/AUTO line; do not store the buffer."""
from .completion import (
    TabCompletionCycle,
    accept_unique_completion,
    advance_tab_completion,
    compute_matches,
)

_COMPLETER_DELIMS = ' \t\n;'
_WORD_BREAK = frozenset(' \t\n;,:()+-*/=<>"\'')


def _word_left(buffer: List[str], cursor: int) -> int:
    if cursor <= 0:
        return 0
    i = cursor - 1
    while i > 0 and buffer[i] in _WORD_BREAK:
        i -= 1
    while i > 0 and buffer[i - 1] not in _WORD_BREAK:
        i -= 1
    return i


def _word_right(buffer: List[str], cursor: int) -> int:
    n = len(buffer)
    if cursor >= n:
        return n
    i = cursor
    while i < n and buffer[i] not in _WORD_BREAK:
        i += 1
    while i < n and buffer[i] in _WORD_BREAK:
        i += 1
    return i


def parse_special_key(getwch, prefix: str) -> Optional[str]:
    """Map Windows / VT special key sequences to action names."""
    # Windows scan codes after 0x00 / 0xE0
    legacy = {
        'K': 'left',
        'M': 'right',
        'H': 'up',
        'P': 'down',
        'G': 'home',
        'O': 'end',
        'S': 'delete',
        's': 'word_left',   # Ctrl+Left
        't': 'word_right',  # Ctrl+Right
        '\x93': 'word_delete',  # Ctrl+Delete (some consoles)
    }
    if prefix in ('\x00', '\xe0'):
        code = getwch()
        # Ctrl+Delete often arrives as 0xE0 0x93
        if isinstance(code, str) and len(code) == 1 and ord(code) == 0x93:
            return 'word_delete'
        return legacy.get(code)

    if prefix != '\x1b':
        return None

    try:
        second = getwch()
    except (EOFError, OSError, IndexError, StopIteration):
        return None

    # ESC O H / F = home/end (application mode)
    if second == 'O':
        code = getwch()
        return {
            'D': 'left',
            'C': 'right',
            'A': 'up',
            'B': 'down',
            'H': 'home',
            'F': 'end',
        }.get(code)

    if second != '[':
        return None

    # CSI: collect until letter or ~
    params: List[str] = []
    chunk = ''
    while True:
        try:
            ch = getwch()
        except (EOFError, OSError, IndexError, StopIteration):
            return None
        # CSI params are digits (and ';'); final byte is a letter or '~'.
        # Do not treat ';' as a terminator — it separates multi-param sequences
        # like ESC [ 1 ; 5 D (Ctrl+Left).
        if ch == '~' or (len(ch) == 1 and ch.isalpha()):
            if chunk:
                params.append(chunk)
            final = ch
            break
        if ch == ';':
            params.append(chunk)
            chunk = ''
            continue
        chunk += ch

    # ESC [ H / F
    if final in ('H', 'F'):
        return 'home' if final == 'H' else 'end'
    # ESC [ 1~ home, 4~ end, 3~ delete
    if final == '~' and params:
        return {
            '1': 'home',
            '4': 'end',
            '3': 'delete',
            '7': 'home',
            '8': 'end',
        }.get(params[0])
    # ESC [ 1 ; 5 D = Ctrl+Left
    if final in ('D', 'C', 'A', 'B') and len(params) >= 2 and params[-1] == '5':
        return {
            'D': 'word_left',
            'C': 'word_right',
            'A': 'up',
            'B': 'down',
        }.get(final)
    if final in ('D', 'C', 'A', 'B'):
        return {
            'D': 'left',
            'C': 'right',
            'A': 'up',
            'B': 'down',
        }.get(final)
    return None


# Back-compat alias used by tests / runtime
_windows_arrow_action = parse_special_key


def apply_line_edit(
    action: str,
    buffer: List[str],
    cursor: int,
    *,
    default: str = '',
) -> Tuple[List[str], int, bool]:
    """Apply a named edit action. Returns (buffer, cursor, needs_full_redraw)."""
    redraw = False
    if action == 'left' and cursor > 0:
        cursor -= 1
    elif action == 'right':
        if cursor < len(buffer):
            cursor += 1
        elif not buffer and default:
            buffer[:] = list(default)
            cursor = len(buffer)
            redraw = True
    elif action == 'home':
        cursor = 0
    elif action == 'end':
        cursor = len(buffer)
    elif action == 'word_left':
        cursor = _word_left(buffer, cursor)
    elif action == 'word_right':
        cursor = _word_right(buffer, cursor)
    elif action == 'backspace':
        if cursor > 0:
            del buffer[cursor - 1]
            cursor -= 1
            redraw = True
    elif action == 'delete':
        if cursor < len(buffer):
            del buffer[cursor]
            redraw = True
    elif action == 'word_backspace':
        start = _word_left(buffer, cursor)
        if start < cursor:
            del buffer[start:cursor]
            cursor = start
            redraw = True
    elif action == 'word_delete':
        end = _word_right(buffer, cursor)
        if end > cursor:
            del buffer[cursor:end]
            redraw = True
    elif action == 'kill_end':
        if cursor < len(buffer):
            del buffer[cursor:]
            redraw = True
    elif action == 'kill_start':
        if cursor > 0:
            del buffer[:cursor]
            cursor = 0
            redraw = True
    elif action == 'up' and default:
        buffer[:] = list(default)
        cursor = len(buffer)
        redraw = True
    return buffer, cursor, redraw


def _windows_apply_arrow(
    action: str,
    buffer: List[str],
    cursor: int,
    default: str,
) -> Tuple[List[str], int, bool]:
    """Back-compat for tests expecting (buffer, cursor, redraw) tuple returns."""
    return apply_line_edit(action, buffer, cursor, default=default)


def _completion_word(line: str, cursor: int) -> Tuple[str, int]:
    """Return ``(partial_word, start_index)`` for the token ending at ``cursor``."""
    start = cursor
    while start > 0 and line[start - 1] not in _COMPLETER_DELIMS:
        start -= 1
    return line[start:cursor], start


def _expand_line_for_completion(line: str, expand_abbrev: Callable[[str], str]) -> str:
    expanded = expand_abbrev(line)
    if line.endswith((' ', '\t')) and expanded and not expanded.endswith((' ', '\t')):
        expanded += line[len(line.rstrip()):]
    return expanded


def _apply_tab_completion(
    buffer: List[str],
    cursor: int,
    working_dir: str,
    expand_abbrev: Callable[[str], str],
    cycle: TabCompletionCycle | None,
) -> Tuple[int, TabCompletionCycle | None, bool]:
    """Return ``(new_cursor, cycle, redraw)``."""
    line = ''.join(buffer)
    prefix, start = _completion_word(line, cursor)

    if cycle is not None:
        next_index = (cycle.index + 1) % len(cycle.matches)
        replacement = cycle.matches[next_index]
        cycle = TabCompletionCycle(cycle.matches, next_index, cycle.prefix)
    else:
        expanded = _expand_line_for_completion(line, expand_abbrev)
        matches = compute_matches(working_dir, expanded, prefix)
        replacement, cycle = advance_tab_completion(prefix, matches, None)
        if replacement == prefix:
            return cursor, cycle, False

    buffer[start:cursor] = list(replacement)
    return start + len(replacement), cycle, True


def _apply_accept_completion(
    buffer: List[str],
    cursor: int,
    working_dir: str,
    expand_abbrev: Callable[[str], str],
) -> Tuple[int, bool]:
    """Right-arrow accept: apply the sole extension of the current word, if any."""
    line = ''.join(buffer)
    prefix, start = _completion_word(line, cursor)
    expanded = _expand_line_for_completion(line, expand_abbrev)
    matches = compute_matches(working_dir, expanded, prefix)
    accepted = accept_unique_completion(prefix, matches)
    if accepted is None or accepted == prefix:
        return cursor, False
    buffer[start:cursor] = list(accepted)
    return start + len(accepted), True


def _append_history(history: List[str], line: str) -> None:
    if not line:
        return
    if history and history[-1] == line:
        return
    history.append(line)


def _is_editable_char(ch: str) -> bool:
    if not ch:
        return False
    o = ord(ch[0])
    if o == 9:
        return True
    if o < 32 or o == 127:
        return False
    return True


def _live_tty_getwch(getwch) -> bool:
    """True when *getwch* reads the real console (not a test stub)."""
    if getwch is None:
        return True
    name = getattr(getwch, '__name__', '')
    return name in ('getwch', 'getch', 'posix_getwch')


def _stdin_escape_pending(timeout: float = 0.06) -> bool:
    """True if more bytes follow ESC (arrow / CSI), else a lone Esc key."""
    if sys.platform == 'win32':
        try:
            import msvcrt

            deadline = time.perf_counter() + timeout
            while time.perf_counter() < deadline:
                if msvcrt.kbhit():
                    return True
                time.sleep(0.005)
            return False
        except Exception:
            return False
    try:
        import select

        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        return bool(ready)
    except Exception:
        return False


def _cancel_line_edit() -> None:
    # \\r\\n: POSIX setraw does not map \\n to CR+LF.
    sys.stdout.write('\r\n')
    sys.stdout.flush()
    raise LineEditCancelled()


def windows_line_edit(
    prompt: str,
    *,
    default: str = '',
    getwch=None,
    history: Optional[List[str]] = None,
    idle: Optional[Callable[[], bool]] = None,
    working_dir: Optional[Callable[[], str]] = None,
    expand_abbrev: Optional[Callable[[str], str]] = None,
    use_history: bool = True,
    use_completion: bool = False,
    escape_cancels: bool = False,
) -> str:
    """Shared Windows line editor for REPL and AUTO/EDIT prompts."""
    # Import msvcrt only on the Windows console path. Linux EDIT n reuses this
    # editor with a termios getwch; ``import msvcrt`` there is ImportError,
    # which used to fall back to bare input() and show only the line number.
    msvcrt = None
    if getwch is None or idle is not None:
        if sys.platform == 'win32':
            import msvcrt as msvcrt_mod

            msvcrt = msvcrt_mod

    if getwch is None:
        if not sys.stdin.isatty():
            return input(prompt).rstrip()
        if msvcrt is None:
            raise ImportError('msvcrt is only available on Windows')
        getwch = msvcrt.getwch

    if history is None:
        history = []

    buffer: List[str] = list(default)
    cursor = len(buffer)
    tab_cycle: TabCompletionCycle | None = None
    hist_index = -1

    def place_cursor() -> None:
        column = len(prompt) + cursor + 1
        sys.stdout.write(f'\x1b[{column}G')
        sys.stdout.flush()

    def redraw() -> None:
        sys.stdout.write('\x1b[2K\r' + prompt + ''.join(buffer))
        sys.stdout.flush()
        place_cursor()

    def load_history_entry(index: int) -> None:
        nonlocal buffer, cursor, hist_index
        buffer = list(history[index])
        cursor = len(buffer)
        hist_index = index
        redraw()

    # Prefill default without clearing console history / paste context.
    if default:
        redraw()
    else:
        sys.stdout.write(prompt)
        sys.stdout.flush()

    while True:
        if idle is not None:
            if not idle():
                raise ProgramExit()
            if msvcrt is None or not msvcrt.kbhit():
                time.sleep(0.005)
                continue
        try:
            key = getwch()
        except KeyboardInterrupt:
            if escape_cancels:
                _cancel_line_edit()
            raise

        # Enter
        if key in ('\r', '\n'):
            # Ignore lone LF after CR (Windows paste \r\n)
            if key == '\n' and not buffer and not default:
                continue
            sys.stdout.write('\r\n')
            sys.stdout.flush()
            line = ''.join(buffer)
            if use_history:
                _append_history(history, line)
            return line.rstrip()

        if key == '\x03':
            if escape_cancels:
                _cancel_line_edit()
            raise KeyboardInterrupt

        # Ctrl+A / Ctrl+E
        if key == '\x01':
            buffer, cursor, need = apply_line_edit('home', buffer, cursor)
            place_cursor()
            continue
        if key == '\x05':
            buffer, cursor, need = apply_line_edit('end', buffer, cursor)
            place_cursor()
            continue
        # Ctrl+W / Ctrl+Backspace (often \x7f or \x08 with modifiers already handled)
        if key == '\x17':
            hist_index = -1
            buffer, cursor, need = apply_line_edit('word_backspace', buffer, cursor)
            if need:
                redraw()
            continue
        # Ctrl+K / Ctrl+U
        if key == '\x0b':
            hist_index = -1
            buffer, cursor, need = apply_line_edit('kill_end', buffer, cursor)
            if need:
                redraw()
            continue
        if key == '\x15':
            hist_index = -1
            buffer, cursor, need = apply_line_edit('kill_start', buffer, cursor)
            if need:
                redraw()
            continue

        if use_completion and key == '\t' and working_dir and expand_abbrev:
            cursor, tab_cycle, needs_redraw = _apply_tab_completion(
                buffer, cursor, working_dir(), expand_abbrev, tab_cycle,
            )
            if needs_redraw:
                redraw()
            continue
        tab_cycle = None

        # Backspace
        if key in ('\x08', '\x7f'):
            hist_index = -1
            # Ctrl+Backspace on many Windows terminals is \x7f with empty buffer edge —
            # treat plain backspace; word delete via Ctrl+W or extended key.
            buffer, cursor, need = apply_line_edit('backspace', buffer, cursor)
            if need:
                redraw()
            continue

        if key in ('\x00', '\xe0', '\x1b'):
            if key == '\x1b' and escape_cancels:
                if _live_tty_getwch(getwch) and not _stdin_escape_pending():
                    _cancel_line_edit()
            try:
                action = parse_special_key(getwch, key)
            except KeyboardInterrupt:
                if escape_cancels:
                    _cancel_line_edit()
                raise
            if action is None:
                if escape_cancels and key == '\x1b':
                    _cancel_line_edit()
                continue
            if action == 'up' and use_history and history:
                if hist_index == -1:
                    load_history_entry(len(history) - 1)
                elif hist_index > 0:
                    load_history_entry(hist_index - 1)
                continue
            if action == 'down' and use_history and history and hist_index >= 0:
                if hist_index < len(history) - 1:
                    load_history_entry(hist_index + 1)
                else:
                    hist_index = -1
                    # Restore empty line for new input — do not wipe default edit buffer
                    # when we started with a prefilled EDIT line.
                    if default and not history:
                        buffer = list(default)
                        cursor = len(buffer)
                    else:
                        buffer = []
                        cursor = 0
                    redraw()
                continue
            if action == 'right' and use_completion and working_dir and expand_abbrev:
                if cursor == len(buffer):
                    cursor, needs_redraw = _apply_accept_completion(
                        buffer, cursor, working_dir(), expand_abbrev,
                    )
                    if needs_redraw:
                        redraw()
                        continue
            hist_index = -1
            buffer, cursor, need = apply_line_edit(action, buffer, cursor, default=default)
            if need:
                redraw()
            else:
                place_cursor()
            continue

        if not _is_editable_char(key):
            continue
        hist_index = -1
        buffer.insert(cursor, key)
        cursor += 1
        redraw()


def windows_repl_input(
    prompt: str,
    working_dir: Callable[[], str],
    expand_abbrev: Callable[[str], str],
    getwch=None,
    history: Optional[List[str]] = None,
    idle: Optional[Callable[[], bool]] = None,
) -> str:
    """Read one REPL line with history, Tab completion, and word editing."""
    return windows_line_edit(
        prompt,
        getwch=getwch,
        history=history,
        idle=idle,
        working_dir=working_dir,
        expand_abbrev=expand_abbrev,
        use_history=True,
        use_completion=True,
    )


def windows_editing_input(
    prompt: str,
    default: str = '',
    getwch=None,
) -> str:
    """AUTO/EDIT style single-line editor (prefill default, no Tab completion)."""
    return windows_line_edit(
        prompt,
        default=default,
        getwch=getwch,
        use_history=False,
        use_completion=False,
        escape_cancels=True,
    )


__all__ = [
    'LineEditCancelled',
    'windows_repl_input',
    'windows_editing_input',
    'windows_line_edit',
    'parse_special_key',
    'apply_line_edit',
    '_windows_arrow_action',
    '_windows_apply_arrow',
]
