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

New-Item -Path 'HKCU:\Software\Classes\.bas' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\.bas' -Name '(default)' -Value 'MiniBasicProgram'
New-ItemProperty -Path 'HKCU:\Software\Classes\.bas' -Name 'PerceivedType' -Value 'text' -PropertyType String -Force | Out-Null
New-ItemProperty -Path 'HKCU:\Software\Classes\.bas' -Name 'Content Type' -Value 'text/plain' -PropertyType String -Force | Out-Null

New-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram' -Name '(default)' -Value 'Mini-BASIC source'

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
