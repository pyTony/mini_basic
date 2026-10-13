"""Pure-function tests for tools/editor_logic.py (no tkinter/display needed).

Covers: numbered- vs unnumbered-program detection, picking the next free
line number, and the auto-indent rules the tkinter editor applies on
Return and on finishing a closer keyword (NEXT/ENDPROC/...).
"""
from __future__ import annotations

import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from tools.editor_logic import (
    dedent_for_keyword,
    detect_numbered,
    first_keyword,
    indent_for_new_line,
    is_block_if,
    next_line_number,
    split_leading_number,
    split_leading_ws,
    used_line_numbers,
)

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


class TestDetectNumbered:
    def test_numbered_program_detected(self) -> None:
        text = '10 PRINT "hi"\n20 GOTO 10\n'
        assert detect_numbered(text) is True

    def test_unnumbered_program_detected(self) -> None:
        text = 'PRINT "hi"\nFOR i% = 1 TO 10\nNEXT\n'
        assert detect_numbered(text) is False

    def test_dialect_hint_alone_is_not_numbered(self) -> None:
        text = "1 REM dialect: bbc\nPRINT \"hi\"\n"
        assert detect_numbered(text) is False

    def test_blank_lines_are_ignored(self) -> None:
        assert detect_numbered('\n\n   \n') is False


class TestSplitHelpers:
    def test_split_leading_ws(self) -> None:
        assert split_leading_ws('    PRINT 1') == ('    ', 'PRINT 1')
        assert split_leading_ws('PRINT 1') == ('', 'PRINT 1')

    def test_split_leading_number(self) -> None:
        assert split_leading_number('10 PRINT 1') == (10, 'PRINT 1')
        assert split_leading_number('PRINT 1') == (None, 'PRINT 1')

    def test_used_line_numbers(self) -> None:
        text = '10 PRINT 1\n  20 PRINT 2\nPRINT "preamble"\n30 END\n'
        assert used_line_numbers(text) == {10, 20, 30}


class TestNextLineNumber:
    def test_first_line_defaults_to_ten(self) -> None:
        assert next_line_number(set(), None) == 10

    def test_steps_by_ten_after_a_line(self) -> None:
        assert next_line_number({10}, 10) == 20

    def test_skips_numbers_already_in_use(self) -> None:
        assert next_line_number({10, 20, 30}, 10) == 21


class TestBlockIf:
    def test_block_if_with_nothing_after_then(self) -> None:
        assert is_block_if('IF x% > 0 THEN') is True

    def test_single_line_if_is_not_a_block(self) -> None:
        assert is_block_if('IF x% > 0 THEN PRINT "yes"') is False

    def test_non_if_statement(self) -> None:
        assert is_block_if('PRINT "hi"') is False


class TestIndentForNewLine:
    def test_for_opens_a_block(self) -> None:
        assert indent_for_new_line('', 'FOR i% = 1 TO 10') == '    '

    def test_block_if_opens_a_block(self) -> None:
        assert indent_for_new_line('    ', 'IF x% > 0 THEN') == '        '

    def test_single_line_if_does_not_open_a_block(self) -> None:
        assert indent_for_new_line('', 'IF x% > 0 THEN PRINT "yes"') == ''

    def test_plain_statement_keeps_indent(self) -> None:
        assert indent_for_new_line('    ', 'PRINT "hi"') == '    '

    def test_def_proc_opens_a_block(self) -> None:
        assert indent_for_new_line('', 'DEF PROCgreet') == '    '


class TestDedentForKeyword:
    def test_next_dedents_one_step(self) -> None:
        assert dedent_for_keyword('        ', 'NEXT') == '    '

    def test_endproc_dedents_one_step(self) -> None:
        assert dedent_for_keyword('    ', 'ENDPROC') == ''

    def test_non_closer_keyword_is_unchanged(self) -> None:
        assert dedent_for_keyword('    ', 'PRINT') is None

    def test_cannot_dedent_below_zero(self) -> None:
        assert dedent_for_keyword('', 'NEXT') is None

    def test_else_dedents_one_step(self) -> None:
        assert dedent_for_keyword('        ', 'ELSE') == '    '


class TestFirstKeyword:
    def test_plain_keyword(self) -> None:
        assert first_keyword('  for i% = 1 to 10') == 'FOR'

    def test_no_keyword(self) -> None:
        assert first_keyword('   ') == ''
