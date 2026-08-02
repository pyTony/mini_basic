"""CLI --version / -V report."""
from __future__ import annotations

import os
import sys
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import __version__, format_version_report, main
from mini_basic.version import print_version_report

pytestmark = [pytest.mark.phase0]


def test_format_version_report_includes_version_and_minibasic_dir():
    with patch.dict(os.environ, {'MINIBASIC_DIR': r'C:\fake\minibasic'}, clear=False):
        text = format_version_report()
    assert __version__ in text
    assert 'mini_basic' in text
    assert 'MINIBASIC_DIR' in text
    assert r'C:\fake\minibasic' in text or 'fake' in text
    assert 'Implementation status' in text
    assert 'process env' in text


def test_main_version_exits_zero():
    buf = StringIO()
    with redirect_stdout(buf):
        with pytest.raises(SystemExit) as exc:
            main(['--version'])
    assert exc.value.code == 0
    assert 'mini_basic' in buf.getvalue()
    assert __version__ in buf.getvalue()


def test_main_version_short_flag():
    buf = StringIO()
    with redirect_stdout(buf):
        with pytest.raises(SystemExit) as exc:
            main(['-V'])
    assert exc.value.code == 0
    assert 'Implementation status' in buf.getvalue()
