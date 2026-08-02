"""Interactive HELP browser with its own HELP> prompt and topic menu."""
from __future__ import annotations

import sys
from typing import Callable, List, Optional, Tuple

from .help_topics import (
    HELP_MENU_ITEMS,
    normalize_help_topic,
    print_help_topic,
)

ReadLineFn = Callable[[str], str]

_HELP_MENU_WORDS = frozenset({'index', 'menu', 'topics', 'list', '?'})

_MENU_PROMPT = 'HELP menu> '
_TOPIC_PROMPT = 'HELP> '


def _help_prompt(at_menu: bool) -> str:
    return _MENU_PROMPT if at_menu else _TOPIC_PROMPT


def _print_help_menu(selected: int = 1) -> None:
    print('=== HELP menu ===')
    for index, (name, summary) in enumerate(HELP_MENU_ITEMS, start=1):
        marker = '>' if index == selected else ' '
        print(f' {marker} {index:2} {name:<12} {summary}')
    print()
    count = len(HELP_MENU_ITEMS)
    print(f'  1-{count} open topic   empty line returns to BASIC >')
    if sys.platform == 'win32' and sys.stdin.isatty():
        print('  Up/Down: move highlight   Enter: open selection')


def _print_topic_hint() -> None:
    count = len(HELP_MENU_ITEMS)
    print(f'  0 menu   1-{count} jump   empty line returns to BASIC >')


def _open_topic(
    topic: str,
    *,
    print_dialects: Optional[Callable[[], None]],
    selected: int,
) -> Tuple[int, bool]:
    print_help_topic(topic, print_dialects=print_dialects)
    index = next(
        (i + 1 for i, (name, _) in enumerate(HELP_MENU_ITEMS) if name == topic),
        selected,
    )
    _print_topic_hint()
    return index, False


def _menu_number_choice(text: str) -> Optional[int]:
    stripped = text.strip()
    if not stripped.isdigit():
        return None
    return int(stripped)


def _execute_help_command(
    text: str,
    *,
    print_dialects: Optional[Callable[[], None]],
    at_menu: bool,
    selected: int,
) -> Tuple[str, int, bool]:
    """Return ``(action, new_selected, at_menu)`` — action is leave|menu|noop."""
    token = text.strip().lower()
    if not token:
        return 'leave', selected, at_menu

    number = _menu_number_choice(text)

    if at_menu:
        if token in _HELP_MENU_WORDS:
            return 'menu', max(1, min(selected, len(HELP_MENU_ITEMS))), True
        if number is not None:
            if number == 0:
                return 'menu', selected, True
            if 1 <= number <= len(HELP_MENU_ITEMS):
                topic = HELP_MENU_ITEMS[number - 1][0]
                index, viewing = _open_topic(
                    topic,
                    print_dialects=print_dialects,
                    selected=number,
                )
                return 'noop', index, viewing
            print(f'? Pick 1-{len(HELP_MENU_ITEMS)}')
            return 'noop', selected, True
        print(f'? At menu use 1-{len(HELP_MENU_ITEMS)} (numbered menu)')
        return 'noop', selected, True

    # Viewing a topic: 0 returns to menu; 1-N jumps to another topic.
    if token in _HELP_MENU_WORDS or (number is not None and number == 0):
        return 'menu', max(1, min(selected, len(HELP_MENU_ITEMS))), True
    if number is not None and 1 <= number <= len(HELP_MENU_ITEMS):
        topic = HELP_MENU_ITEMS[number - 1][0]
        index, viewing = _open_topic(
            topic,
            print_dialects=print_dialects,
            selected=number,
        )
        return 'noop', index, viewing
    if number is not None:
        print(f'? Pick 0 for menu or 1-{len(HELP_MENU_ITEMS)} to jump')
        return 'noop', selected, False

    topic = normalize_help_topic(text)
    if topic is None or topic == 'INDEX':
        print(f'? Use 0 for menu or 1-{len(HELP_MENU_ITEMS)} to jump')
        return 'noop', selected, False
    index, viewing = _open_topic(
        topic,
        print_dialects=print_dialects,
        selected=selected,
    )
    return 'noop', index, viewing


def _help_arrow_action(getwch, prefix: str) -> Optional[str]:
    if prefix in ('\x00', '\xe0'):
        return {'H': 'up', 'P': 'down'}.get(getwch())
    if prefix != '\x1b':
        return None
    try:
        second = getwch()
    except (EOFError, OSError):
        return None
    if second == '[':
        return {'A': 'up', 'B': 'down'}.get(getwch())
    return None


def _read_help_line_windows(
    prompt: str,
    *,
    at_menu: bool,
    selected: int,
    redraw_menu: Callable[[int], None],
) -> Tuple[str, int]:
    """Read HELP> with optional Up/Down menu navigation on Windows."""
    import msvcrt

    if not sys.stdin.isatty():
        return input(prompt), selected

    buffer: List[str] = []
    cursor = 0
    highlight = selected

    def redraw_input() -> None:
        if at_menu:
            redraw_menu(highlight)
        sys.stdout.write('\x1b[2K\r' + prompt + ''.join(buffer))
        column = len(prompt) + cursor + 1
        sys.stdout.write(f'\x1b[{column}G')
        sys.stdout.flush()

    redraw_input()

    while True:
        key = msvcrt.getwch()
        if key in ('\r', '\n'):
            sys.stdout.write('\n')
            sys.stdout.flush()
            if at_menu and not buffer:
                return str(highlight), highlight
            return ''.join(buffer), highlight
        if key == '\x03':
            raise KeyboardInterrupt
        if key in ('\x08', '\x7f'):
            if cursor > 0:
                del buffer[cursor - 1]
                cursor -= 1
                redraw_input()
            continue
        if at_menu and key in ('\x00', '\xe0', '\x1b'):
            action = _help_arrow_action(msvcrt.getwch, key)
            if action == 'up':
                highlight = max(1, highlight - 1)
                redraw_input()
            elif action == 'down':
                highlight = min(len(HELP_MENU_ITEMS), highlight + 1)
                redraw_input()
            continue
        buffer.insert(cursor, key)
        cursor += 1
        redraw_input()


def _default_read_line(
    prompt: str,
    *,
    at_menu: bool,
    selected: int,
) -> Tuple[str, int]:
    if sys.platform == 'win32' and sys.stdin.isatty() and at_menu:
        try:
            return _read_help_line_windows(
                prompt,
                at_menu=at_menu,
                selected=selected,
                redraw_menu=_print_help_menu,
            )
        except (ImportError, OSError, ValueError):
            pass
    line = input(prompt)
    return line, selected


def run_help_browser(
    start_topic: str = '',
    *,
    read_line: Optional[ReadLineFn] = None,
    print_dialects: Optional[Callable[[], None]] = None,
) -> None:
    """Run the HELP> sub-shell until the user leaves (empty line)."""
    selected = 1
    at_menu = True

    canonical = normalize_help_topic(start_topic) if start_topic.strip() else None
    if canonical is not None and canonical != 'INDEX':
        selected, at_menu = _open_topic(
            canonical,
            print_dialects=print_dialects,
            selected=next(
                (i + 1 for i, (name, _) in enumerate(HELP_MENU_ITEMS) if name == canonical),
                1,
            ),
        )
    else:
        _print_help_menu(selected=selected)

    while True:
        prompt = _help_prompt(at_menu)
        try:
            if read_line is not None:
                text = read_line(prompt)
                new_selected = selected
            else:
                text, new_selected = _default_read_line(
                    prompt,
                    at_menu=at_menu,
                    selected=selected,
                )
            selected = new_selected

            action, selected, at_menu = _execute_help_command(
                text,
                print_dialects=print_dialects,
                at_menu=at_menu,
                selected=selected,
            )
            if action == 'leave':
                return
            if action == 'menu':
                at_menu = True
                _print_help_menu(selected=selected)
        except EOFError:
            print()
            return
        except KeyboardInterrupt:
            print()
            return


__all__ = ['run_help_browser']
