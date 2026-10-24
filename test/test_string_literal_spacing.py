"""Spaces inside "string literals" must survive entry canonicalization."""
from __future__ import annotations

import pytest

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

pytestmark = [pytest.mark.phase0, pytest.mark.non_gfx]


@pytest.mark.parametrize('dialect', ['mini', 'bbc', 'mits'])
def test_suffix_characters_do_not_eat_spaces_in_strings(dialect):
    interp = BASICInterpreter(InterpreterConfig(dialect=dialect, display='none', display_locked=True))
    interp.set_program_line(10, 'PRINT "HI!  I\'M BETH $ #  5"')
    assert '"HI!  I\'M BETH $ #  5"' in interp.program[10]


def test_suffix_gluing_still_applies_outside_strings():
    interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none', display_locked=True))
    interp.set_program_line(10, 'A $ = "X $ Y"')
    assert interp.program[10] == 'A$ = "X $ Y"'
