import pytest
from mini_basic.dialect_hint import parse_shebang_line, DialectHint


def test_parse_shebang_not_shebang():
    assert parse_shebang_line("REM dialect: bbc") is None
    assert parse_shebang_line("' dialect: bbc") is None
    assert parse_shebang_line("10 PRINT \"Hello\"") is None
    assert parse_shebang_line("") is None


def test_parse_shebang_empty():
    assert parse_shebang_line("#!") is None
    assert parse_shebang_line("#!  ") is None


def test_parse_shebang_direct_dialect():
    assert parse_shebang_line("#! bbc") == DialectHint(dialect='bbc')
    assert parse_shebang_line("#!bbc") == DialectHint(dialect='bbc')
    assert parse_shebang_line("#! tiny") == DialectHint(dialect='tiny')
    assert parse_shebang_line("#!mini") == DialectHint(dialect='mini')
    assert parse_shebang_line("#!commodore") == DialectHint(dialect='commodore')
    assert parse_shebang_line("#!mits") == DialectHint(dialect='mits')
    # Extra spaces
    assert parse_shebang_line("  #!   bbc  ") == DialectHint(dialect='bbc')


def test_parse_shebang_env_dialect():
    assert parse_shebang_line("#!/usr/bin/env python -m mini_basic --dialect bbc") == DialectHint(dialect='bbc')
    assert parse_shebang_line("#!/usr/bin/env python -m mini_basic --dialect=tiny") == DialectHint(dialect='tiny')
    assert parse_shebang_line("#!/usr/bin/env python -m mini-basic --dialect=mits") == DialectHint(dialect='mits')
    assert parse_shebang_line("#!/usr/bin/env python -m mini basic --dialect commodore") == DialectHint(dialect='commodore')


def test_parse_shebang_colon_dialect():
    assert parse_shebang_line("#!/usr/local/bin/mini-basic : mits") == DialectHint(dialect='mits')
    assert parse_shebang_line("#!/usr/bin/minibasic:bbc") == DialectHint(dialect='bbc')
    assert parse_shebang_line("#!/usr/bin/mini_basic: tiny") == DialectHint(dialect='tiny')


def test_parse_shebang_token_dialect():
    assert parse_shebang_line("#!/usr/bin/env mini_basic tiny") == DialectHint(dialect='tiny')
    assert parse_shebang_line("#!/usr/bin/mini-basic mits") == DialectHint(dialect='mits')
    assert parse_shebang_line("#!/usr/bin/minibasic bbc") == DialectHint(dialect='bbc')
    assert parse_shebang_line("#!/usr/bin/mini basic commodore") == DialectHint(dialect='commodore')


def test_parse_shebang_invalid_dialect():
    assert parse_shebang_line("#!/usr/bin/env python -m mini_basic --dialect foo") is None
    assert parse_shebang_line("#!/usr/local/bin/mini-basic : unknown") is None
    assert parse_shebang_line("#!/usr/bin/env mini_basic invalid") is None
    assert parse_shebang_line("#! not_a_dialect") is None


def test_parse_shebang_modifiers():
    # Strict
    assert parse_shebang_line("#! bbc strict").strict is True
    assert parse_shebang_line("#!/usr/bin/env python -m mini_basic --dialect bbc --strict-dialect").strict is True

    # Case sensitive
    assert parse_shebang_line("#! bbc case sensitive").case_sensitive is True
    assert parse_shebang_line("#! bbc sensitive").case_sensitive is True

    # Case insensitive
    assert parse_shebang_line("#! bbc case insensitive").case_sensitive is False
    assert parse_shebang_line("#! bbc casefold").case_sensitive is False
    assert parse_shebang_line("#! bbc fold").case_sensitive is False

    # Combinations
    hint = parse_shebang_line("#! bbc strict casefold")
    assert hint.dialect == 'bbc'
    assert hint.strict is True
    assert hint.case_sensitive is False
