"""Smoke tests for tools/make_shortcut.py: pure helpers only, no desktop I/O."""
from __future__ import annotations

import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from tools import make_shortcut


def test_desktop_quote_escapes_backslash_quote_backtick_dollar() -> None:
    assert make_shortcut.desktop_quote('a"b') == '"a\\"b"'
    assert make_shortcut.desktop_quote('C:\\path') == '"C:\\\\path"'
    assert make_shortcut.desktop_quote('$HOME`cmd`') == '"\\$HOME\\`cmd\\`"'


def test_pythonw_falls_back_to_current_executable_when_absent(tmp_path, monkeypatch) -> None:
    fake_python = tmp_path / 'python.exe'
    fake_python.write_text('')
    monkeypatch.setattr(sys, 'executable', str(fake_python))
    assert make_shortcut.pythonw() == str(fake_python)


def test_pythonw_prefers_sibling_pythonw_when_present(tmp_path, monkeypatch) -> None:
    fake_python = tmp_path / 'python.exe'
    fake_python.write_text('')
    fake_pythonw = tmp_path / 'pythonw.exe'
    fake_pythonw.write_text('')
    monkeypatch.setattr(sys, 'executable', str(fake_python))
    assert make_shortcut.pythonw() == str(fake_pythonw)


def test_main_refuses_unsupported_platform(monkeypatch) -> None:
    monkeypatch.setattr(sys, 'platform', 'darwin')
    with pytest.raises(SystemExit):
        make_shortcut.main()


def test_desktop_entry_references_editor_and_icon() -> None:
    assert 'tools/editor.py' not in make_shortcut.DESKTOP_ENTRY  # template, filled at runtime
    assert '{exec_line}' in make_shortcut.DESKTOP_ENTRY
    assert '{icon}' in make_shortcut.DESKTOP_ENTRY
    assert 'mini_basic Editor' in make_shortcut.DESKTOP_ENTRY
