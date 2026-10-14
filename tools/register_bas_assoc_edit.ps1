<<<<<<< HEAD
# register_bas_assoc.ps1
# Associate .bas files with miniBASIC editor.py and add context-menu entry
# Run as Administrator (right-click → Run with PowerShell as admin)

# ---- CONFIGURE THESE TWO PATHS ----
$EditorScript = "C:\Users\admin\mini_basic\tools\editor.py"   # full path to editor.py
$PythonExe    = "pythonw.exe"   # or full path e.g. "C:\Python312\pythonw.exe"
# -----------------------------------

# Resolve pythonw if only the name is given
if (-not [System.IO.Path]::IsPathRooted($PythonExe)) {
    $PythonExe = (Get-Command $PythonExe -ErrorAction Stop).Source
}

$ProgId = "miniBASIC.Editor"
$MenuText = "Avaa miniBASIC Editorilla"   # Finnish; change if you prefer English
=======
# Register .bas as Mini-BASIC source: double-click opens the mini_basic
# tkinter editor (tools/editor.py); context menu also offers Start Mini-BASIC
# (run) and Edit as Text (Notepad) as secondary verbs.
param(
    [string]$EditorCommand = '',
    [string]$RunCommand = ''
)

$ErrorActionPreference = 'Stop'

if (-not $RunCommand) {
    $pipExe = Get-Command mini-basic -ErrorAction SilentlyContinue
    if ($pipExe) {
        $RunCommand = "`"$($pipExe.Source)`" `"%1`""
    } else {
        $RunCommand = 'cmd.exe /k python -m mini_basic "%1"'
    }
}

if (-not $EditorCommand) {
    # tools/editor.py lives next to this script in the repo checkout; it is
    # not packaged/installed by pip (see pyproject.toml), so there is no
    # console-script entry point to look up the way $RunCommand does above.
    $editorScript = Join-Path $PSScriptRoot 'editor.py'
    if (-not (Test-Path $editorScript)) {
        throw "Could not find tools/editor.py next to this script ($PSScriptRoot). Pass -EditorCommand explicitly."
    }
    # Prefer pythonw.exe so opening a file doesn't also pop a console window.
    $pyw = Get-Command pythonw -ErrorAction SilentlyContinue
    $pyExe = if ($pyw) { $pyw.Source } else { 'python' }
    $EditorCommand = "`"$pyExe`" `"$editorScript`" `"%1`""
}

$pol = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\Associations'
try {
    New-Item -Path $pol -Force -ErrorAction Stop | Out-Null
    $cur = ''
    try { $cur = [string](Get-ItemProperty -Path $pol -Name LowRiskFileTypes -ErrorAction Stop).LowRiskFileTypes } catch { }
    $parts = @($cur -split ';' | ForEach-Object { $_.Trim().ToLowerInvariant() } | Where-Object { $_ })
    foreach ($ext in @('.bas', '.bbc')) {
        if ($parts -notcontains $ext) { $parts += $ext }
    }
    Set-ItemProperty -Path $pol -Name LowRiskFileTypes -Value (($parts -join ';') + ';')
} catch {
    Write-Host 'Note: could not set LowRiskFileTypes (policy key denied).'
}
>>>>>>> fc79396ed8adbf765de61fd02cda684aa261e8ed

Write-Host "Registering .bas association..."
Write-Host "  Editor : $EditorScript"
Write-Host "  Python : $PythonExe"

# 1. Create the ProgID
New-Item -Path "HKCU:\Software\Classes\$ProgId" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\$ProgId" -Name "(Default)" -Value "miniBASIC Source File"

<<<<<<< HEAD
# Icon (optional – uses the python icon)
New-Item -Path "HKCU:\Software\Classes\$ProgId\DefaultIcon" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\$ProgId\DefaultIcon" -Name "(Default)" -Value "$PythonExe,0"

# 2. Open command (double-click)
$OpenCmd = "`"$PythonExe`" `"$EditorScript`" `"%1`""
New-Item -Path "HKCU:\Software\Classes\$ProgId\shell\open\command" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\$ProgId\shell\open\command" -Name "(Default)" -Value $OpenCmd

# 3. Context-menu entry (appears alongside "Muokkaa muistiossa")
New-Item -Path "HKCU:\Software\Classes\$ProgId\shell\edit" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\$ProgId\shell\edit" -Name "(Default)" -Value $MenuText
New-Item -Path "HKCU:\Software\Classes\$ProgId\shell\edit\command" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\$ProgId\shell\edit\command" -Name "(Default)" -Value $OpenCmd

# 4. Link the .bas extension to our ProgID
New-Item -Path "HKCU:\Software\Classes\.bas" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\.bas" -Name "(Default)" -Value $ProgId

# Also register uppercase .BAS (some tools create it that way)
New-Item -Path "HKCU:\Software\Classes\.BAS" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\.BAS" -Name "(Default)" -Value $ProgId

# 5. Tell Explorer to refresh
$signature = @'
[DllImport("shell32.dll")]
public static extern void SHChangeNotify(int eventId, int flags, IntPtr item1, IntPtr item2);
'@
$type = Add-Type -MemberDefinition $signature -Name ShellNotify -Namespace WinAPI -PassThru
$type::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)   # SHCNE_ASSOCCHANGED

Write-Host ""
Write-Host "Done. .bas files now open with the miniBASIC editor."
Write-Host "Right-click a .bas file → you should see '$MenuText' next to 'Muokkaa muistiossa'."
Write-Host ""
Write-Host "If the menu does not appear immediately, log off/on or restart Explorer."
=======
New-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell' -Name '(default)' -Value 'open'

# Clear out any verbs from a previous run of this script before re-adding
# them, so stale commands never linger (e.g. an old editor path).
foreach ($verb in @('open', 'edit', 'run', 'notepad')) {
    Remove-Item -Path "HKCU:\Software\Classes\MiniBasicProgram\shell\$verb" -Recurse -Force -ErrorAction SilentlyContinue
}

# "open" is the default verb (double-click): launch the mini_basic editor.
New-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\open' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\open' -Name '(default)' -Value 'Edit with Mini-BASIC Editor'
New-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\open\command' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\open\command' -Name '(default)' -Value $EditorCommand

# "run" is a secondary context-menu verb: run the program directly.
New-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\run' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\run' -Name '(default)' -Value 'Start Mini-BASIC'
New-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\run\command' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\run\command' -Name '(default)' -Value $RunCommand

# "notepad" is a secondary context-menu verb: plain-text viewing/editing,
# now that the default "open" verb launches the mini_basic editor instead.
New-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\notepad' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\notepad' -Name '(default)' -Value 'Edit as Text (Notepad)'
New-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\notepad\command' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\notepad\command' -Name '(default)' -Value 'notepad.exe "%1"'

Write-Host 'Registered .bas: double-click opens the Mini-BASIC Editor; right-click offers Start Mini-BASIC and Edit as Text (Notepad).'
>>>>>>> fc79396ed8adbf765de61fd02cda684aa261e8ed
