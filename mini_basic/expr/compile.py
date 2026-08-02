"""Compiled expression cache for numeric and condition evaluation.

When ``optimization_level >= 2``, pure arithmetic expressions are compiled with
Python's ``compile()`` and evaluated via ``eval()`` against a tight namespace of
float slots, integer proxy slots, and system variables. Expressions that contain
arrays, boolean syntax, or dynamic builtins fall back to the interpreter's slow
path.

``CompiledExpr`` holds the compiled bytecode plus metadata about which variable
slots must be populated before evaluation.
"""
from __future__ import annotations

from types import CodeType
from typing import TYPE_CHECKING, Dict, Optional, Tuple

from ..constants import SAFE_EVAL_GLOBALS

if TYPE_CHECKING:
    from mini_basic import BASICInterpreter


def int_slot(name: str) -> str:
    """Proxy identifier used when compiling integer variables into Python eval.

    Storage keys may include BBCSDL suffixes (``a%``, ``a%%``); map them to
    valid Python identifiers.
    """
    safe = (
        name.replace('%%', '_i64_')
        .replace('%', '_i_')
        .replace('$', '_s_')
        .replace('!', '_f_')
        .replace('#', '_d_')
        .replace('.', '_dot_')
    )
    return f'__ib_{safe}__'


class CompiledExpr:
    """One compiled BASIC expression, optionally cached per run."""

    __slots__ = (
        'source',
        'code',
        'float_vars',
        'int_vars',
        'system_vars',
        'needs_time',
        'is_condition',
        'use_fallback',
        '_ns_cache',
    )

    def __init__(
        self,
        source: str,
        code: Optional[CodeType] = None,
        float_vars: Optional[Tuple[str, ...]] = None,
        int_vars: Optional[Tuple[str, ...]] = None,
        system_vars: Optional[Tuple[str, ...]] = None,
        needs_time: bool = False,
        is_condition: bool = False,
        use_fallback: bool = False,
    ):
        self.source = source
        self.code = code
        self.float_vars = float_vars or ()
        self.int_vars = int_vars or ()
        self.system_vars = system_vars or ()
        self.needs_time = needs_time
        self.is_condition = is_condition
        self.use_fallback = use_fallback
        self._ns_cache: Optional[Dict[str, float]] = None

    def _namespace(self, interp: BASICInterpreter) -> Dict[str, float]:
        namespace = self._ns_cache
        if namespace is None:
            namespace = {}
            self._ns_cache = namespace
        else:
            namespace.clear()
        if self.needs_time:
            namespace['__basic_time__'] = interp._get_time()
        for name in self.float_vars:
            if name in interp.variables:
                namespace[name] = interp.variables[name]
        for name in self.int_vars:
            namespace[int_slot(name)] = interp.int_variables.get(name, 0)
        for name in self.system_vars:
            namespace[name] = interp._get_system_var(name)
        return namespace

    def eval_numeric(self, interp: BASICInterpreter) -> float:
        if (
            self.use_fallback
            or self.code is None
            or interp._expr_has_array_ref(self.source)
            or (
                not self.is_condition
                and interp._expr_has_boolean_syntax(self.source)
                and not interp._expr_is_pure_bitwise(self.source)
            )
        ):
            return interp._eval_numeric_slow(self.source)
        result = eval(self.code, SAFE_EVAL_GLOBALS, self._namespace(interp))
        # Preserve exact precision for integer results (e.g. a bigint literal left
        # behind by FN-call expansion, such as FNfact(100)). Forcing float() here
        # would silently truncate anything past ~53 bits of mantissa, and would
        # raise OverflowError outright for integers beyond float's ~1.8e308 range.
        if isinstance(result, int):
            return result
        return float(result)

    def eval_condition(self, interp: BASICInterpreter) -> bool:
        if (
            self.use_fallback
            or self.code is None
            or interp._expr_has_array_ref(self.source)
            # NOTE: do not force fallback on boolean syntax here:
            # simple comparisons are deliberately compiled via prepare_simple_comparison
        ):
            return interp._eval_numeric(self.source) != 0
        result = eval(self.code, SAFE_EVAL_GLOBALS, self._namespace(interp))
        return result != 0


__all__ = ['CompiledExpr', 'int_slot']
