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


class _BasicSemantics(ast.NodeTransformer):
    """Give Python's %, // and ** the BASIC meaning.

    * ``%`` (MOD) and ``//`` (DIV, backslash) truncate toward zero, so
      -7 MOD 3 is -1 and -7 DIV 2 is -3 (Python floors: 2 and -4).
    * ``^`` is left-associative in BASIC: 2^3^2 is 64, Python's ** gives 512.
      Only chains the source did not parenthesize are regrouped.
    """

    def __init__(self, source: str) -> None:
        self._src = source.encode('utf-8')

    def _parenthesized(self, node: ast.AST) -> bool:
        index = getattr(node, 'col_offset', 0) - 1
        while index >= 0 and self._src[index:index + 1].isspace():
            index -= 1
        return index >= 0 and self._src[index:index + 1] == b'('

    def _left_assoc_pow(self, node: ast.BinOp) -> ast.BinOp:
        right = node.right
        if (
            isinstance(right, ast.BinOp)
            and isinstance(right.op, ast.Pow)
            and not self._parenthesized(right)
        ):
            left = ast.copy_location(ast.BinOp(node.left, ast.Pow(), right.left), node)
            left = self._left_assoc_pow(left)
            node = ast.copy_location(ast.BinOp(left, ast.Pow(), right.right), node)
        return node

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        self.generic_visit(node)
        if isinstance(node.op, ast.Pow):
            return self._left_assoc_pow(node)
        helper = None
        if isinstance(node.op, ast.Mod):
            helper = '__basic_mod__'
        elif isinstance(node.op, ast.FloorDiv):
            helper = '__basic_idiv__'
        if helper is None:
            return node
        call = ast.Call(ast.Name(helper, ast.Load()), [node.left, node.right], [])
        return ast.copy_location(call, node)


@lru_cache(maxsize=4096)
def compile_safe(source: str) -> CodeType:
    """Parse, validate and compile *source*; SyntaxError / ValueError on failure."""
    tree = ast.parse(source, filename='<string>', mode='eval')
    check_expression_tree(tree)
    tree = ast.fix_missing_locations(_BasicSemantics(source).visit(tree))
    return compile(tree, '<string>', 'eval')


def safe_eval(source: str, namespace: Optional[dict] = None) -> object:
    return eval(compile_safe(source), SAFE_EVAL_GLOBALS, {} if namespace is None else namespace)


__all__ = ['check_expression_tree', 'compile_safe', 'safe_eval']
