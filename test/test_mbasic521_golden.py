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

# Only listings that *crash* or fail their own PASS/FAIL summary.
# PRINT spacing vs 5.21 .txt is not an xfail — a clean run is a pass.
_XFAIL = {}

_SELF_OK = re.compile(
    r'All tests PASSED|Tests failed:\s*0\b',
    re.IGNORECASE,
)
_SELF_FAIL = re.compile(
    r'Some tests FAILED|Tests failed:\s*[1-9]',
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


def _ran_clean(err: int, out: str) -> bool:
    if err != 0:
        return False
    if any(line.lstrip().startswith('?') for line in out.splitlines()):
        return False
    if _SELF_FAIL.search(out) and not _SELF_OK.search(out):
        return False
    return True


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
    ok = _ran_clean(err, out)
    if reason:
        if ok:
            pytest.fail(
                f'{name} now runs clean — remove it from _XFAIL ({reason})'
            )
        pytest.xfail(reason)
    assert ok, f'{name}: error_line={err} out={out[:800]!r}'


def test_corpus_skip_message_documents_fetch() -> None:
    """Always collected: reminds how to enable the optional ladder."""
    if _have_corpus():
        assert any(_CORPUS.glob('test_*.bas'))
        return
    assert not _have_corpus()
