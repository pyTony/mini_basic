"""Optional MBASIC 5.21 golden ladder (fetched, not vendored).

Fetch first:

    python test/manual/fetch_mbasic_golden.py

If ``test/corpus/mbasic521/`` is empty, every test here skips so a plain
clone stays green. This is a mits coverage ladder, not a 5.21-compat claim.

Source of the listings: https://github.com/avwohl/mbasic
  basic/dev/tests_with_results/
"""
from __future__ import annotations

import io
import os
import re
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

pytestmark = [
    pytest.mark.phase1,
    pytest.mark.mits,
    pytest.mark.non_gfx,
]

_CORPUS = Path(_ROOT) / 'test' / 'corpus' / 'mbasic521'

# Dialect override. Default is mits.
_DIALECT = {
    'test_while_wend': 'mini',
}

# Product-honest gaps. Remove a name when an implement cycle makes it match.
_XFAIL = {
    'test_operator_precedence': 'EXPECTED parsed as EXP(ECTED)',
    'test_mod_intdiv': 'PRINT spacing or \\ / MOD vs 5.21 transcript',
    'test_logical_ops': 'PRINT spacing or AND/OR/NOT vs 5.21 transcript',
    'test_gosub': 'PRINT spacing vs 5.21 transcript',
    'test_goto': 'PRINT spacing vs 5.21 transcript',
    'test_for_next': 'FOR 10 TO 1 still iterates; PRINT glue vs 5.21',
    'test_data_read': 'PRINT spacing vs 5.21 transcript',
    'test_def_fn': 'FN GREET$ / quote-build line errors',
    'test_dim_arrays': 'PRINT spacing vs 5.21 transcript',
    'test_option_base': 'OPTION BASE or PRINT spacing vs 5.21',
    'test_swap': 'PRINT spacing vs 5.21 transcript',
    'test_erase': 'ERASE statement not implemented',
    'test_string_functions': 'PRINT glue (LEFT$works) vs 5.21 transcript',
    'test_tab_spc': 'TAB/SPC columns vs 5.21 WIDTH',
    'test_while_wend': 'PRINT spacing vs 5.21 transcript',
    'test_print_using': 'USING column layout vs 5.21 / IEEE vs MBF',
    'test_file_io': 'KILL / NAME AS / sequential details may differ',
    'test_random_files': 'FIELD / GET / PUT record layout may differ',
    'test_chain': 'CHAIN + written partner file / working dir',
    'test_deftypes': 'DEFINT/DEFSNG/DEFDBL letter-range depth',
    'test_mid_assignment': 'MID$(a$,i)=… may differ',
    'test_hex_oct': '&H / &O literals if incomplete',
    'test_type_conversion': 'CINT/CSNG/CDBL/FIX vs IEEE',
    'test_math_functions': 'transcendental rounding vs MBF',
    'test_eqv_imp': 'EQV/IMP bit values if incomplete',
}

_SELF_OK = re.compile(
    r'All tests PASSED|Tests failed:\s*0\b',
    re.IGNORECASE,
)


def _have_corpus() -> bool:
    return _CORPUS.is_dir() and any(_CORPUS.glob('test_*.bas'))


def _load_numbered(path: Path, interp: BASICInterpreter) -> None:
    for raw in path.read_text(encoding='utf-8', errors='replace').splitlines():
        text = raw.strip()
        if not text:
            continue
        match = re.match(r'^(\d+)\s*(.*)$', text)
        if not match:
            continue
        interp.set_program_line(int(match.group(1)), match.group(2))


def _normalize(text: str) -> str:
    lines = [ln.rstrip() for ln in text.replace('\r\n', '\n').replace('\r', '\n').split('\n')]
    while lines and not lines[-1]:
        lines.pop()
    return '\n'.join(lines)


def _run(name: str, tmp_path: Path) -> tuple[int, str]:
    path = _CORPUS / f'{name}.bas'
    dialect = _DIALECT.get(name, 'mits')
    interp = BASICInterpreter(
        InterpreterConfig(
            dialect=dialect,
            display='none',
            display_locked=True,
            identifiers_case_sensitive=False,
        )
    )
    interp.working_dir = str(tmp_path)
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(io.StringIO()):
        _load_numbered(path, interp)
        interp.run()
    return int(getattr(interp, 'error_line_num', 0) or 0), buf.getvalue()


def _matches_golden(name: str, out: str) -> bool:
    if _SELF_OK.search(out):
        return True
    golden = _CORPUS / f'{name}.txt'
    if not golden.is_file():
        return False
    return _normalize(out) == _normalize(golden.read_text(encoding='utf-8', errors='replace'))


def _program_names() -> list[str]:
    if not _have_corpus():
        return []
    names = sorted(p.stem for p in _CORPUS.glob('test_*.bas'))
    return names


@pytest.mark.skipif(not _have_corpus(), reason='run: python test/manual/fetch_mbasic_golden.py')
@pytest.mark.parametrize('name', _program_names() or ['__no_corpus__'])
def test_mbasic521_golden(name: str, tmp_path: Path) -> None:
    if name == '__no_corpus__':
        pytest.skip('run: python test/manual/fetch_mbasic_golden.py')
    reason = _XFAIL.get(name)
    err, out = _run(name, tmp_path)
    crashed = err != 0 or any(
        line.lstrip().startswith('?') for line in out.splitlines()
    )
    ok = (not crashed) and _matches_golden(name, out)
    if reason:
        if ok:
            pytest.fail(
                f'{name} now matches — remove it from _XFAIL ({reason})'
            )
        pytest.xfail(reason)
    assert not crashed, f'{name}: error_line={err} out={out[:400]!r}'
    assert ok, f'{name}: output mismatch\n--- got ---\n{out[:800]}'


def test_corpus_skip_message_documents_fetch() -> None:
    """Always collected: reminds how to enable the optional ladder."""
    if _have_corpus():
        assert any(_CORPUS.glob('test_*.bas'))
        return
    assert not _have_corpus()
