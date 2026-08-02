"""Expression parsing, compilation, and builtin expansion (Phase 2).

Full evaluation still lives on ``BASICInterpreter`` in ``mini_basic.py``;
this package holds shared infrastructure extracted from the monolith:

- ``patterns`` — regex tables for expressions and builtins
- ``compile`` — ``CompiledExpr`` and the integer slot helper

Future modules (not yet extracted):

- ``builtins`` — RND, VAL, CVI, INKEY$, string functions
- ``eval`` — boolean logic, slow-path numeric eval
"""
from . import patterns
from .compile import CompiledExpr, int_slot

__all__ = ['CompiledExpr', 'int_slot', 'patterns']
