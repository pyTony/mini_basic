"""LIST must glue PROC/FN names for Archimedes / RISC OS paste."""
from __future__ import annotations

import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic.format.save_case import glue_bbc_proc_fn_names, format_program_line
from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [pytest.mark.phase1]


def test_glue_proc_fn_names():
    assert glue_bbc_proc_fn_names('PROC SWOOSH(M0)') == 'PROCSWOOSH(M0)'
    assert glue_bbc_proc_fn_names('DEF PROC LETTER') == 'DEFPROCLETTER'
    assert glue_bbc_proc_fn_names('PROC PLOT: END PROC') == 'PROCPLOT: ENDPROC'
    assert 'PROC SWOOSH' not in glue_bbc_proc_fn_names('FOR I%=1: PROC SWOOSH(M0): NEXT')


def test_format_program_line_glues_proc():
    line = format_program_line('PROC SWOOSH(M0): PROC LETTER', 'upper')
    assert 'PROCSWOOSH(M0)' in line
    assert 'PROCLETTER' in line
    assert 'PROC S' not in line


def test_list_line_glues_proc():
    interp = BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', display_locked=True),
    )
    out = interp.format_list_line('FOR I%=1 TO 2: PROCSWOOSH(M0): NEXT')
    # Internal storage may already be spaced; list output must be glued.
    assert 'PROCSWOOSH' in out.replace(' ', '') or 'PROCSWOOSH' in out
    assert 'PROC SWOOSH' not in out
