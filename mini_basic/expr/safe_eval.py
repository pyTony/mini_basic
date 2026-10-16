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
import operator
import re
from functools import lru_cache
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


_BINOPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.BitAnd: operator.and_, ast.BitOr: operator.or_, ast.BitXor: operator.xor,
    ast.LShift: operator.lshift, ast.RShift: operator.rshift,
}

_UNOPS = {
    ast.UAdd: operator.pos, ast.USub: operator.neg,
    ast.Not: operator.not_, ast.Invert: operator.invert,
}

_CMPS = {
    ast.Eq: operator.eq, ast.NotEq: operator.ne,
    ast.Lt: operator.lt, ast.LtE: operator.le,
    ast.Gt: operator.gt, ast.GtE: operator.ge,
}


def evaluate_ast(node: ast.AST, globals_dict: dict, locals_dict: dict) -> object:
    if isinstance(node, ast.Expression):
        return evaluate_ast(node.body, globals_dict, locals_dict)
    elif isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Name):
        if node.id in locals_dict:
            return locals_dict[node.id]
        if node.id in globals_dict:
            return globals_dict[node.id]
        raise NameError(f"name '{node.id}' is not defined")
    elif isinstance(node, ast.BinOp):
        if type(node.op) not in _BINOPS:
            raise ValueError(f"syntax error: unsupported binop {type(node.op).__name__}")
        return _BINOPS[type(node.op)](
            evaluate_ast(node.left, globals_dict, locals_dict),
            evaluate_ast(node.right, globals_dict, locals_dict)
        )
    elif isinstance(node, ast.UnaryOp):
        if type(node.op) not in _UNOPS:
            raise ValueError(f"syntax error: unsupported unop {type(node.op).__name__}")
        return _UNOPS[type(node.op)](
            evaluate_ast(node.operand, globals_dict, locals_dict)
        )
    elif isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            for val in node.values:
                res = evaluate_ast(val, globals_dict, locals_dict)
                if not res: return res
            return res
        elif isinstance(node.op, ast.Or):
            for val in node.values:
                res = evaluate_ast(val, globals_dict, locals_dict)
                if res: return res
            return res
    elif isinstance(node, ast.Compare):
        left = evaluate_ast(node.left, globals_dict, locals_dict)
        for op, comp in zip(node.ops, node.comparators):
            if type(op) not in _CMPS:
                raise ValueError(f"syntax error: unsupported cmpop {type(op).__name__}")
            right = evaluate_ast(comp, globals_dict, locals_dict)
            if not _CMPS[type(op)](left, right):
                return False
            left = right
        return True
    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.keywords:
            raise ValueError('syntax error')
        func = evaluate_ast(node.func, globals_dict, locals_dict)
        args = [evaluate_ast(arg, globals_dict, locals_dict) for arg in node.args]
        return func(*args)
    elif isinstance(node, ast.Subscript):
        if not isinstance(node.value, ast.Name):
            raise ValueError('syntax error')
        val = evaluate_ast(node.value, globals_dict, locals_dict)
        if hasattr(ast, 'Index') and isinstance(node.slice, getattr(ast, 'Index')):
            idx = evaluate_ast(node.slice.value, globals_dict, locals_dict)
        else:
            idx = evaluate_ast(node.slice, globals_dict, locals_dict)
        return val[idx]
    elif isinstance(node, ast.IfExp):
        if evaluate_ast(node.test, globals_dict, locals_dict):
            return evaluate_ast(node.body, globals_dict, locals_dict)
        return evaluate_ast(node.orelse, globals_dict, locals_dict)
    elif type(node).__name__ == 'Num':
        return getattr(node, 'n')
    elif type(node).__name__ == 'Str':
        return getattr(node, 's')
    elif type(node).__name__ == 'NameConstant':
        return getattr(node, 'value')

    raise ValueError(f"syntax error: {type(node).__name__}")


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


_RE_STRING_OR_LEADING_ZEROS = re.compile(r'''"[^"]*"|'[^']*'|(?<![\w.])0+(?=\d)''')


def _strip_leading_zeros(source: str) -> str:
    """BASIC 010 is ten; Python rejects leading zeros in int literals."""
    if '0' not in source:
        return source
    return _RE_STRING_OR_LEADING_ZEROS.sub(
        lambda m: m.group(0) if m.group(0)[0] in '"\'' else '', source,
    )


# Text that could hold a forbidden node: attribute (.name), [ ] { } literals,
# lambda / comprehension / walrus / f-string / await / yield.
_RE_MAYBE_UNSAFE = re.compile(
    r'''\.\s*[A-Za-z_]|[\[\]{}]|\b(?:lambda|for|await|yield)\b|:=|\b[fF][rR]?["']'''
)


@lru_cache(maxsize=4096)
def compile_safe(source: str) -> ast.Expression:
    """Parse, validate and transform *source*; SyntaxError / ValueError on failure."""
    source = _strip_leading_zeros(source)
    tree = ast.parse(source, filename='<string>', mode='eval')
    check_expression_tree(tree)
    tree = ast.fix_missing_locations(_BasicSemantics(source).visit(tree))
    return tree


def safe_eval(source: str, namespace: Optional[dict] = None) -> object:
    return evaluate_ast(compile_safe(source), SAFE_EVAL_GLOBALS, {} if namespace is None else namespace)


__all__ = ['check_expression_tree', 'compile_safe', 'safe_eval', 'evaluate_ast']
