"""Run from a windowed editor must provide a console for terminal BASIC I/O."""
import sys
from unittest.mock import Mock, patch

import pytest

from tools.editor import EditorWindow

pytestmark = [pytest.mark.phase0]


def editor(path):
    app = Mock(path=str(path))
    app.pygame_var.get.return_value = False
    app.dialect_var.get.return_value = 'mits'
    app.wait_esc_var.get.return_value = False
    app.text.edit_modified.return_value = False
    app._build_run_command.side_effect = lambda p: EditorWindow._build_run_command(app, p)
    return app


def test_pythonw_terminal_run_selects_matching_console_python(tmp_path):
    console = tmp_path/'python.exe'
    console.touch()
    app = editor(tmp_path/'trek.bas')
    with patch('tools.editor.sys.executable', str(tmp_path/'pythonw.exe')):
        command = EditorWindow._build_run_command(app, app.path)
    assert command[0] == str(console)
    assert command[1:3] == ['-m', 'mini_basic']
    assert command[-3:] == ['--dialect', 'mits', '--no-hold']


def test_pygame_run_can_keep_windowed_python(tmp_path):
    app = editor(tmp_path/'trek.bas')
    app.pygame_var.get.return_value = True
    executable = str(tmp_path/'pythonw.exe')
    with patch('tools.editor.sys.executable', executable):
        command = EditorWindow._build_run_command(app, app.path)
    assert command[0] == executable
    assert '--pygame' in command


def test_missing_console_python_reports_run_error(tmp_path):
    app = editor(tmp_path/'trek.bas')
    with patch('tools.editor.sys.executable', str(tmp_path/'pythonw.exe')), \
            patch('tools.editor.messagebox.showerror') as error, \
            patch('tools.editor.subprocess.Popen') as launch:
        EditorWindow.run_program(app)
    launch.assert_not_called()
    assert 'python.exe' in error.call_args.args[1]


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows console launch')
def test_terminal_run_uses_console_and_keeps_program_directory(tmp_path):
    console = tmp_path/'python.exe'
    console.touch()
    app = editor(tmp_path/'trek.bas')
    with patch('tools.editor.sys.executable', str(tmp_path/'pythonw.exe')), \
            patch('tools.editor.subprocess.Popen') as launch:
        EditorWindow.run_program(app)
    assert launch.call_args.args[0][0] == str(console)
    assert launch.call_args.kwargs['cwd'] == str(tmp_path)
    assert launch.call_args.kwargs['creationflags'] != 0
