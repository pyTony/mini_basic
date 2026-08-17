"""Lexer/parser reserved words and builtin name tables.

Centralises names that must stay consistent across expression expansion,
dialect checking, and the compiled-expression fast path. When adding a numeric
builtin, update ``NUMERIC_BUILTIN_FUNCS`` and the expander in ``mini_basic.py``
(or future ``expr/builtins.py``).
"""

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

SAFE_EVAL_GLOBALS = {'__builtins__': {}, 'int': int}
"""Restricted globals dict for CompiledExpr eval()."""

EXPR_RESERVED_WORDS = frozenset({
    'MOD', 'DIV', 'AND', 'OR', 'NOT', 'XOR', 'EOR', 'EQV', 'IMP',
    'TRUE', 'FALSE', 'ERR', 'ERL', 'GET', 'INKEY',
})
"""Identifiers that must not be treated as variables during compile()."""

NUMERIC_BUILTIN_FUNCS = (
    'NEARSIG', 'NEAR', 'SGN', 'RND', 'LEN', 'INSTR', 'ARG', 'PI', 'POINT', 'TINT', 'VAL',
    'POS', 'VPOS', 'GET', 'INKEY', 'WIDTH',
    'SIN', 'COS', 'TAN', 'SINRAD', 'COSRAD', 'TANRAD',
    'ASN', 'ASIN', 'ACS', 'ACOS', 'ATN', 'ATAN',
    'DEG', 'RAD',
    'LOG', 'EXP', 'SQR', 'SQRT', 'ABS', 'INT', 'SNG', 'DBL', 'FLOAT', 'DIM', 'SUM',
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
