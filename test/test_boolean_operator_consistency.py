"""Systematic check for siblings of the PRINT-AND-comparison bug (#33/#35).

Root cause of that bug: ``_eval_whole_arith`` (PRINT's fast numeric-
formatting path) normalized AND/OR/EOR to Python's bitwise &/|/^ before
handing the text to ``eval()``. Those bitwise operators bind *tighter*
than Python's </>/==, so "A>0 AND B>0" became the text "A>0 & B>0", which
Python parsed as the chained comparison "A > (0 & B) > 0" instead of two
comparisons ANDed together. ``IF``/assignment used a different code path
(``_eval_numeric``) that already special-cased boolean syntax, so only
PRINT's fast path silently gave the wrong answer — the bug class is a
*divergence between evaluation paths for the same expression text*, not
something specific to AND.

Rather than hand-computing truth tables (easy to get wrong and only as
good as the operators we think to check), each case here runs the same
expression through PRINT, assignment-then-PRINT and IF-then-PRINT and
asserts all three agree — exactly the property that broke for AND. This
catches any sibling operator/construct for which one path has the
boolean-syntax special case and another doesn't, without needing to know
in advance which one is wrong.

See test_print_and_comparison.py for the original, narrower regression
test (AND specifically, plus the struct-member case from the bug report).
"""
from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stdout

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


def _run(lines: list[str], dialect: str = 'mini') -> str:
    cfg = InterpreterConfig(display='none', display_locked=True, dialect=dialect)
    interp = BASICInterpreter(cfg)
    buf = io.StringIO()
    with redirect_stdout(buf):
        for raw in lines:
            num_s, stmt = raw.split(' ', 1)
            interp.set_program_line(int(num_s), stmt)
        interp.run()
    return buf.getvalue().strip()


# (label, setup lines, expr) — expr must be a single boolean/comparison
# expression usable directly after PRINT / X= / IF ... THEN.
CASES: list[tuple[str, list[str], str]] = [
    ('and_true_true', ['A=5', 'B=5'], 'A>0 AND B>0'),
    ('and_true_false', ['A=5', 'B=-1'], 'A>0 AND B>0'),
    ('and_false_false', ['A=-5', 'B=-1'], 'A>0 AND B>0'),
    ('or_true_false', ['A=5', 'B=-1'], 'A>0 OR B>0'),
    ('or_false_false', ['A=-5', 'B=-1'], 'A>0 OR B>0'),
    ('eor_true_true', ['A=5', 'B=5'], 'A>0 EOR B>0'),
    ('eor_true_false', ['A=5', 'B=-1'], 'A>0 EOR B>0'),
    ('xor_true_false', ['A=5', 'B=-1'], 'A>0 XOR B>0'),
    ('eqv_true_true', ['A=5', 'B=5'], 'A>0 EQV B>0'),
    ('not_true', ['A=5'], 'NOT (A>0)'),
    ('not_false', ['A=-5'], 'NOT (A>0)'),
    ('and_chain_3_all_true', ['A=5', 'B=5', 'C=5'], 'A>0 AND B>0 AND C>0'),
    ('and_chain_3_last_false', ['A=5', 'B=5', 'C=-5'], 'A>0 AND B>0 AND C>0'),
    (
        'mixed_or_and_precedence',
        ['A=-5', 'B=5', 'C=5'],
        'A>0 OR B>0 AND C>0',
    ),
    (
        'mixed_and_or_parens',
        ['A=-5', 'B=-5', 'C=5'],
        '(A>0 AND B>0) OR C>0',
    ),
    ('chained_relational_true', ['A=3', 'B=2', 'C=1'], 'A>B AND B>C'),
    ('chained_gt_gt_basic', ['A=3', 'B=2', 'C=1'], 'A>B>C'),
    ('not_equal_and_equal', ['A=3', 'B=2', 'C=1', 'D=1'], 'A<>B AND C=D'),
    (
        'comparison_as_operand',
        ['A=5', 'B=5'],
        '(A>0) = (B>0)',
    ),
    (
        'string_and_comparison',
        ['A$="foo"', 'B$="bar"'],
        'A$="foo" AND B$="bar"',
    ),
    (
        'string_or_comparison',
        ['A$="foo"', 'B$="nope"'],
        'A$="foo" OR B$="nope"',
    ),
]


class BooleanOperatorConsistencyTests(unittest.TestCase):
    """PRINT / assignment / IF must agree on every boolean-syntax expression."""

    def test_consistency_across_paths(self):
        for label, setup, expr in CASES:
            for dialect in ('mini', 'bbc'):
                with self.subTest(case=label, dialect=dialect):
                    lines = [f'{10 + i * 10} {stmt}' for i, stmt in enumerate(setup)]
                    base = 10 + len(setup) * 10
                    lines += [
                        f'{base} PRINT {expr}',
                        f'{base + 10} X = {expr}',
                        f'{base + 20} PRINT X',
                        f'{base + 30} IF {expr} THEN PRINT -1 ELSE PRINT 0',
                        f'{base + 40} END',
                    ]
                    # bbc dialect right-pads numeric PRINT output with
                    # leading spaces — strip per line, not just the whole
                    # blob, so that padding isn't mistaken for divergence.
                    out = [
                        line.strip() for line in _run(lines, dialect=dialect).splitlines()
                    ]
                    self.assertEqual(
                        len(out), 3,
                        msg=(label, dialect, expr, out),
                    )
                    print_val, assign_val, if_val = out
                    self.assertEqual(
                        print_val, assign_val,
                        msg=f'{label} ({dialect}): PRINT {expr!r} -> {print_val!r} '
                            f'but assignment -> {assign_val!r}',
                    )
                    self.assertEqual(
                        print_val, if_val,
                        msg=f'{label} ({dialect}): PRINT {expr!r} -> {print_val!r} '
                            f'but IF -> {if_val!r}',
                    )

    def test_struct_member_and_or_eor(self):
        for op, w, h, expected in (
            ('AND', 10, 20, -1),
            ('AND', 0, 20, 0),
            ('OR', 0, 20, -1),
            ('OR', 0, 0, 0),
            ('EOR', 10, 0, -1),
            ('EOR', 10, 20, 0),
        ):
            with self.subTest(op=op, w=w, h=h):
                lines = [
                    '10 DIM M{W%, H%}',
                    f'20 M.W% = {w}',
                    f'30 M.H% = {h}',
                    f'40 PRINT M.W% > 0 {op} M.H% > 0',
                    '50 END',
                ]
                out = _run(lines, dialect='bbc')
                self.assertEqual(out, str(expected), msg=(op, w, h))

    def test_array_element_and_or(self):
        lines = [
            '10 DIM ARR(3)',
            '20 ARR(1) = 5',
            '30 ARR(2) = -5',
            '40 PRINT ARR(1)>0 AND ARR(2)>0',
            '50 PRINT ARR(1)>0 OR ARR(2)>0',
            '60 END',
        ]
        out = [line.strip() for line in _run(lines, dialect='bbc').splitlines()]
        self.assertEqual(out, ['0', '-1'])


if __name__ == '__main__':
    unittest.main()
