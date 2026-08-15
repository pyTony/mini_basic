"""MITS dialect vs Microsoft BASIC M6502 C-port tutorial examples.

Source: examples/m6502-cport/ (garyexplains/BASIC-M6502-CPORT, MIT).
Summary: docs/MITS_IMPLEMENTATION.md

Markers:
  mits          — any MITS dialect coverage
  m6502_cport   — this C-port example suite
  phase0        — baseline regression
  non_gfx       — no pygame
"""
from __future__ import annotations

import io
import os
import re
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [
    pytest.mark.phase0,
    pytest.mark.mits,
    pytest.mark.m6502_cport,
    pytest.mark.non_gfx,
]

_EXAMPLES = Path(_ROOT) / 'examples' / 'm6502-cport'

# Non-interactive ladder 01–48 that currently pass under --dialect mits
_PASS_01_48 = (
    '01_hello',
    '02_arithmetic',
    '03_numeric_variables',
    '04_integer_variables',
    '05_string_variables',
    '06_comparisons',
    '07_if_then',
    '08_goto_counter',
    '09_for_loop',
    '10_step_loop',
    '11_nested_loops',
    '12_gosub',
    '13_on_goto',
    '14_on_gosub',
    '15_numeric_array',
    '16_matrix',
    '17_string_array',
    '18_data_numbers',
    '19_data_strings',
    '20_restore',
    '21_def_fn_square',
    '22_def_fn_conversion',
    '23_math_functions',
    '24_trigonometry',
    '25_random_numbers',
    '26_string_functions',
    '27_string_conversion',
    '28_character_codes',
    '31_print_zones',
    '32_tab_and_spc',
    '33_colon_statements',
    '34_comments',
    '35_boolean_logic',
    '36_powers',
    '37_fibonacci',
    '38_factorial',
    '39_prime_numbers',
    '40_bubble_sort',
    '41_linear_search',
    '42_multiplication_table',
    '43_average',
    '44_minimum_maximum',
    '45_reverse_string',
    '46_palindrome',
    '47_histogram',
    '48_compound_interest',
)

# Known gaps (still useful as xfail regression locks)
_XFAIL_01_48 = {
    '29_peek_and_poke': 'POKE not implemented',
    '30_wait': 'POKE/WAIT memory not implemented',
}


def _load_numbered(path: Path, interp: BASICInterpreter) -> None:
    for raw in path.read_text(encoding='utf-8').splitlines():
        raw = raw.strip()
        if not raw:
            continue
        match = re.match(r'^(\d+)\s*(.*)$', raw)
        if not match:
            continue
        interp.set_program_line(int(match.group(1)), match.group(2))


def _run_example(name: str) -> tuple[int, str]:
    path = _EXAMPLES / f'{name}.bas'
    if not path.is_file():
        raise FileNotFoundError(path)
    interp = BASICInterpreter(
        InterpreterConfig(
            dialect='mits',
            display='none',
            display_locked=True,
            identifiers_case_sensitive=False,
        )
    )
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(io.StringIO()):
        _load_numbered(path, interp)
        interp.run()
    return int(getattr(interp, 'error_line_num', 0) or 0), buf.getvalue()


class M6502CportMitsPassTests(unittest.TestCase):
    """Examples that must keep working under mits."""

    def test_pass_count_documented(self):
        self.assertEqual(len(_PASS_01_48), 46)
        self.assertEqual(len(_XFAIL_01_48), 2)
        self.assertEqual(len(_PASS_01_48) + len(_XFAIL_01_48), 48)

    def test_hello(self):
        err, out = _run_example('01_hello')
        self.assertEqual(err, 0)
        self.assertIn('HELLO', out.upper())

    def test_for_and_gosub_band(self):
        for name in ('09_for_loop', '12_gosub', '13_on_goto'):
            err, out = _run_example(name)
            self.assertEqual(err, 0, msg=name)
            self.assertNotIn('?', out.splitlines()[0] if out else '', msg=name)

    def test_data_and_arrays_band(self):
        for name in ('15_numeric_array', '18_data_numbers', '20_restore'):
            err, _ = _run_example(name)
            self.assertEqual(err, 0, msg=name)

    def test_algorithms_band(self):
        for name in ('37_fibonacci', '40_bubble_sort', '48_compound_interest'):
            err, out = _run_example(name)
            self.assertEqual(err, 0, msg=name)
            self.assertTrue(out.strip(), msg=name)


@pytest.mark.parametrize('name', list(_PASS_01_48))
def test_m6502_pass_parametrized(name: str):
    err, out = _run_example(name)
    assert err == 0, f'{name}: error_line={err} out={out[:200]!r}'


@pytest.mark.parametrize('name,reason', sorted(_XFAIL_01_48.items()))
def test_m6502_known_gaps_still_fail(name: str, reason: str):
    """Documented gaps: must keep failing until fixed (then remove from map)."""
    err, out = _run_example(name)
    broken = err != 0 or any(
        line.lstrip().startswith('?') for line in out.splitlines()
    )
    assert broken, (
        f'{name} unexpectedly passed ({reason}) — '
        'update docs/MITS_IMPLEMENTATION.md and _XFAIL_01_48'
    )


class M6502CportMitsDialectGates(unittest.TestCase):
    """mits dialect gates used alongside the tutorial suite."""

    def test_while_forbidden_strict(self):
        interp = BASICInterpreter(
            InterpreterConfig(
                dialect='mits',
                strict_dialect=True,
                display='none',
                display_locked=True,
            )
        )
        self.assertFalse(interp._dialect_allows('WHILE'))
        self.assertFalse(interp._dialect_allows('PROC'))

    def test_goto_for_allowed(self):
        interp = BASICInterpreter(
            InterpreterConfig(dialect='mits', display='none', display_locked=True)
        )
        self.assertTrue(interp._dialect_allows('if_then_line'))
        self.assertTrue(interp._dialect_allows('numbered_program'))


if __name__ == '__main__':
    unittest.main()
