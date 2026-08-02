"""Windows console REPL input with history and Tab filename completion."""
from __future__ import annotations

import sys
import time
from typing import Callable, List, Optional, Tuple

from ..type_system import ProgramExit
from .completion import (
    TabCompletionCycle,
    accept_unique_completion,
    advance_tab_completion,
    compute_matches,
)

_COMPLETER_DELIMS = ' \t\n;'


def _windows_arrow_action(getwch, prefix: str) -> Optional[str]:
    legacy = {
        'K': 'left',
        'M': 'right',
        'H': 'up',
        'P': 'down',
    }
    if prefix in ('\x00', '\xe0'):
        code = getwch()
        return legacy.get(code)

    if prefix != '\x1b':
        return None

    try:
        second = getwch()
    except (EOFError, OSError):
        return None
    if second == '[':
        code = getwch()
        return {
            'D': 'left',
            'C': 'right',
            'A': 'up',
            'B': 'down',
        }.get(code)
    if second == 'O':
        code = getwch()
        return {
            'D': 'left',
            'C': 'right',
            'H': 'up',
            'F': 'down',
        }.get(code)
    return None


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


def windows_repl_input(
    prompt: str,
    working_dir: Callable[[], str],
    expand_abbrev: Callable[[str], str],
    getwch=None,
    history: Optional[List[str]] = None,
    idle: Optional[Callable[[], bool]] = None,
) -> str:
    """Read one REPL line with history and Tab filename completion on Windows."""
    import msvcrt  # noqa: F811 — used for getwch default and kbhit polling

    if getwch is None:
        if not sys.stdin.isatty():
            return input(prompt)
        getwch = msvcrt.getwch

    if history is None:
        history = []

    buffer: List[str] = []
    cursor = 0
    tab_cycle: TabCompletionCycle | None = None
    hist_index = -1

    def place_cursor() -> None:
        column = len(prompt) + cursor + 1
        sys.stdout.write(f'\x1b[{column}G')
        sys.stdout.flush()

    def redraw() -> None:
        sys.stdout.write('\x1b[2K\r' + prompt + ''.join(buffer))
        place_cursor()

    def load_history_entry(index: int) -> None:
        nonlocal buffer, cursor, hist_index
        buffer = list(history[index])
        cursor = len(buffer)
        hist_index = index
        redraw()

    sys.stdout.write(prompt)
    sys.stdout.flush()

    while True:
        if idle is not None:
            if not idle():
                raise ProgramExit()
            if not msvcrt.kbhit():
                time.sleep(0.005)
                continue
        key = getwch()
        if key in ('\r', '\n'):
            sys.stdout.write('\n')
            sys.stdout.flush()
            line = ''.join(buffer)
            _append_history(history, line)
            return line
        if key == '\x03':
            raise KeyboardInterrupt
        if key == '\t':
            cursor, tab_cycle, needs_redraw = _apply_tab_completion(
                buffer,
                cursor,
                working_dir(),
                expand_abbrev,
                tab_cycle,
            )
            if needs_redraw:
                redraw()
            continue
        tab_cycle = None
        if key in ('\x08', '\x7f'):
            hist_index = -1
            if cursor > 0:
                del buffer[cursor - 1]
                cursor -= 1
                redraw()
            continue
        if key in ('\x00', '\xe0', '\x1b'):
            action = _windows_arrow_action(getwch, key)
            if action == 'left' and cursor > 0:
                cursor -= 1
                place_cursor()
            elif action == 'right':
                if cursor == len(buffer):
                    cursor, needs_redraw = _apply_accept_completion(
                        buffer,
                        cursor,
                        working_dir(),
                        expand_abbrev,
                    )
                    if needs_redraw:
                        tab_cycle = None
                        redraw()
                        continue
                if cursor < len(buffer):
                    cursor += 1
                    place_cursor()
            elif action == 'up' and history:
                if hist_index == -1:
                    load_history_entry(len(history) - 1)
                elif hist_index > 0:
                    load_history_entry(hist_index - 1)
            elif action == 'down' and history and hist_index >= 0:
                if hist_index < len(history) - 1:
                    load_history_entry(hist_index + 1)
                else:
                    hist_index = -1
                    buffer = []
                    cursor = 0
                    redraw()
            continue
        # Drop C0 controls (e.g. Ctrl+S = U+0013) so they never enter BASIC source.
        if key and len(key) == 1:
            o = ord(key)
            if o < 32 or o == 127:
                continue
        hist_index = -1
        buffer.insert(cursor, key)
        cursor += 1
        redraw()


__all__ = ['windows_repl_input']
