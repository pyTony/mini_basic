"""Prove new _split_at_depth fixes weaknesses of regex / naive legacy splitters."""
from __future__ import annotations

import io
import re
import sys
import unittest
from contextlib import redirect_stdout
from typing import Callable, List, Tuple
from unittest.mock import patch

_ROOT = __file__.replace("\\", "/").rsplit("/test/", 1)[0]
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig


# --- Legacy implementations (pre-unification / regex) ---


def legacy_regex_comma_split(text: str) -> List[str]:
    """Naive top-level comma split — breaks on commas in strings and parens."""
    if not text:
        return ['']
    return [part.strip() for part in re.split(r',', text)]


def legacy_naive_first_delim(text: str, delim: str) -> Tuple[str, str]:
    """Old _parse_otherwise_spec style: str.find(delim), ignores strings."""
    index = text.find(delim)
    if index >= 0:
        return text[:index].strip(), text[index + 1:].strip()
    return text.strip(), ''


def legacy_monolithic_split_args(arg: str) -> List[str]:
    """Snapshot-era loop: depth + in_string, but no BBC \"\" escape."""
    args: List[str] = []
    current: List[str] = []
    depth = 0
    in_string = False
    for ch in arg:
        if ch == '"':
            in_string = not in_string
        elif ch == '(' and not in_string:
            depth += 1
        elif ch == ')' and not in_string:
            depth -= 1
        elif ch == ',' and not in_string and depth == 0:
            args.append(''.join(current).strip())
            current = []
            continue
        current.append(ch)
    args.append(''.join(current).strip())
    return args


def legacy_monolithic_split_input_line(line: str) -> List[str]:
    """Pre-one-liner INPUT value split (same structure, no shared BBC rules)."""
    parts: List[str] = []
    current: List[str] = []
    in_string = False
    for ch in line:
        if ch == '"':
            in_string = not in_string
            current.append(ch)
        elif ch == ',' and not in_string:
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    parts.append(''.join(current).strip())
    return parts


def legacy_regex_vdu_parts(rest: str) -> List[str]:
    return [part.strip() for part in re.split(r',', rest) if part.strip()]


def legacy_monolithic_colon_statements(line: str) -> List[str]:
    """Snapshot colon splitter: no REM guard, no WHEN/OTHERWISE guard."""
    parts: List[str] = []
    current: List[str] = []
    in_string = False
    after_then = False
    index = 0
    while index < len(line):
        ch = line[index]
        if ch == '"':
            in_string = not in_string
            current.append(ch)
            index += 1
            continue
        if (
            not in_string
            and not after_then
            and line[index:index + 4].upper() == 'THEN'
            and (index == 0 or not line[index - 1].isalnum())
            and (index + 4 >= len(line) or not line[index + 4].isalnum())
        ):
            after_then = True
            current.append(line[index:index + 4])
            index += 4
            continue
        if ch == ':' and not in_string:
            part = ''.join(current).strip()
            if after_then:
                current.append(ch)
                index += 1
                continue
            if part:
                parts.append(part)
            current = []
            after_then = False
            index += 1
            continue
        current.append(ch)
        index += 1
    part = ''.join(current).strip()
    if part:
        parts.append(part)
    return parts


class SplitterCase:
    __slots__ = ('name', 'expected', 'text', 'delim', 'mode')

    def __init__(
        self,
        name: str,
        text: str,
        expected: object,
        *,
        delim: str = ',',
        mode: str = 'list',
    ) -> None:
        self.name = name
        self.text = text
        self.expected = expected
        self.delim = delim
        self.mode = mode


UNIT_CASES = [
    SplitterCase(
        'commas_inside_strings',
        '"Hello, world", 42',
        ['"Hello, world"', '42'],
    ),
    SplitterCase(
        'nested_parens_fn_args',
        'FNSUM(1+2, 3+4), 5',
        ['FNSUM(1+2, 3+4)', '5'],
    ),
    SplitterCase(
        'bbc_doubled_quotes',
        '"a""b",c',
        ['"a""b"', 'c'],
    ),
    SplitterCase(
        'colon_inside_string',
        'WHEN "x:y": PRINT',
        ('WHEN "x:y"', 'PRINT'),
        delim=':',
        mode='pair',
    ),
    SplitterCase(
        'plus_inside_string',
        '"A+B" + "C"',
        ['"A+B"', '"C"'],
        delim='+',
        mode='list_plus',
    ),
    SplitterCase(
        'colon_in_print_string',
        'PRINT "A:B:C" : PRINT "ok"',
        ['PRINT "A:B:C"', 'PRINT "ok"'],
        mode='colon_line',
    ),
    SplitterCase(
        'rem_colon_segment',
        'PRINT "Hi" : REM comment : PRINT "There"',
        ['PRINT "Hi"', 'REM comment : PRINT "There"'],
        mode='colon_line',
    ),
]


class ParsingLegacyVerifyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.interp = BASICInterpreter(
            InterpreterConfig(dialect='bbc', display='none'),
        )

    def _new_result(self, case: SplitterCase) -> object:
        if case.mode == 'pair':
            return self.interp._split_first_at_depth(case.text, case.delim)
        if case.mode == 'colon_line':
            return self.interp._split_colon_statements(case.text)
        if case.mode == 'list_plus':
            return self.interp._split_at_depth(
                case.text,
                case.delim,
                skip_empty=True,
            )
        return self.interp._split_at_depth(case.text, case.delim)

    def test_new_splitters_pass_all_weakness_cases(self) -> None:
        for case in UNIT_CASES:
            with self.subTest(case=case.name):
                self.assertEqual(self._new_result(case), case.expected)

    def test_regex_comma_split_fails_key_cases(self) -> None:
        failures: List[str] = []
        for case in UNIT_CASES:
            if case.mode != 'list':
                continue
            got = legacy_regex_comma_split(case.text)
            if got != case.expected:
                failures.append(case.name)
        self.assertIn('commas_inside_strings', failures)
        self.assertIn('nested_parens_fn_args', failures)
        self.assertGreater(len(failures), 0, 'expected regex comma split to fail somewhere')

    def test_naive_colon_find_fails_inside_string(self) -> None:
        case = next(c for c in UNIT_CASES if c.name == 'colon_inside_string')
        self.assertEqual(
            legacy_naive_first_delim(case.text, ':'),
            ('WHEN "x', 'y": PRINT'),
        )
        self.assertEqual(self._new_result(case), case.expected)

    def test_monolithic_args_matches_new_on_bbc_doubled_quotes(self) -> None:
        """Snapshot loop toggles quotes; this case is not a differentiator."""
        case = next(c for c in UNIT_CASES if c.name == 'bbc_doubled_quotes')
        self.assertEqual(legacy_monolithic_split_args(case.text), case.expected)
        self.assertEqual(self._new_result(case), case.expected)

    def test_regex_split_args_breaks_nested_fn_call_operand(self) -> None:
        arg = 'FNSUM(1,2), 5'
        self.assertEqual(self.interp._split_at_depth(arg, ','), ['FNSUM(1,2)', '5'])
        self.assertEqual(
            legacy_regex_comma_split(arg),
            ['FNSUM(1', '2)', '5'],
        )

    def test_regex_vdu_split_breaks_on_commas_in_expressions(self) -> None:
        rest = 'STR$("a,b"), 1'
        self.assertEqual(
            legacy_regex_vdu_parts(rest),
            ['STR$("a', 'b")', '1'],
        )
        self.assertEqual(
            self.interp._split_at_depth(rest, ',', skip_empty=True),
            ['STR$("a,b")', '1'],
        )

    def test_legacy_colon_splitter_lacks_rem_guard(self) -> None:
        case = next(c for c in UNIT_CASES if c.name == 'rem_colon_segment')
        legacy = legacy_monolithic_colon_statements(case.text)
        self.assertEqual(
            legacy,
            ['PRINT "Hi"', 'REM comment', 'PRINT "There"'],
        )
        self.assertEqual(self._new_result(case), case.expected)

    def test_parsing_program_suite_passes_on_new_runtime_only(self) -> None:
        """All 28 BASIC parsing regression tests pass on current runtime."""
        suite = unittest.defaultTestLoader.loadTestsFromName('test.test_parsing')
        result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        self.assertTrue(result.wasSuccessful(), result.failures + result.errors)

    def test_otherwise_spec_fails_with_naive_colon(self) -> None:
        with patch.object(
            self.interp,
            '_split_first_at_depth',
            lambda text, delim: legacy_naive_first_delim(text, delim),
        ):
            head, tail = self.interp._parse_otherwise_spec(
                'OTHERWISE "a:b": PRINT',
            )
        self.assertEqual(head, 'OTHERWISE "a')
        self.assertEqual(tail, 'b": PRINT')

        head, tail = self.interp._parse_otherwise_spec('OTHERWISE "a:b": PRINT')
        self.assertEqual(head, 'OTHERWISE "a:b"')
        self.assertEqual(tail, 'PRINT')


if __name__ == '__main__':
    unittest.main()