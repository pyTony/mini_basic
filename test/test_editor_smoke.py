"""Headless-safe smoke test for tools/editor.py.

No Tk mainloop is ever started. If a Tk root cannot even be created
(no display available), the test skips rather than failing.
"""
from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import ttk
from typing import List
from unittest import mock

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from tools.editor import (
    EditorWindow,
    _DIALECT_HINT_RE,
    _ICONS_DIR,
    _KEYWORD_RE,
    _PROC_RE,
    _STAR_CMD_RE,
    _set_window_icon,
    _strip_leading_line_number,
)


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


def test_strip_line_numbers_turns_goto_target_into_label() -> None:
    root = _make_root()
    try:
        win = EditorWindow(root)
        win.dialect_var.set('bbc')
        win.text.delete('1.0', tk.END)
        win.text.insert(
            '1.0',
            '10 PRINT "a"\n20 GOTO 40\n30 PRINT "skip"\n40 PRINT "b"\n',
        )

        win.strip_line_numbers()
        content = win.text.get('1.0', 'end-1c')

        assert '10' not in content
        assert '40' not in content
        assert 'GOTO L40' in content
        assert '(L40) PRINT' in content
    finally:
        root.destroy()


def test_strip_line_numbers_refuses_computed_goto() -> None:
    root = _make_root()
    try:
        win = EditorWindow(root)
        win.dialect_var.set('bbc')
        win.text.delete('1.0', tk.END)
        win.text.insert(
            '1.0',
            '10 DIM T%(1)\n20 T%(0)=40\n30 GOTO (T%(0))\n40 PRINT "b"\n',
        )
        original = win.text.get('1.0', 'end-1c')

        with mock.patch('tools.editor.messagebox.showerror') as mock_error:
            win.strip_line_numbers()
        mock_error.assert_called_once()
        assert 'calculated GOTO' in mock_error.call_args[0][1]
        # Refused: buffer must be untouched.
        assert win.text.get('1.0', 'end-1c') == original
    finally:
        root.destroy()


def test_reindent_keeps_line_numbers() -> None:
    root = _make_root()
    try:
        win = EditorWindow(root)
        win.text.delete('1.0', tk.END)
        win.text.insert('1.0', '10 FOR I=1 TO 3\n20 PRINT I\n30 NEXT I\n40 END\n')

        win.reindent()
        content = win.text.get('1.0', 'end-1c')

        assert '10' in content
        assert '20' in content
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


def test_icon_files_exist_for_both_platforms() -> None:
    assert os.path.isfile(os.path.join(_ICONS_DIR, 'mini_basic_editor.png'))
    assert os.path.isfile(os.path.join(_ICONS_DIR, 'mini_basic_editor.ico'))


def test_editor_window_sets_its_own_icon() -> None:
    """Replaces the platform-default Tk feather/icon with the editor's own."""
    root = _make_root()
    try:
        win = EditorWindow(root)
        if sys.platform == 'win32':
            assert win._icon_image is None  # iconbitmap path; nothing to keep alive
        else:
            assert isinstance(win._icon_image, tk.PhotoImage)
    finally:
        root.destroy()


def test_set_window_icon_survives_a_bad_icon_path(monkeypatch, tmp_path) -> None:
    """A missing/unreadable icon file must not crash window setup."""
    monkeypatch.setattr('tools.editor._ICONS_DIR', str(tmp_path))  # no icon files here
    root = _make_root()
    try:
        assert _set_window_icon(root) is None
    finally:
        root.destroy()


def test_run_dialog_offers_python_and_bbcsdl_launchers() -> None:
    """The toolbar's Run button opens a dialog with icon buttons, not a menu."""
    root = _make_root()
    try:
        win = EditorWindow(root)
        assert win.run_dialog is None

        win._open_run_dialog()

        assert win.run_dialog is not None and win.run_dialog.winfo_exists()
        labels = _collect_button_texts(win.run_dialog)
        assert any('Python' in label for label in labels)
        assert any('Real BBC BASIC' in label for label in labels)
    finally:
        root.destroy()


def test_run_dialog_reopen_reuses_existing_window() -> None:
    root = _make_root()
    try:
        win = EditorWindow(root)
        win._open_run_dialog()
        first = win.run_dialog
        win._open_run_dialog()
        assert win.run_dialog is first
    finally:
        root.destroy()


def _collect_button_texts(widget) -> List[str]:
    texts = []
    for child in widget.winfo_children():
        if isinstance(child, ttk.Button):
            texts.append(child.cget('text'))
        texts.extend(_collect_button_texts(child))
    return texts


def test_run_program_bbcsdl_requires_executable_configured() -> None:
    root = _make_root()
    try:
        win = EditorWindow(root)
        win.bbcsdl_executable_var.set('')
        with mock.patch('tools.editor.messagebox.showinfo'), \
             mock.patch('tools.editor.messagebox.showerror') as error, \
             mock.patch.object(win, 'save_file_as') as save_as:
            win.path = __file__  # already "saved"; skip the save-required path
            win.text.edit_modified(False)
            win.run_program_bbcsdl()
        save_as.assert_not_called()
        assert error.called
        assert 'executable' in error.call_args.args[1]
    finally:
        root.destroy()


def test_run_program_bbcsdl_requires_helper_configured(tmp_path) -> None:
    root = _make_root()
    try:
        win = EditorWindow(root)
        fake_exe = tmp_path / 'bbcsdl.exe'
        fake_exe.write_text('x')
        win.bbcsdl_executable_var.set(str(fake_exe))
        win.bbcsdl_helper_var.set('')
        win.path = __file__
        win.text.edit_modified(False)
        with mock.patch('tools.editor.messagebox.showerror') as error:
            win.run_program_bbcsdl()
        assert error.called
        assert 'basrun.bbc' in error.call_args.args[1]
    finally:
        root.destroy()


def test_run_program_bbcsdl_launches_configured_executable_and_helper(tmp_path) -> None:
    root = _make_root()
    try:
        win = EditorWindow(root)
        fake_exe = tmp_path / 'bbcsdl.exe'
        fake_exe.write_text('x')
        fake_helper = tmp_path / 'basrun.bbc'
        fake_helper.write_text('x')
        win.bbcsdl_executable_var.set(str(fake_exe))
        win.bbcsdl_helper_var.set(str(fake_helper))

        sample = tmp_path / 'demo.bas'
        sample.write_text('10 PRINT 1\n')
        win.path = str(sample)
        win.text.delete('1.0', tk.END)
        win.text.insert('1.0', '10 PRINT 1\n')
        win.text.edit_modified(False)

        with mock.patch('tools.editor.subprocess.Popen') as popen:
            win.run_program_bbcsdl()

        popen.assert_called_once()
        args, kwargs = popen.call_args
        assert args[0] == [str(fake_exe), str(fake_helper), str(sample)]
        assert kwargs['cwd'] == str(tmp_path)
    finally:
        root.destroy()


def test_browsing_bbcsdl_paths_persists_to_settings(tmp_path) -> None:
    """Chosen executable/helper paths are saved so they survive the next run."""
    root = _make_root()
    try:
        win = EditorWindow(root)
        chosen = str(tmp_path / 'bbcsdl.exe')
        with mock.patch('tools.editor._save_editor_settings_to_disk') as save_to_disk:
            win.bbcsdl_executable_var.set(chosen)
            win._save_bbcsdl_settings()
        assert win._editor_settings['bbcsdl_executable'] == chosen
        save_to_disk.assert_called_once_with(win._editor_settings)
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
        assert win._original_source_path == race_bbc
    finally:
        root.destroy()


def test_run_program_opened_tokenized_bbc_runs_original_file_without_save(tmp_path) -> None:
    """Opening a .bbc to run it, unmodified, must not force a Save As first.

    LOAD already auto-detects tokenized/text programs by content, so Run can
    replay the original file directly -- the untitled buffer is only an
    artifact of ``.bbc`` being reserved for tokenized Save/Save As output.
    """
    race_bbc = os.path.join(_ROOT, 'basics', 'RACE.BBC')
    if not os.path.exists(race_bbc):
        pytest.skip('basics/RACE.BBC fixture not present')

    root = _make_root()
    try:
        win = EditorWindow(root)
        with mock.patch('tools.editor.filedialog.askopenfilename', return_value=race_bbc):
            win.open_file()
        assert win.path is None
        assert win.text.edit_modified() is False

        with mock.patch('tools.editor.messagebox.showinfo') as info, \
             mock.patch.object(win, 'save_file_as') as save_as, \
             mock.patch('tools.editor.subprocess.Popen') as popen:
            win.run_program()

        info.assert_not_called()
        save_as.assert_not_called()
        popen.assert_called_once()
        args, kwargs = popen.call_args
        assert race_bbc in args[0]  # the original tokenized file, run as-is
        assert kwargs['cwd'] == os.path.dirname(race_bbc)
    finally:
        root.destroy()


def test_run_program_edited_tokenized_bbc_still_asks_to_save(tmp_path) -> None:
    """Once the detokenized buffer is actually edited, it no longer matches
    the original file, so Run must fall back to the normal save-as-.bas
    prompt instead of silently running the stale original."""
    race_bbc = os.path.join(_ROOT, 'basics', 'RACE.BBC')
    if not os.path.exists(race_bbc):
        pytest.skip('basics/RACE.BBC fixture not present')

    root = _make_root()
    try:
        win = EditorWindow(root)
        with mock.patch('tools.editor.filedialog.askopenfilename', return_value=race_bbc):
            win.open_file()
        win.text.insert(tk.END, "\n' edited\n")
        assert win.text.edit_modified() is True

        with mock.patch('tools.editor.messagebox.showinfo') as info, \
             mock.patch.object(win, 'save_file_as') as save_as:
            win.run_program()

        info.assert_called_once()
        save_as.assert_called_once()
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
