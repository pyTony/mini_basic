"""Validated compile/eval for translated BASIC expressions.

Expressions are rewritten to Python and run with ``eval()``. Empty builtins are
not a sandbox on their own: ``(1).__class__.__bases__`` walks from any literal
to every loaded class. BASIC never needs attribute access, comprehensions or
lambdas, so the AST is checked before compile and those forms are refused.
(The translator itself emits ``__ib_X__`` slot names and ``-1 if c else 0``,
so dunder names and conditional expressions stay allowed; without attribute
access they only read the eval namespace.)
"""
from __future__ import annotations

import ast
from functools import lru_cache
from types import CodeType
from typing import Optional

from ..constants import SAFE_EVAL_GLOBALS

_FORBIDDEN_NODES = (
    ast.Attribute, ast.Lambda, ast.NamedExpr, ast.Starred,
    ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
    ast.List, ast.Dict, ast.Set, ast.Slice,
    ast.Await, ast.Yield, ast.YieldFrom, ast.JoinedStr, ast.FormattedValue,
)


def check_expression_tree(tree: ast.AST) -> None:
    """Raise ValueError if *tree* uses Python beyond BASIC arithmetic/calls."""
    for node in ast.walk(tree):
        if isinstance(node, _FORBIDDEN_NODES):
            raise ValueError('syntax error')
        if isinstance(node, ast.Call) and (
            not isinstance(node.func, ast.Name) or node.keywords
        ):
            raise ValueError('syntax error')
        if isinstance(node, ast.Subscript) and not isinstance(node.value, ast.Name):
            raise ValueError('syntax error')


@lru_cache(maxsize=4096)
def compile_safe(source: str) -> CodeType:
    """Parse, validate and compile *source*; SyntaxError / ValueError on failure."""
    tree = ast.parse(source, filename='<string>', mode='eval')
    check_expression_tree(tree)
    return compile(tree, '<string>', 'eval')


def safe_eval(source: str, namespace: Optional[dict] = None) -> object:
    return eval(compile_safe(source), SAFE_EVAL_GLOBALS, {} if namespace is None else namespace)


__all__ = ['check_expression_tree', 'compile_safe', 'safe_eval']
