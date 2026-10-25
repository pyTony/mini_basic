"""Put a "mini_basic Editor" launcher with its own icon on the desktop.

    python tools/make_shortcut.py

Windows: a desktop shortcut that starts tools/editor.py with pythonw.exe (no
console window). Windows PowerShell writes it, so pywin32 is not needed.

Linux: a mini-basic-editor.desktop launcher in ~/.local/share/applications,
so the editor shows up in the applications menu and the dock with its icon,
plus a copy on the desktop. It starts the editor with the Python that ran
this script, so run it with your venv's python if you use one.

Either way it works from any folder. Same approach as lispy3's own
icons/make_shortcut.py; macOS has no automated path here.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
ICONS = os.path.join(HERE, "icons")

# Paths go to PowerShell as environment variables, so spaces and quotes in
# them need no escaping.
POWERSHELL = r"""
$desktop = [Environment]::GetFolderPath('Desktop')
$link = Join-Path $desktop 'mini_basic Editor.lnk'
$s = (New-Object -ComObject WScript.Shell).CreateShortcut($link)
$s.TargetPath = $env:MINI_BASIC_PYTHONW
$s.Arguments = '"' + $env:MINI_BASIC_SCRIPT + '"'
$s.WorkingDirectory = $env:MINI_BASIC_DIR
$s.IconLocation = $env:MINI_BASIC_ICON + ',0'
$s.Description = 'mini_basic BASIC source editor'
$s.Save()
Write-Output $link
"""


def pythonw():
    """pythonw.exe next to the running Python, or that Python itself."""
    folder, exe = os.path.split(sys.executable)
    candidate = os.path.join(folder, exe.lower().replace("python.exe", "pythonw.exe"))
    return candidate if os.path.exists(candidate) else sys.executable


def windows():
    env = dict(os.environ,
               MINI_BASIC_PYTHONW=pythonw(),
               MINI_BASIC_SCRIPT=os.path.join(HERE, "editor.py"),
               MINI_BASIC_DIR=REPO,
               MINI_BASIC_ICON=os.path.join(ICONS, "mini_basic_editor.ico"))
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", POWERSHELL],
        env=env, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit("Could not create the shortcut:\n" + result.stderr)
    print("Shortcut created:", result.stdout.strip())


DESKTOP_ENTRY = """[Desktop Entry]
Type=Application
Name=mini_basic Editor
Comment=Source editor for mini_basic BASIC programs
Exec={exec_line}
Path={repo}
Icon={icon}
Terminal=false
Categories=Development;IDE;
StartupWMClass=MiniBasicEditor
"""


def desktop_quote(arg):
    """Quote one Exec= argument as the Desktop Entry spec asks."""
    for ch in '\\"`$':
        arg = arg.replace(ch, "\\" + ch)
    return '"' + arg + '"'


def desktop_folder():
    """The user's desktop folder (it has a local name in some languages), or None."""
    try:
        folder = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True,
                                text=True).stdout.strip()
    except OSError:
        folder = ""
    folder = folder or os.path.expanduser("~/Desktop")
    home = os.path.expanduser("~").rstrip("/")
    return folder if os.path.isdir(folder) and folder.rstrip("/") != home else None


def linux():
    script = os.path.join(HERE, "editor.py")
    entry = DESKTOP_ENTRY.format(
        exec_line=" ".join(desktop_quote(a) for a in (sys.executable, script)) + " %F",
        repo=REPO, icon=os.path.join(ICONS, "mini_basic_editor.png"))
    apps = os.path.join(os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share"),
                        "applications")
    targets = [os.path.join(apps, "mini-basic-editor.desktop")]
    desktop = desktop_folder()
    if desktop:
        targets.append(os.path.join(desktop, "mini-basic-editor.desktop"))
    for path in targets:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(entry)
        os.chmod(path, 0o755)
        print("Launcher created:", path)
    if desktop:
        # GNOME runs a desktop launcher only once it is marked trusted.
        try:
            subprocess.run(["gio", "set", targets[-1], "metadata::trusted", "true"],
                           capture_output=True)
        except OSError:
            pass


def main():
    if sys.platform == "win32":
        windows()
    elif sys.platform.startswith("linux"):
        linux()
    else:
        sys.exit("Launchers are made this way only on Windows and Linux.")


if __name__ == "__main__":
    main()
