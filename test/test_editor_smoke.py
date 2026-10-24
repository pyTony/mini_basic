"""Headless-safe smoke test for tools/editor.py.

No Tk mainloop is ever started. If a Tk root cannot even be created
(no display available), the test skips rather than failing.
"""
from __future__ import annotations

import time
import os
import sys
import tkinter as tk
from unittest import mock

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from tools.editor import (
    EditorWindow,
    _DIALECT_HINT_RE,
    _KEYWORD_RE,
    _PROC_RE,
    _STAR_CMD_RE,
    _strip_leading_line_number,
)


def _make_root() -> tk.Tk:
    # Tcl start-up can fail transiently on Windows (init.tcl briefly locked by a
    # scanner), so retry a few times before concluding there is no display.
    root = None
    for attempt in range(20):
        try:
            root = tk.Tk()
            break
        except tk.TclError as exc:
            if attempt == 19:
                pytest.skip(f'no display available for Tk: {exc}')
            time.sleep(0.5)
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


def test_build_run_command_wait_for_esc_toggle(tmp_path) -> None:
    root = _make_root()
    try:
        win = EditorWindow(root)

        assert win.wait_esc_var.get() is False
        assert '--no-hold' in win._build_run_command(str(tmp_path / 'demo.bas'))

        win.wait_esc_var.set(True)
        cmd = win._build_run_command(str(tmp_path / 'demo.bas'))
        assert '--hold' in cmd
        assert '--no-hold' not in cmd
    finally:
        root.destroy()


def test_open_tokenized_bbc_detokenizes_into_editable_text(tmp_path) -> None:
    """Reuses the interpreter's own LOAD/LIST, same as basics/RACE.BBC et al."""
    from mini_basic.bbc_detokenize import parse_wilson_program

    assert parse_wilson_program  # module importable; real binary fixtures live under basics/
    race_bbc = os.path.join(_ROOT, 'basics', 'RACE.BBC')
    if not os.path.exists(race_bbc):
        pytest.skip('basics/RACE.BBC fixture not present')

    root = _make_root()
    try:
        win = EditorWindow(root)
        with mock.patch('tools.editor.filedialog.askopenfilename', return_value=race_bbc):
            win.open_file()
        content = win.text.get('1.0', 'end-1c')
        assert '   100 A = 0: B = 0' in content
        assert win.path is None  # untitled: Save As targets a new .bas file
    finally:
        root.destroy()


def test_open_tokenized_bbc_reports_error_for_bad_path(tmp_path) -> None:
    root = _make_root()
    try:
        win = EditorWindow(root)
        missing = str(tmp_path / 'missing.bbc')
        with mock.patch('tools.editor.filedialog.askopenfilename', return_value=missing), \
             mock.patch('tools.editor.messagebox.showerror') as mock_error:
            win.open_file()
        assert mock_error.called
    finally:
        root.destroy()


def test_strip_leading_line_number() -> None:
    assert _strip_leading_line_number('10 PRINT "hi"') == 'PRINT "hi"'
    assert _strip_leading_line_number('PRINT "hi"') == 'PRINT "hi"'
    assert _strip_leading_line_number('  20   GOTO 10') == 'GOTO 10'


def test_listener_eval_line_at_cursor_runs_immediately_no_line_number() -> None:
    root = _make_root()
    try:
        win = EditorWindow(root)
        win.text.delete('1.0', tk.END)
        win.text.insert('1.0', 'PRINT 1 + 2\n')
        win.text.mark_set('insert', '1.0')

        win.eval_line_at_cursor()

        output = win.listener_output.get('1.0', 'end-1c')
        assert '> PRINT 1 + 2' in output
        assert '3' in output
    finally:
        root.destroy()


def test_listener_eval_selection_defines_and_runs_a_proc_without_auto() -> None:
    """A whole DEF PROC...ENDPROC block, selected and sent at once, is stored
    directly (no AUTO, no line numbers typed) and is then callable."""
    root = _make_root()
    try:
        win = EditorWindow(root)
        win.text.delete('1.0', tk.END)
        win.text.insert(
            '1.0', 'DEF PROCgreet(n$)\nPRINT "hi " + n$\nENDPROC\n',
        )
        win.text.tag_add('sel', '1.0', '3.end')

        win.eval_selection()
        output = win.listener_output.get('1.0', 'end-1c')
        assert 'DEF PROC defined.' in output

        win.listener_entry.insert(0, 'PROCgreet("Tony")')
        win._listener_submit()
        output = win.listener_output.get('1.0', 'end-1c')
        assert 'hi Tony' in output
    finally:
        root.destroy()


def test_listener_blocks_auto_and_bare_edit() -> None:
    root = _make_root()
    try:
        win = EditorWindow(root)
        win.listener_entry.insert(0, 'AUTO')
        win._listener_submit()
        output = win.listener_output.get('1.0', 'end-1c')
        assert 'not available here' in output
    finally:
        root.destroy()


def test_closing_with_a_pending_highlight_job_does_not_raise() -> None:
    """Edit, then close immediately (before the 200ms highlight debounce
    fires) — _on_close must cancel the pending job rather than let it hit
    a destroyed widget.
    """
    root = _make_root()
    win = EditorWindow(root)
    win.text.insert('1.0', '10 PRINT 1\n')
    win.text.event_generate('<<Modified>>')
    assert win._highlight_job is not None

    win._on_close()  # must not raise, and must leave no job to fire later

    assert win._highlight_job is None


@pytest.fixture
def file_editor():
    root = _make_root()
    win = EditorWindow(root)
    yield win
    win._on_close()


@pytest.mark.parametrize('entry', ['open', 'startup'])
def test_regular_open_decodes_sieve_bbc(file_editor, tmp_path, entry):
    from pathlib import Path
    source = Path(_ROOT)/'examples'/'SIEVE.bbc'
    target = tmp_path/'sieve.BBC'
    target.write_bytes(source.read_bytes())
    original = target.read_bytes()
    if entry == 'open':
        with mock.patch('tools.editor.filedialog.askopenfilename', return_value=str(target)):
            file_editor.open_file()
    else:
        file_editor._load_file(str(target))
    content = file_editor.text.get('1.0', 'end-1c')
    assert 'DIM FLAGS(8191)' in content
    assert 'FOR I = 0 TO SIZE' in content
    assert '\ufffd' not in content
    assert file_editor.path is None
    assert target.read_bytes() == original


def test_file_menu_has_no_separate_tokenized_open(file_editor):
    menu = file_editor.root.nametowidget(file_editor.root['menu'])
    index = next(i for i in range(menu.index('end')+1)
                 if menu.type(i) == 'cascade' and menu.entrycget(i, 'label') == 'File')
    file_menu = file_editor.root.nametowidget(menu.entrycget(index, 'menu'))
    labels = [file_menu.entrycget(i, 'label') for i in range(file_menu.index('end')+1)
              if file_menu.type(i) != 'separator']
    assert not any('Tokenized' in label for label in labels)


@pytest.mark.parametrize('existing', [False, True])
def test_editor_rejects_bbc_save_without_changing_state(file_editor, tmp_path, existing):
    target = tmp_path/'target.bBc'
    if existing:
        target.write_bytes(b'original tokenized bytes')
    old_path = str(tmp_path/'working.bas')
    file_editor.path = old_path
    file_editor.text.insert('1.0', 'PRINT 42')
    file_editor.text.edit_modified(True)
    with mock.patch('tools.editor.filedialog.asksaveasfilename', return_value=str(target)), \
            mock.patch('tools.editor.messagebox.showerror') as error:
        file_editor.save_file_as()
    assert error.called
    assert '.bbc is reserved for tokenized programs' in error.call_args.args[1]
    assert '.bas' in error.call_args.args[1]
    assert file_editor.path == old_path
    assert file_editor.text.edit_modified()
    assert target.read_bytes() == b'original tokenized bytes' if existing else not target.exists()


def test_editor_plain_save_also_rejects_bbc(file_editor, tmp_path):
    target = tmp_path/'existing.BBC'
    target.write_bytes(b'original tokenized bytes')
    file_editor.path = str(target)
    file_editor.text.insert('1.0', 'PRINT 42')
    with mock.patch('tools.editor.messagebox.showerror') as error:
        file_editor.save_file()
    assert error.called
    assert target.read_bytes() == b'original tokenized bytes'
