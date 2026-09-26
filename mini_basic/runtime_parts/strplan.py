"""String expressions parsed once: static type and cached evaluation plans.

The older string evaluator works on text: every evaluation expands builtin
calls into literals (``STR$(I)`` → ``"3"``), splits the result at ``+`` and
resolves each piece. This module parses an expression once into a closure and
reuses it; anything it does not fully understand returns ``None`` and keeps
the text path, so behaviour only changes where the plan is certain.

- ``_expr_static_kind``: ``'str'`` / ``'num'`` from the first operand
  (``LEN(A$)+1`` is a number although it contains ``$``), or ``None``.
- ``_get_string_plan``: ``+`` concatenation of literals, ``A$``, ``A$(i)``,
  ``CHR$ STR$ LEFT$ RIGHT$ MID$ STRING$ SPACE$ UCASE$ LCASE$`` and ``( … )``.
- ``_rewrite_string_calls_for_compile``: ``LEN/ASC/VAL/INSTR(<string>)`` →
  ``__sfn__(id)`` so numeric expressions using them stay compiled.

Caches are keyed by expression text and dropped with the compiled-expression
cache (``_clear_string_plan_caches``).
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from ..expr.patterns import ident_prefix_len

StrThunk = Callable[[], str]

_MISSING = object()

# Names that are builtins when followed by ``$`` — never plain string variables.
_RESERVED_STR_NAMES = frozenset({
    'CHR', 'STR', 'HEX', 'OCT', 'BIN', 'STRING', 'SPACE', 'INKEY', 'GET',
    'MKI', 'MKS', 'MKD', 'LEFT', 'RIGHT', 'MID', 'UCASE', 'LCASE', 'ANSI',
    'FG', 'BG', 'RGB', 'BGRGB', 'RESET', 'ARG', 'TIME', 'REPORT', 'DATE',
    'ERR', 'COMMAND', 'ENVIRON', 'INPUT', 'UPPER', 'LOWER', 'SUM', 'EVAL',
})

# (min args, max args) of the string builtins a plan evaluates itself.
_PLAN_FUNC_ARITY = {
    'CHR': (1, 1), 'STR': (1, 1), 'LEFT': (1, 2), 'RIGHT': (1, 2),
    'MID': (2, 3), 'STRING': (1, 2), 'SPACE': (1, 1),
    'UCASE': (1, 1), 'LCASE': (1, 1),
}

# Numeric builtins of a string argument that compiled code may call.
_COMPILED_STR_CALLS = frozenset({'LEN', 'ASC', 'VAL', 'INSTR'})

# Glued BBC forms (LENA$ = LEN A$) start with these; their type is not static.
_GLUE_PREFIXES = ('LEN', 'ASC', 'VAL', 'INSTR', 'EVAL', 'NOT')


def _string_end(text: str, start: int) -> int:
    """Index after the literal opening at ``start`` (``""`` is an escaped quote)."""
    index = start + 1
    n = len(text)
    while index < n:
        if text[index] == '"':
            if index + 1 < n and text[index + 1] == '"':
                index += 2
                continue
            return index + 1
        index += 1
    return -1


def _close_paren(text: str, open_index: int) -> int:
    """Index of the ``)`` matching ``text[open_index]``, skipping literals; -1 if none."""
    depth = 0
    index = open_index
    n = len(text)
    while index < n:
        ch = text[index]
        if ch == '"':
            index = _string_end(text, index)
            if index < 0:
                return -1
            continue
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return -1


def _split_top_level(text: str, delim: str) -> Optional[List[str]]:
    """Split at ``delim`` outside literals and parentheses; None if unbalanced."""
    parts: List[str] = []
    depth = 0
    start = 0
    index = 0
    n = len(text)
    while index < n:
        ch = text[index]
        if ch == '"':
            index = _string_end(text, index)
            if index < 0:
                return None
            continue
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth < 0:
                return None
        elif ch == delim and depth == 0:
            parts.append(text[start:index].strip())
            start = index + 1
        index += 1
    if depth:
        return None
    parts.append(text[start:].strip())
    return parts


class RuntimeStrPlanMixin:
    """Mixin: static expression kind and cached string evaluation plans."""

    def _clear_string_plan_caches(self) -> None:
        self._static_kind_cache.clear()
        self._str_plan_cache.clear()
        self._str_call_thunks.clear()

    def _keyword_name(self, name: str) -> str:
        """``name`` as a keyword candidate: uppercase-only unless case folds."""
        if self._identifiers_case_sensitive():
            return name
        return name.upper()

    # ------------------------------------------------------------------ kind

    def _expr_static_kind(self, expr: str) -> Optional[str]:
        cached = self._static_kind_cache.get(expr, _MISSING)
        if cached is not _MISSING:
            return cached
        kind = self._compute_static_kind(expr.strip())
        self._static_kind_cache[expr] = kind
        return kind

    def _compute_static_kind(self, text: str) -> Optional[str]:
        index = 0
        n = len(text)
        while index < n and (text[index].isspace() or text[index] in '+-'):
            index += 1
        if index >= n:
            return None
        ch = text[index]
        if ch == '(':
            close = _close_paren(text, index)
            if close < 0:
                return None
            return self._compute_static_kind(text[index + 1:close].strip())
        if ch == '"':
            return 'str'
        if ch.isdigit() or ch in '.&%':
            return 'num'
        length = ident_prefix_len(text[index:])
        if not length:
            return None
        name = text[index:index + length]
        after = text[index + length:index + length + 1]
        upper = self._keyword_name(name)
        for prefix in _GLUE_PREFIXES:
            if upper.startswith(prefix) and upper != prefix:
                return None  # LENA$ / NOTA: glued keyword, type not static
        if after == '$':
            return 'str'
        if upper.startswith('FN'):
            return None  # QBasic-style FN names may return strings without $
        if after == '.':
            return None  # struct member
        return 'num'

    def _is_numeric_arith_item(self, item: str) -> bool:
        """``LEN(A$)+1`` / ``1+ASC("A")``: numeric although it mentions strings.

        Needs a numeric first operand, a top-level arithmetic operator and no
        top-level literal, so BBC juxtaposition (``1"foo"``, ``A%B$``) is not
        taken for arithmetic.
        """
        if self._expr_static_kind(item) != 'num':
            return False
        text = item.strip()
        depth = 0
        index = 0
        has_op = False
        n = len(text)
        while index < n:
            ch = text[index]
            if ch == '"':
                if depth == 0:
                    return False
                index = _string_end(text, index)
                if index < 0:
                    return False
                continue
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
            elif depth == 0 and index and ch in '+-*/^':
                has_op = True
            index += 1
        return has_op

    # ------------------------------------------------------------------ plan

    def _get_string_plan(self, expr: str) -> Optional[StrThunk]:
        plan = self._str_plan_cache.get(expr, _MISSING)
        if plan is not _MISSING:
            return plan
        try:
            plan = self._build_string_plan(expr.strip())
        except Exception:
            plan = None
        self._str_plan_cache[expr] = plan
        return plan

    def _string_thunk(self, expr: str) -> StrThunk:
        """Plan for ``expr``, else the text evaluator for it."""
        plan = self._get_string_plan(expr)
        if plan is not None:
            return plan
        return lambda: self._resolve_string_value(expr)

    def _build_string_plan(self, text: str) -> Optional[StrThunk]:
        if not text or '\\' in text:
            return None
        parts = _split_top_level(text, '+')
        if parts is None:
            return None
        thunks: List[StrThunk] = []
        for part in parts:
            thunk = self._build_string_term(part)
            if thunk is None:
                return None
            thunks.append(thunk)
        if len(thunks) == 1:
            return thunks[0]
        if len(thunks) == 2:
            first, second = thunks
            return lambda: first() + second()
        return lambda: ''.join([thunk() for thunk in thunks])

    def _build_string_term(self, term: str) -> Optional[StrThunk]:
        if not term:
            return None
        if term[0] == '"':
            if _string_end(term, 0) != len(term):
                return None  # juxtaposed "a" "b" chains keep the text path
            # "A""B" is one literal with a quote in it (BASIC V).
            value = self._decode_string_literal(term)
            return lambda: value
        if term[0] == '(':
            if _close_paren(term, 0) != len(term) - 1:
                return None
            return self._build_string_plan(term[1:-1].strip())
        length = ident_prefix_len(term)
        if not length or length >= len(term) or term[length] != '$':
            return None
        name = term[:length]
        upper = self._keyword_name(name)
        rest = term[length + 1:].strip()
        if not rest:
            if upper in _RESERVED_STR_NAMES or upper.startswith('FN'):
                return None
            if self._expand_dynamic_calls(term) != term:
                return None
            key = self._normalize_identifier(name)
            return lambda: self.str_variables.get(key, '')
        if rest[0] != '(' or _close_paren(rest, 0) != len(rest) - 1:
            return None
        if upper in _PLAN_FUNC_ARITY:
            return self._build_string_func(upper, rest[1:-1])
        if upper in _RESERVED_STR_NAMES or upper.startswith('FN'):
            return None
        parsed = self._parse_array_lvalue(term)
        if parsed is None or parsed[1] != 'str':
            return None
        base, _kind, indices_expr = parsed
        return lambda: str(
            self._array_get(base, 'str', self._eval_array_indices(indices_expr))
        )

    def _build_string_func(self, func: str, arg_text: str) -> Optional[StrThunk]:
        args = _split_top_level(arg_text, ',')
        if args is None or any(not arg for arg in args):
            return None
        low, high = _PLAN_FUNC_ARITY[func]
        if not low <= len(args) <= high:
            return None
        num = self._eval_numeric
        if func == 'CHR':
            code_expr = args[0]
            return lambda: chr(int(num(code_expr)) % 256)
        if func == 'STR':
            value_expr = args[0]
            return lambda: self._format_number(num(value_expr))
        if func == 'SPACE':
            count_expr = args[0]
            return lambda: ' ' * max(0, int(num(count_expr)))
        if func == 'STRING':
            count_expr = args[0]
            if len(args) == 1:
                return lambda: ' ' * max(0, int(num(count_expr)))
            second = args[1]
            if second.startswith('"'):
                text_of = self._string_thunk(second)

                def string_of_text() -> str:
                    count = int(num(count_expr))
                    text = text_of()
                    return (text[0] if text else ' ') * max(0, count)
                return string_of_text
            return lambda: chr(int(num(second)) % 256) * max(0, int(num(count_expr)))
        text_of = self._string_thunk(args[0])
        if func == 'UCASE':
            return lambda: text_of().upper()
        if func == 'LCASE':
            return lambda: text_of().lower()
        if func == 'LEFT':
            if len(args) == 1:
                return lambda: text_of()[:-1]
            length_expr = args[1]

            def left() -> str:
                text = text_of()
                return text[:max(0, int(num(length_expr)))]
            return left
        if func == 'RIGHT':
            if len(args) == 1:
                return lambda: text_of()[-1:]
            length_expr = args[1]

            def right() -> str:
                text = text_of()
                length = int(num(length_expr))
                return text[max(0, len(text) - length):]
            return right
        # MID$: non-positive length or start → empty (BBC), as the text path.
        start_expr = args[1]
        length_expr = args[2] if len(args) > 2 else None

        def mid() -> str:
            text = text_of()
            start_pos = int(num(start_expr))
            if length_expr is None:
                length = max(0, len(text) - start_pos + 1)
            else:
                length = int(num(length_expr))
            if length <= 0 or start_pos < 1:
                return ''
            return text[start_pos - 1:start_pos - 1 + length]
        return mid

    # --------------------------------------------------- numeric compile bridge

    def _rewrite_string_calls_for_compile(self, expr: str) -> Optional[str]:
        """``LEN(A$)+1`` → ``__sfn__(0)+1``; None unless every string is covered."""
        out: List[str] = []
        index = 0
        start = 0
        n = len(expr)
        changed = False
        while index < n:
            ch = expr[index]
            if ch == '"':
                index = _string_end(expr, index)
                if index < 0:
                    return None
                continue
            prev = expr[index - 1] if index else ' '
            if not (ch.isalpha() or ch == '_') or prev.isalnum() or prev in '_%$&!#@':
                index += 1
                continue
            length = ident_prefix_len(expr[index:])
            name = expr[index:index + length]
            func = self._keyword_name(name)
            open_index = index + length
            while open_index < n and expr[open_index] == ' ':
                open_index += 1
            if func not in _COMPILED_STR_CALLS or open_index >= n or expr[open_index] != '(':
                index += max(1, length)
                continue
            close = _close_paren(expr, open_index)
            if close < 0:
                return None
            call_id = self._string_call_id(func, expr[open_index + 1:close])
            if call_id is None:
                return None
            out.append(expr[start:index])
            out.append(f'__sfn__({call_id})')
            index = start = close + 1
            changed = True
        if not changed:
            return None
        out.append(expr[start:])
        result = ''.join(out)
        if '"' in result or '$' in result:
            return None
        return result

    def _string_call_id(self, func: str, arg_text: str) -> Optional[int]:
        args = _split_top_level(arg_text, ',')
        if args is None or any(not arg for arg in args):
            return None
        string_count = 2 if func == 'INSTR' else 1
        if func == 'INSTR' and len(args) not in (2, 3):
            return None
        if func != 'INSTR' and len(args) != 1:
            return None
        for arg in args[:string_count]:
            if self._get_string_plan(arg) is None:
                return None
        ident: Tuple[str, str] = (func, arg_text)
        call_id = self._compiled_str_call_ids.get(ident)
        if call_id is None:
            call_id = len(self._compiled_str_call_keys)
            self._compiled_str_call_keys.append(ident)
            self._compiled_str_call_ids[ident] = call_id
        return call_id

    def _compiled_str_call(self, call_id: int) -> object:
        """Runtime side of ``__sfn__`` in compiled expressions."""
        thunk = self._str_call_thunks.get(call_id)
        if thunk is None:
            thunk = self._build_str_call_thunk(*self._compiled_str_call_keys[call_id])
            self._str_call_thunks[call_id] = thunk
        return thunk()

    def _build_str_call_thunk(self, func: str, arg_text: str) -> Callable[[], object]:
        if func == 'LEN':
            text_of = self._string_thunk(arg_text)
            return lambda: float(len(text_of()))
        if func == 'ASC':
            text_of = self._string_thunk(arg_text)

            def asc() -> int:
                text = text_of()
                return ord(text[0]) if text else 0
            return asc
        return lambda: self._eval_numeric_builtin_call(func, arg_text)


def init_string_plan_state(interp: object) -> None:
    """Attributes the mixin needs; called from the interpreter constructor."""
    interp._static_kind_cache: Dict[str, Optional[str]] = {}
    interp._str_plan_cache: Dict[str, Optional[StrThunk]] = {}
    interp._str_call_thunks: Dict[int, Callable[[], object]] = {}
    # __sfn__ ids stay valid for the interpreter's life (like __aget__ ids).
    interp._compiled_str_call_keys: List[Tuple[str, str]] = []
    interp._compiled_str_call_ids: Dict[Tuple[str, str], int] = {}


__all__ = ['RuntimeStrPlanMixin', 'init_string_plan_state']
