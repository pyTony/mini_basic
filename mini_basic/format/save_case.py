"""Fold keywords and identifiers when saving case-insensitive dialect programs."""
from __future__ import annotations

import re
from typing import Callable, List, Literal, Optional, Tuple

from ..constants import EXPR_RESERVED_WORDS, NUMERIC_BUILTIN_FUNCS

Fold = Literal['upper', 'lower']

# Keep in sync with expr/patterns.py (leading _ for BBCSDL names).
VAR_BASE_PATTERN = r'[_A-Za-z][A-Za-z0-9_]*'
RE_VAR_BASE_FULL = re.compile(rf'^{VAR_BASE_PATTERN}$')

_STMT_KEYWORDS = (
    'PRINT#', 'INPUT#', 'WRITE#', 'CLOSE#',
    'PRINT', 'INPUT', 'WRITE',
    'FOR', 'NEXT', 'WHILE', 'WEND', 'REPEAT', 'UNTIL',
    'BREAK', 'CONTINUE', 'EXIT', 'PROC', 'ENDPROC',
    'LET', 'IF', 'ELSE', 'ELSEIF', 'ELIF', 'ENDIF',
    'GOTO', 'GOSUB', 'RESUME', 'RETURN',
    'DATA', 'DEF', 'DIM', 'READ', 'RESTORE', 'END', 'REM',
    'MODE', 'VDU', 'COLOUR', 'COLOR', 'CLS', 'CLG', 'GCOL', 'MOVE', 'DRAW',
    'ORIGIN', 'PLOT', 'SPRITEDEF', 'SPRITE', 'STOP', 'OSCLI', 'WAIT',
    'TO', 'STEP', 'THEN', 'MOD', 'AND', 'OR', 'NOT', 'TRUE', 'FALSE',
    'ON', 'ERROR', 'OFF', 'OPEN', 'FIELD', 'GET', 'PUT', 'LSET', 'RSET',
    'OPTION', 'BASE', 'RANDOMIZE', 'DEFINT', 'DEFSNG', 'DEFDBL', 'DEFSTR',
    'INT', 'SNG', 'DBL', 'STR',
)

_STRING_BUILTINS = (
    'CHR$', 'STR$', 'STRING$', 'SPACE$', 'INKEY$', 'MKI$', 'MKS$', 'MKD$',
    'ASC', 'LEFT$', 'RIGHT$', 'MID$', 'UCASE$', 'LCASE$', 'ANSI$', 'FG$', 'BG$',
    'RGB$', 'BGRGB$', 'RESET$', 'ARG$', 'OPENIN', 'OPENOUT',
)

_RESERVED_WORDS = frozenset(
    word.upper()
    for word in (
        *_STMT_KEYWORDS,
        *EXPR_RESERVED_WORDS,
        *NUMERIC_BUILTIN_FUNCS,
        *_STRING_BUILTINS,
    )
)

_RE_LABEL_PREFIX = re.compile(
    rf'^({VAR_BASE_PATTERN}):\s*(.*)$',
    re.IGNORECASE,
)
_RE_REM = re.compile(r'^REM\b(.*)$', re.IGNORECASE)
_RE_STMT_CMD = re.compile(
    r'^(' + '|'.join(sorted(_STMT_KEYWORDS, key=len, reverse=True)) + r')(?![A-Za-z0-9_])',
    re.IGNORECASE,
)
_RE_STMT_CMD_BBC = re.compile(
    r'^(' + '|'.join(sorted(_STMT_KEYWORDS, key=len, reverse=True)) + r')(?![A-Za-z0-9_])',
)
_RE_FN = re.compile(
    rf'\bFN({VAR_BASE_PATTERN})(%|\$)?\b',
    re.IGNORECASE,
)
_RE_PROC = re.compile(
    rf'\bPROC({VAR_BASE_PATTERN})\b',
    re.IGNORECASE,
)
_RE_IDENTIFIER = re.compile(
    rf'\b({VAR_BASE_PATTERN})([%$!#])?\b',
)


def _fold_text(text: str, fold: Fold) -> str:
    return text.upper() if fold == 'upper' else text.lower()


def _split_string_literal_regions(text: str) -> List[Tuple[bool, str]]:
    regions: List[Tuple[bool, str]] = []
    index = 0
    while index < len(text):
        if text[index] == '"':
            end = index + 1
            while end < len(text):
                if text[end] == '"':
                    end += 1
                    break
                end += 1
            regions.append((True, text[index:end]))
            index = end
            continue
        end = index
        while end < len(text) and text[end] != '"':
            end += 1
        if end > index:
            regions.append((False, text[index:end]))
        index = end
    return regions


def _split_colon_statements(line: str) -> List[str]:
    parts: List[str] = []
    current: List[str] = []
    in_string = False
    after_then = False
    index = 0
    while index < len(line):
        ch = line[index]
        if ch == '"':
            in_string = not in_string
            current.append(ch)
            index += 1
            continue
        if (
            not in_string
            and not after_then
            and line[index:index + 4].upper() == 'THEN'
            and (index == 0 or not line[index - 1].isalnum())
            and (index + 4 >= len(line) or not line[index + 4].isalnum())
        ):
            after_then = True
            current.append(line[index:index + 4])
            index += 4
            continue
        if ch == ':' and not in_string:
            part = ''.join(current).strip()
            if after_then:
                current.append(ch)
                index += 1
                continue
            if part and RE_VAR_BASE_FULL.fullmatch(part):
                current.append(ch)
                index += 1
                continue
            if part:
                parts.append(part)
            current = []
            after_then = False
            index += 1
            continue
        current.append(ch)
        index += 1
    part = ''.join(current).strip()
    if part:
        parts.append(part)
    return parts


def _space_expr_segment(segment: str, fold: Fold) -> str:
    # Ensure type suffixes like % $ are glued, no space before them (e.g. result% not result %)
    segment = re.sub(r'(\w)\s+([%$!#]+)', r'\1\2', segment)
    segment = re.sub(r'([%$!#]+)\s+(\w)', r'\1\2', segment)

    segment = re.sub(r'\bMOD\b', _fold_text('MOD', fold), segment, flags=re.IGNORECASE)
    segment = re.sub(r'\bTO\b', _fold_text('TO', fold), segment, flags=re.IGNORECASE)
    segment = re.sub(r'\bSTEP\b', _fold_text('STEP', fold), segment, flags=re.IGNORECASE)
    segment = re.sub(r'\bGOTO\b', _fold_text('GOTO', fold), segment, flags=re.IGNORECASE)
    segment = re.sub(r'\bTHEN\b', _fold_text('THEN', fold), segment, flags=re.IGNORECASE)
    # Space glued MOD/DIV for readability (consistent with execution)
    segment = re.sub(r'(?<=[0-9)])(MOD|DIV)(?=[0-9A-Za-z_(])', r' \1 ', segment, flags=re.IGNORECASE)
    for op in ('>=', '<=', '<>'):
        segment = re.sub(rf'\s*{re.escape(op)}\s*', f' {op} ', segment)
    segment = re.sub(
        rf'({VAR_BASE_PATTERN}[%$!#]?)\s*=\s*',
        r'\1 = ',
        segment,
        flags=re.IGNORECASE,
    )
    segment = re.sub(r'=\s*(["\'])', r'= \1', segment)
    segment = re.sub(r'([\w$)\]])([*/\\])', r'\1 \2', segment)
    segment = re.sub(r'([*/\\])([\w"(])', r'\1 \2', segment)
    segment = re.sub(r'(?<=[A-Za-z0-9_])\s+%\s+(?=[A-Za-z0-9_"(])', ' % ', segment)
    segment = re.sub(r'([\w%$)\]])([+\-])(?=[\w"(])', r'\1 \2 ', segment)
    segment = re.sub(r'(?<![=<>!+\-*/])\s*=\s*(?!=)', ' = ', segment)
    segment = re.sub(r'\s+', ' ', segment)
    return segment.strip()


def _fold_code_segment(segment: str, fold: Fold) -> str:
    def fold_fn(match: re.Match) -> str:
        name = match.group(1)
        suffix = match.group(2) or ''
        return _fold_text('FN', fold) + _fold_text(name, fold) + suffix

    def fold_proc(match: re.Match) -> str:
        return _fold_text('PROC', fold) + _fold_text(match.group(1), fold)

    def fold_word(match: re.Match) -> str:
        word = match.group(1)
        suffix = match.group(2) or ''
        upper = word.upper()
        if suffix == '$' and upper in _RESERVED_WORDS:
            return _fold_text(word, fold) + suffix
        if upper in _RESERVED_WORDS:
            return _fold_text(word, fold) + suffix
        if upper.startswith('FN') and len(upper) > 2:
            return match.group(0)
        return _fold_text(word, fold) + suffix

    segment = _RE_FN.sub(fold_fn, segment)
    segment = _RE_PROC.sub(fold_proc, segment)

    keywords = sorted(_RESERVED_WORDS, key=len, reverse=True)
    for keyword in keywords:
        segment = re.sub(
            rf'(?<![A-Za-z0-9_]){re.escape(keyword)}(?![A-Za-z0-9_])',
            _fold_text(keyword, fold),
            segment,
            flags=re.IGNORECASE,
        )

    return _RE_IDENTIFIER.sub(fold_word, segment)


def _format_expression(expr: str, fold: Fold) -> str:
    parts: List[str] = []
    for is_string, chunk in _split_string_literal_regions(expr):
        if is_string:
            parts.append(chunk)
        else:
            spaced = _space_expr_segment(chunk, fold)
            parts.append(_fold_code_segment(spaced, fold))
    return ''.join(parts)


def _format_statement_body(body: str, fold: Fold) -> str:
    stripped = body.strip()
    if not stripped:
        return stripped
    if stripped.startswith("'"):
        return body
    if _RE_REM.match(stripped):
        return body
    if stripped.startswith('*'):
        return body
    
    match = _RE_STMT_CMD.match(stripped)
    if match:
        cmd = _fold_text(match.group(1), fold)
        rest = stripped[match.end():].lstrip()
        if rest and rest[0] in '"\'(':
            rest = ' ' + rest
        elif rest and not rest[0].isspace():
            rest = ' ' + rest
        rest = _format_expression(rest.strip(), fold)
        return f'{cmd} {rest}'.rstrip() if rest else cmd

    return _format_expression(stripped, fold)


def format_statement_part(part: str, fold: Fold) -> str:
    stripped = part.strip()
    if not stripped:
        return stripped
    # Preserve apostrophe / REM text (do not space FG$/RESET$ as operators).
    if stripped.startswith("'") or re.match(r'^REM\b', stripped, re.IGNORECASE):
        return stripped
    label_match = _RE_LABEL_PREFIX.match(stripped)
    if label_match and label_match.group(1).upper() not in _RESERVED_WORDS:
        label = _fold_text(label_match.group(1), fold)
        body = label_match.group(2)
        formatted = _format_statement_body(body, fold)
        if formatted:
            return f'{label}: {formatted}'
        return f'{label}:'
    return _format_statement_body(stripped, fold)


def glue_bbc_proc_fn_names(text: str) -> str:
    """Re-glue PROC/FN to their names for Beeb / RISC OS source export.

    Internal normalize inserts ``PROC SWOOSH`` for parsing; Archimedes BASIC
    reports "Bad call of function/procedure" if a space remains between PROC
    and the name (RISC OS manual: no spaces between PROC and the name).
    """
    text = re.sub(r'\bEND\s+PROC\b', 'ENDPROC', text, flags=re.IGNORECASE)
    text = re.sub(r'\bEND\s+FN\b', 'ENDFN', text, flags=re.IGNORECASE)
    # DEF PROC NAME → DEFPROCNAME (space after DEF is optional; PROC+name must glue)
    text = re.sub(
        r'\bDEF\s+PROC\s+([A-Za-z_@])',
        r'DEFPROC\1',
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r'\bDEF\s+FN\s+([A-Za-z_@])',
        r'DEFFN\1',
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r'\bPROC\s+([A-Za-z_@])',
        r'PROC\1',
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r'\bFN\s+([A-Za-z_@%])',
        r'FN\1',
        text,
        flags=re.IGNORECASE,
    )
    return text


def format_program_line(statement: str, fold: Fold) -> str:
    parts = _split_colon_statements(statement)
    formatted = ': '.join(format_statement_part(part, fold) for part in parts)
    formatted = re.sub(r'=\s*(["\'])', r'= \1', formatted)
    return glue_bbc_proc_fn_names(formatted)


def fold_from_save_case(save_case: int) -> Fold:
    return 'lower' if int(save_case) == 1 else 'upper'


__all__ = [
    'Fold',
    'fold_from_save_case',
    'format_program_line',
    'format_statement_part',
    'glue_bbc_proc_fn_names',
]
