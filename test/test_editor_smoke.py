"""Headless-safe smoke test for tools/editor.py.

No Tk mainloop is ever started. If a Tk root cannot even be created
(no display available), the test skips rather than failing.
"""
from __future__ import annotations

import os
import sys
import tkinter as tk

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from tools.editor import EditorWindow, _DIALECT_HINT_RE, _KEYWORD_RE, _PROC_RE, _STAR_CMD_RE


def _make_root() -> tk.Tk:
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f'no display available for Tk: {exc}')
    root.withdraw()
    return root


def test_highlight_patterns_match_expected_tokens() -> None:
    assert _KEYWORD_RE.search('PRINT "hi"')
    assert _KEYWORD_RE.search('print "hi"')  # case-insensitive
    assert _PROC_RE.search('DEF PROCgreet')
    assert _PROC_RE.search('ENDPROC')
    assert _STAR_CMD_RE.search('*PLAY "tune.wav"')
    assert _DIALECT_HINT_RE.match('1 REM dialect: bbc')


def test_editor_loads_and_highlights_without_mainloop(tmp_path) -> None:
    root = _make_root()
    try:
        sample = tmp_path / 'demo.bas'
        sample.write_text('10 REM dialect: bbc\n20 PRINT "hi"\n30 DEF PROCgreet\n40 ENDPROC\n')

        win = EditorWindow(root, str(sample))
        content = win.text.get('1.0', 'end-1c')
        assert 'PROCgreet' in content

        # Highlighting ran on load; a keyword tag should cover some text.
        ranges = win.text.tag_ranges('keyword')
        assert ranges, 'expected at least one keyword-tagged range'
    finally:
        root.destroy()


def test_pretty_no_numbers_strips_line_numbers_and_indents() -> None:
    root = _make_root()
    try:
        win = EditorWindow(root)
        win.text.delete('1.0', tk.END)
        win.text.insert('1.0', '10 FOR I=1 TO 3\n20 PRINT I\n30 NEXT I\n40 END\n')

        win.pretty_no_numbers()
        content = win.text.get('1.0', 'end-1c')

        assert '10' not in content
        assert 'FOR I = 1 TO 3' in content
        assert '    PRINT I' in content
    finally:
        root.destroy()


def test_renumber_fixes_up_goto_targets() -> None:
    root = _make_root()
    try:
        win = EditorWindow(root)
        win.text.delete('1.0', tk.END)
        win.text.insert('1.0', '10 PRINT 1\n50 GOTO 999\n999 PRINT 2\n')

        win.renumber()
        content = win.text.get('1.0', 'end-1c')

        assert '    10 PRINT 1' in content
        assert '    20 GOTO 30' in content
        assert '    30 PRINT 2' in content
    finally:
        root.destroy()


def test_build_run_command_defaults_and_overrides(tmp_path) -> None:
    root = _make_root()
    try:
        win = EditorWindow(root)
        win.dialect_var.set('bbc')
        win.pygame_var.set(True)

        cmd = win._build_run_command(str(tmp_path / 'demo.bas'))

        assert cmd[0] == sys.executable
        assert cmd[1:3] == ['-m', 'mini_basic']
        assert '--dialect' in cmd and 'bbc' in cmd
        assert '--pygame' in cmd
    finally:
        root.destroy()
