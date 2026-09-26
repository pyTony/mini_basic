"""Lexer/parser reserved words and builtin name tables.

Centralises names that must stay consistent across expression expansion,
dialect checking, and the compiled-expression fast path. When adding a numeric
builtin, update ``NUMERIC_BUILTIN_FUNCS`` and the expander in ``mini_basic.py``
(or future ``expr/builtins.py``).
"""

import math

CLI_EXIT_WORDS = frozenset({
    'bye',
    'goodbye',
    'quit',
    'exit',
    'q',
})
"""Optional mini_basic extension (--input-exit): magic words at INPUT, not MBASIC/BBC."""

EXIT_HOLD_CONSOLE = 10
"""Exit code for mini_basic.cmd pause-after-run behaviour."""

def _basic_mod(a, b):
    """BASIC MOD: truncating remainder, sign of the dividend (-7 MOD 3 = -1)."""
    if not b:
        raise ZeroDivisionError('division by zero')
    if isinstance(a, int) and isinstance(b, int):
        r = abs(a) % abs(b)
        return -r if a < 0 else r
    return math.fmod(a, b)


def _basic_idiv(a, b):
    """BASIC DIV and backslash: quotient truncated toward zero (-7 DIV 2 = -3)."""
    if not b:
        raise ZeroDivisionError('division by zero')
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


SAFE_EVAL_GLOBALS = {
    '__builtins__': {},
    'int': int,
    '__basic_mod__': _basic_mod,
    '__basic_idiv__': _basic_idiv,
    # Pure math builtins for the compiled fast path (same as the slow path).
    '__m_sin__': math.sin,
    '__m_cos__': math.cos,
    '__m_tan__': math.tan,
    '__m_atn__': math.atan,
    '__m_rad__': math.radians,
    '__m_deg__': math.degrees,
    '__m_sqr__': math.sqrt,
    '__m_exp__': math.exp,
    '__m_abs__': abs,
    # Placeholder: each CompiledExpr namespace binds the interpreter's reader.
    '__aget__': None,
    # Same: numeric builtin of a planned string (strplan.py ``__sfn__``).
    '__sfn__': None,
}
"""Restricted globals dict for CompiledExpr eval()."""

EXPR_RESERVED_WORDS = frozenset({
    'MOD', 'DIV', 'AND', 'OR', 'NOT', 'XOR', 'EOR', 'EQV', 'IMP',
    'TRUE', 'FALSE', 'ERR', 'ERL', 'GET', 'INKEY',
})
"""Identifiers that must not be treated as variables during compile()."""

NUMERIC_BUILTIN_FUNCS = (
    'NEARSIG', 'NEAR', 'SGN', 'RND', 'LEN', 'INSTR', 'ARG', 'PI', 'POINT', 'TINT', 'VAL',
    'POS', 'VPOS', 'GET', 'INKEY', 'TIMER', 'WIDTH',
    'SIN', 'COS', 'TAN', 'SINRAD', 'COSRAD', 'TANRAD',
    'ASN', 'ASIN', 'ACS', 'ACOS', 'ATN', 'ATAN',
    'DEG', 'RAD',
    'LOG', 'EXP', 'SQR', 'SQRT', 'ABS', 'INT', 'FIX', 'CINT', 'CSNG', 'CDBL',
    'SNG', 'DBL', 'FLOAT', 'DIM', 'SUM',
    'CVI', 'CVS', 'CVD', 'LOC', 'LOF', 'EOF',
)
# Longest names first so SINRAD matches before SIN in glued BBC forms (SINRADT).
NUMERIC_BUILTIN_FUNC_RE = '|'.join(
    sorted(NUMERIC_BUILTIN_FUNCS, key=len, reverse=True)
)

MITS_FORBIDDEN_CMDS = frozenset({
    'WHILE', 'WEND', 'ENDIF', 'ELSEIF', 'ELIF', 'CONTINUE', 'BREAK',
    'REPEAT', 'UNTIL', 'PROC', 'ENDPROC', 'EXIT',
    'CASE', 'WHEN', 'OTHERWISE', 'ENDCASE',
})
MINI_ONLY_CMDS = frozenset({'BREAK', 'CONTINUE', 'EXIT'})
MINI_ONLY_FUNCS = frozenset({
    'ARG', 'FG$', 'BG$', 'RGB$', 'BGRGB$', 'ANSI$', 'RESET$',
})
