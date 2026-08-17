"""Single LIST/SAVE line formatter (keyword fold + operator spacing + PROC glue).

All program-list / save paths should use ``format_program_line`` so glue and
spacing cannot drift between runtime LIST and dialect save-case folding.
See ``docs/BBC_TOKENIZE_VS_UNGLUE.md``.
"""
from __future__ import annotations

import re
from typing import List, Literal, Optional, Tuple

from ..constants import EXPR_RESERVED_WORDS, NUMERIC_BUILTIN_FUNCS
from ..util.debug import dprint  # noqa: F401 — available in this module

# 'none' = mini-style LIST: uppercase statement keywords, preserve identifier case.
Fold = Literal['upper', 'lower', 'none']

# Keep in sync with expr/patterns.py (leading _ for BBCSDL names).
from ..expr.patterns import PROC_FN_NAME_PATTERN, VAR_BASE_PATTERN

RE_VAR_BASE_FULL = re.compile(rf'^{VAR_BASE_PATTERN}$')

_STMT_KEYWORDS = (
    'PRINT#', 'INPUT#', 'WRITE#', 'CLOSE#', 'BPUT#', 'BGET#',
    'PRINT', 'INPUT', 'WRITE',
    'FOR', 'NEXT', 'WHILE', 'WEND', 'ENDWHILE', 'REPEAT', 'UNTIL',
    'BREAK', 'CONTINUE', 'EXIT', 'PROC', 'ENDPROC',
    'LET', 'IF', 'ELSE', 'ELSEIF', 'ELIF', 'ENDIF',
    'GOTO', 'GOSUB', 'RESUME', 'RETURN',
    'DATA', 'DEF', 'DIM', 'READ', 'RESTORE', 'END', 'REM',
    'MODE', 'VDU', 'COLOUR', 'COLOR', 'CLS', 'CLG', 'GCOL', 'MOVE', 'DRAW', 'LINE',
    'ORIGIN', 'PLOT', 'SPRITEDEF', 'SPRITE', 'STOP', 'OSCLI', 'WAIT',
    'TO', 'STEP', 'THEN', 'MOD', 'AND', 'OR', 'NOT', 'TRUE', 'FALSE',
        'ON', 'ERROR', 'OFF', 'OPEN', 'FIELD', 'GET', 'PUT', 'LSET', 'RSET',
    'KILL', 'ERASE', 'TRACE', 'LVAR',
    'OPTION', 'BASE', 'RANDOMIZE', 'DEFINT', 'DEFSNG', 'DEFDBL', 'DEFSTR',
    'INT', 'SNG', 'DBL', 'STR',
)

_STRING_BUILTINS = (
    'CHR$', 'STR$', 'HEX$', 'OCT$', 'BIN$', 'STRING$', 'SPACE$', 'INKEY$', 'MKI$', 'MKS$', 'MKD$',
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
_RE_FN = re.compile(
    rf'\bFN_?{PROC_FN_NAME_PATTERN}(%|\$)?\b',
    re.IGNORECASE,
)
_RE_PROC = re.compile(
    rf'\bPROC_?{PROC_FN_NAME_PATTERN}\b',
    re.IGNORECASE,
)
_RE_IDENTIFIER = re.compile(
    rf'\b({VAR_BASE_PATTERN})([%$!#])?\b',
)


def _fold_text(text: str, fold: Fold) -> str:
    if fold == 'none':
        return text
    return text.upper() if fold == 'upper' else text.lower()


def _fold_keyword_token(text: str, fold: Fold) -> str:
    """Fold a statement/keyword token; mini LIST uppercases keywords."""
    if fold == 'none':
        return text.upper()
    return _fold_text(text, fold)


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


def space_expr_segment(segment: str, fold: Fold = 'none') -> str:
    """Format expression spacing; shared by LIST mini and dialect save-case paths."""
    # Type suffixes glued (result% not result %)
    segment = re.sub(r'(\w)\s+([%$!#]+)', r'\1\2', segment)
    # Only glue % to a following binary digit (not modulo / next identifier)
    segment = re.sub(r'%\s+([01])', r'%\1', segment)

    segment = re.sub(r'\bMOD\b', _fold_keyword_token('MOD', fold), segment, flags=re.IGNORECASE)
    segment = re.sub(r'\bTO\b', _fold_keyword_token('TO', fold), segment, flags=re.IGNORECASE)
    segment = re.sub(r'\bSTEP\b', _fold_keyword_token('STEP', fold), segment, flags=re.IGNORECASE)
    segment = re.sub(r'\bGOTO\b', _fold_keyword_token('GOTO', fold), segment, flags=re.IGNORECASE)
    segment = re.sub(r'\bTHEN\b', _fold_keyword_token('THEN', fold), segment, flags=re.IGNORECASE)
    segment = re.sub(
        r'(?<=[0-9)])(MOD|DIV)(?=[0-9A-Za-z_(])',
        r' \1 ',
        segment,
        flags=re.IGNORECASE,
    )
    for op in ('>=', '<=', '<>'):
        segment = re.sub(rf'\s*{re.escape(op)}\s*', f' {op} ', segment)
    segment = re.sub(
        rf'({VAR_BASE_PATTERN})([%$!#]?)\s*=\s*',
        r'\1\2 = ',
        segment,
        flags=re.IGNORECASE,
    )
    segment = re.sub(r'=\s*(["\'])', r'= \1', segment)
    # Keep compound assign glued. Pre-fix SAVE emitted ``I% + = 1``.
    segment = re.sub(r'([+\-*/])\s+=', r'\1=', segment)
    # * / only — % $ ! # are type suffixes (PX%*2), not spaced as operators.
    segment = re.sub(r'([\w)])([*/])', r'\1 \2', segment)
    segment = re.sub(r'(?<![%$!#])([*/])([\w(])', r'\1 \2', segment)
    segment = re.sub(r'([\w)])([+\-])(?=[\w(])', r'\1 \2 ', segment)
    segment = re.sub(r'(?<![=<>!+\-*/])\s*=\s*(?!=)', ' = ', segment)
    segment = re.sub(r'\s+', ' ', segment)
    return segment.strip()


# Back-compat name used internally / tests
_space_expr_segment = space_expr_segment


def _fold_code_segment(segment: str, fold: Fold) -> str:
    if fold == 'none':
        # Keywords already normalized in space_expr_segment where needed;
        # leave identifier case alone.
        return segment

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
            if parts:
                prev = parts[-1]
                # Chunks are stripped, so ``<> "N"`` lost the space before the quote.
                if prev and not prev[-1].isspace() and (
                    prev.endswith(('<>', '<=', '>=')) or prev[-1] in '=<>'
                ):
                    parts.append(' ')
            parts.append(chunk)
            continue
        spaced = space_expr_segment(chunk, fold)
        folded = _fold_code_segment(spaced, fold)
        # Same strip ate the gap after the quote: ``"N" 15`` became ``"N"15``.
        if parts and parts[-1].endswith('"') and folded[:1].isdigit():
            parts.append(' ')
        parts.append(folded)
    return ''.join(parts).strip()


def _format_statement_body(body: str, fold: Fold) -> str:
    stripped = body.strip()
    if not stripped:
        return stripped
    # Apostrophe comments: never reformat.
    if stripped.startswith("'"):
        return stripped
    # REM: dialect fold preserves full original text; mini LIST uppercases REM only.
    rem_m = _RE_REM.match(stripped)
    if rem_m is not None:
        if fold == 'none':
            rest = rem_m.group(1)
            if rest and not rest[0].isspace():
                return 'REM ' + rest.lstrip()
            return 'REM' + rest
        return stripped
    if stripped.startswith('*'):
        # Old SAVE treated * as multiply (``* REFRESH``). Glue REFRESH only.
        return re.sub(r'^\*\s+REFRESH\b', '*REFRESH', stripped, flags=re.IGNORECASE)

    match = _RE_STMT_CMD.match(stripped)
    if match:
        cmd = _fold_keyword_token(match.group(1), fold)
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
    if stripped.startswith("'") or re.match(r'^REM\b', stripped, re.IGNORECASE):
        return _format_statement_body(stripped, fold)
    label_match = _RE_LABEL_PREFIX.match(stripped)
    if label_match and label_match.group(1).upper() not in _RESERVED_WORDS:
        raw_label = label_match.group(1)
        label = raw_label.upper() if fold == 'none' else _fold_text(raw_label, fold)
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
    text = re.sub(
        r'\bDEF\s+PROC\s+([A-Za-z_@0-9])',
        r'DEFPROC\1',
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r'\bDEF\s+FN\s+([A-Za-z_@0-9])',
        r'DEFFN\1',
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r'\bPROC\s+([A-Za-z_@0-9])',
        r'PROC\1',
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r'\bFN\s+([A-Za-z_@0-9%])',
        r'FN\1',
        text,
        flags=re.IGNORECASE,
    )
    return text


def format_program_line(statement: str, fold: Fold) -> str:
    """Canonical LIST/SAVE formatting for one program statement line."""
    parts = _split_colon_statements(statement)
    formatted = ': '.join(format_statement_part(part, fold) for part in parts)
    formatted = re.sub(r'=\s*(["\'])', r'= \1', formatted)
    return glue_bbc_proc_fn_names(formatted)


def fold_from_save_case(save_case: int) -> Fold:
    return 'lower' if int(save_case) == 1 else 'upper'


def resolve_list_fold(detokenize_fold: Optional[Fold]) -> Fold:
    """Map interpreter detokenize fold (or None for mini) to a Fold mode."""
    if detokenize_fold is None:
        return 'none'
    return detokenize_fold


__all__ = [
    'Fold',
    'fold_from_save_case',
    'format_program_line',
    'format_statement_part',
    'glue_bbc_proc_fn_names',
    'resolve_list_fold',
    'space_expr_segment',
]
