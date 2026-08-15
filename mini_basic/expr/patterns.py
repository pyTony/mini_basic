"""Regular-expression patterns for parsing and expanding BASIC expressions.

These patterns are shared by the expression compiler, builtin expanders, and
the interpreter's slow-path evaluator. Command-statement patterns (PRINT, GOTO,
etc.) remain in ``mini_basic.BASICInterpreter`` until the ``parse/`` package
lands in a later refactor phase.

Patterns are built once at import time. ``NUMERIC_BUILTIN_FUNC_RE`` must stay in
sync with ``mini_basic.constants.NUMERIC_BUILTIN_FUNCS``.
"""
from __future__ import annotations

import re

from ..constants import NUMERIC_BUILTIN_FUNC_RE

# Variable names: letter followed by letters, digits, or underscore.
# BBCSDL / BB4W allow leading underscore (flier: DIM _BOX(4,2)).
VAR_BASE_PATTERN = r'[_A-Za-z][A-Za-z0-9_]*'
# BBCSDL allows numeric PROC/FN names (world.bbc PROC4). One capture group = name.
PROC_FN_NAME_PATTERN = rf'({VAR_BASE_PATTERN}|[0-9]+)'
RE_VAR_BASE_FULL = re.compile(r'^[_A-Za-z][A-Za-z0-9_]*$')
# Statement forms: PROC4(x) / PROC 4(x) / DEF PROC4 …
RE_PROC_CALL = re.compile(
    rf'^PROC_?\s*{PROC_FN_NAME_PATTERN}\s*(?:\((.*)\))?$',
    re.IGNORECASE,
)
RE_DEF_PROC = re.compile(
    rf'^PROC_?\s*{PROC_FN_NAME_PATTERN}\s*(?:\((.*)\))?\s*(.*)$',
    re.IGNORECASE,
)
# After command 'PROC' is stripped: rest is ``4(args)`` or ``name(args)``.
RE_PROC_CALL_REST = re.compile(
    rf'^{PROC_FN_NAME_PATTERN}\s*(?:\((.*)\))?$',
    re.IGNORECASE,
)

# Arithmetic and condition normalisation.
RE_MOD = re.compile(r'\bMOD\b', re.IGNORECASE)
RE_INT_DIV = re.compile(r'(?<=[\d.)])\s*\\\s*(?=[\d.(])')
RE_TIME = re.compile(r'\bTIME\b', re.IGNORECASE)
RE_HAS_LETTER = re.compile(r'[A-Za-z]')
RE_COND_NE = re.compile(r'<>')
RE_COND_EQ = re.compile(r'(?<![=<>!])\s*=\s*(?!=)')
RE_BITWISE_AND = re.compile(r'\bAND\b', re.IGNORECASE)
RE_BITWISE_OR = re.compile(r'\bOR\b', re.IGNORECASE)
RE_BITWISE_EOR = re.compile(r'\bEOR\b', re.IGNORECASE)

# Array element references in expressions, e.g. A(1) or N$(I%).
RE_ARRAY_HEAD = re.compile(
    rf'\b({VAR_BASE_PATTERN})(%%|%|\$|!|#|&)?\s*\(',
)

# String builtin calls with parentheses.
RE_FUNC_CALL = re.compile(
    r'(CHR\$|STR\$|STR\$~|HEX\$|BIN\$|STRING\$|SPACE\$|INKEY\$|GET\$|MKI\$|MKS\$|MKD\$|ASC|LEFT\$|RIGHT\$|'
    r'MID\$|UCASE\$|LCASE\$|ANSI\$|FG\$|BG\$|RGB\$|BGRGB\$|RESET\$|ARG\$)\s*\(',
    re.IGNORECASE,
)

# Bare INKEY$ without parentheses (MBASIC style).
# Do NOT match INKEY$(n) — that form has a timeout arg and is handled by RE_FUNC_CALL.
RE_INKEY_CALL = re.compile(r'(?<![A-Za-z0-9_])INKEY\$(?!\s*\()', re.IGNORECASE)

# Numeric builtins; optional ``(`` or bare call (RND, PI).
RE_NUMERIC_FUNC_CALL = re.compile(
    rf'(?<![A-Za-z0-9_])({NUMERIC_BUILTIN_FUNC_RE})(?![A-Za-z_$])',
    re.IGNORECASE,
)

# User-defined functions FNname( ... ).
RE_FN_CALL = re.compile(
    rf'(?<![A-Za-z0-9_])FN_?{PROC_FN_NAME_PATTERN}(%|\$)?\s*\(',
    re.IGNORECASE,
)

# Detect unexpanded calls remaining after expansion passes.
RE_DYNAMIC_CALL_REMAINS = re.compile(
    rf'(?<![A-Za-z0-9_])(?:CHR\$|STR\$|ASC|LEFT\$|RIGHT\$|MID\$|UCASE\$|LCASE\$|'
    rf'ANSI\$|FG\$|BG\$|RGB\$|BGRGB\$|RESET\$|ARG\$|{NUMERIC_BUILTIN_FUNC_RE}|'
    rf'FN_?{PROC_FN_NAME_PATTERN}[%$]?)',
    re.IGNORECASE,
)

# File channel functions inside expressions.
RE_FILE_FUNC = re.compile(r'\b(OPENIN|OPENOUT)\s*\(', re.IGNORECASE)
RE_FILE_FUNC_BBC = re.compile(
    rf'\b(OPENIN|OPENOUT)\s+("(?:[^"\\]|\\.)*"|{VAR_BASE_PATTERN}\$)',
    re.IGNORECASE,
)

__all__ = [
    'NUMERIC_BUILTIN_FUNC_RE',
    'PROC_FN_NAME_PATTERN',
    'RE_ARRAY_HEAD',
    'RE_COND_EQ',
    'RE_COND_NE',
    'RE_DEF_PROC',
    'RE_DYNAMIC_CALL_REMAINS',
    'RE_FILE_FUNC',
    'RE_FILE_FUNC_BBC',
    'RE_FN_CALL',
    'RE_FUNC_CALL',
    'RE_HAS_LETTER',
    'RE_INKEY_CALL',
    'RE_INT_DIV',
    'RE_MOD',
    'RE_NUMERIC_FUNC_CALL',
    'RE_PROC_CALL',
    'RE_PROC_CALL_REST',
    'RE_TIME',
    'RE_VAR_BASE_FULL',
    'VAR_BASE_PATTERN',
]
