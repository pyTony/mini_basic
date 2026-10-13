"""Pure line-numbering / auto-indent logic for :mod:`tools.editor`.

Kept free of any ``tkinter`` import so it can be unit tested without a
display, and so the rules themselves are easy to read in isolation from
the Text-widget plumbing that applies them.
"""
from __future__ import annotations

import re
from typing import Optional, Set, Tuple

INDENT_STEP = 4

# Statements that open an indented block: the line *after* one of these
# (or after a block-form ``IF ... THEN`` with nothing following THEN) is
# indented one step further.
OPENER_KEYWORDS = {'FOR', 'WHILE', 'REPEAT', 'DEF', 'CASE'}

# Statements that close (or momentarily interrupt) a block: typing one of
# these as the first word of a line dedents that line by one step.
CLOSER_KEYWORDS = {
    'NEXT', 'ENDWHILE', 'WEND', 'UNTIL', 'ENDPROC', 'ENDIF', 'ENDCASE',
    'ENDFN', 'ELSE', 'WHEN', 'OTHERWISE',
}

_LEADING_WS_RE = re.compile(r'^([ \t]*)(.*)$')
_LEADING_NUMBER_RE = re.compile(r'^(\d+)\s*(.*)$')
_FIRST_WORD_RE = re.compile(r'^([A-Za-z_][A-Za-z_$0-9]*)')
_DIALECT_HINT_RE = re.compile(r"^\s*(\d+\s+)?(REM\s+dialect\s*:|'\s*dialect\s*:)", re.IGNORECASE)
_TRAILING_COMMENT_RE = re.compile(r"\bREM\b.*$|'.*$", re.IGNORECASE)


def split_leading_ws(line: str) -> Tuple[str, str]:
    """``(indentation, rest-of-line)``."""
    match = _LEADING_WS_RE.match(line)
    return match.group(1), match.group(2)


def split_leading_number(rest: str) -> Tuple[Optional[int], str]:
    """*rest* has no leading whitespace. ``(line number or None, statement)``."""
    match = _LEADING_NUMBER_RE.match(rest)
    if match:
        return int(match.group(1)), match.group(2)
    return None, rest


def first_keyword(statement: str) -> str:
    match = _FIRST_WORD_RE.match(statement.strip())
    return match.group(1).upper() if match else ''


def is_block_if(statement: str) -> bool:
    """True for ``IF ... THEN`` with nothing but a comment after THEN."""
    stripped = _TRAILING_COMMENT_RE.sub('', statement).rstrip()
    if not re.search(r'\bIF\b', stripped, re.IGNORECASE):
        return False
    return bool(re.search(r'\bTHEN\b\s*$', stripped, re.IGNORECASE))


def detect_numbered(text: str) -> bool:
    """Whether *text* is a numbered-line program (vs. modern unnumbered source)."""
    for raw_line in text.split('\n'):
        if _DIALECT_HINT_RE.match(raw_line):
            continue
        _ws, rest = split_leading_ws(raw_line)
        if not rest.strip():
            continue
        number, _statement = split_leading_number(rest)
        if number is not None:
            return True
    return False


def used_line_numbers(text: str) -> Set[int]:
    numbers: Set[int] = set()
    for raw_line in text.split('\n'):
        _ws, rest = split_leading_ws(raw_line)
        number, _statement = split_leading_number(rest)
        if number is not None:
            numbers.add(number)
    return numbers


def next_line_number(used: Set[int], after: Optional[int]) -> int:
    """Next free line number following *after* (or from 10 if there is none)."""
    candidate = 10 if after is None else after + 10
    while candidate in used:
        candidate += 1
    return candidate


def indent_for_new_line(ws: str, statement: str) -> str:
    """Indentation for the line that follows one starting with *ws* + *statement*."""
    keyword = first_keyword(statement)
    opens_block = keyword in OPENER_KEYWORDS or (keyword == 'IF' and is_block_if(statement))
    if opens_block:
        return ws + ' ' * INDENT_STEP
    return ws


def dedent_for_keyword(ws: str, word: str) -> Optional[str]:
    """New indentation for a line whose first word just became *word*, or
    ``None`` if that word doesn't call for a dedent (or there's nothing to
    remove)."""
    if word.upper() not in CLOSER_KEYWORDS:
        return None
    if len(ws) < INDENT_STEP:
        return None
    return ws[:-INDENT_STEP]
