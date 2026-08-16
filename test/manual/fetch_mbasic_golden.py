#!/usr/bin/env python3
"""Download curated MBASIC 5.21 golden tests (not the 177-program library).

Source: https://github.com/avwohl/mbasic
  basic/dev/tests_with_results/<name>.bas and <name>.txt

These files are not copied into git (license differs). Fetch locally:

    python test/manual/fetch_mbasic_golden.py

Then:

    python -m pytest -q test/test_mbasic521_golden.py --timeout=45
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DEST = _ROOT / 'test' / 'corpus' / 'mbasic521'
_BASE = (
    'https://raw.githubusercontent.com/avwohl/mbasic/main/'
    'basic/dev/tests_with_results/'
)

# Batch-safe programs only. No interactive INPUT/INKEY, no PEEK, no UI demos.
NAMES = (
    'test_operator_precedence',
    'test_mod_intdiv',
    'test_logical_ops',
    'test_eqv_imp',
    'test_gosub',
    'test_goto',
    'test_for_next',
    'test_on_goto_gosub',
    'test_if_then_else',
    'test_data_read',
    'test_def_fn',
    'test_dim_arrays',
    'test_option_base',
    'test_swap',
    'test_erase',
    'test_string_functions',
    'test_mid_assignment',
    'test_tab_spc',
    'test_hex_oct',
    'test_type_conversion',
    'test_deftypes',
    'test_print_using',
    'test_math_functions',
    'test_file_io',
    'test_random_files',
    'test_chain',
    'test_while_wend',
)


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': 'mini_basic-fetch'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def main() -> int:
    _DEST.mkdir(parents=True, exist_ok=True)
    ok = 0
    for name in NAMES:
        for ext in ('.bas', '.txt'):
            url = _BASE + name + ext
            dest = _DEST / (name + ext)
            try:
                dest.write_bytes(_get(url))
            except urllib.error.HTTPError as exc:
                print(f'FAIL {name}{ext}: HTTP {exc.code}', file=sys.stderr)
                return 1
            except urllib.error.URLError as exc:
                print(f'FAIL {name}{ext}: {exc}', file=sys.stderr)
                return 1
        ok += 1
        print(name)
    print(f'Wrote {ok} programs to {_DEST}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
