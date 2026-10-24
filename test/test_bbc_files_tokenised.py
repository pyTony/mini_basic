""".bbc files must be tokenised so BBC BASIC for SDL can load them.

Text listings belong in .bas; tokenise them in BBCSDL (LOAD the .bas,
SAVE as .bbc).
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic.bbc_detokenize import detect_bbc_binary_format

pytestmark = [pytest.mark.non_gfx]


def _tracked_bbc_files():
    out = subprocess.run(['git', 'ls-files', '*.bbc', '*.BBC'], cwd=_ROOT,
                         capture_output=True, text=True)
    if out.returncode:
        pytest.skip('not a git checkout')
    return out.stdout.split()


def test_every_bbc_file_is_tokenised():
    text = [path for path in _tracked_bbc_files()
            if not detect_bbc_binary_format(open(os.path.join(_ROOT, path), 'rb').read())]
    assert text == []
