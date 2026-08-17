# Register .bas as Mini-BASIC source (text). Default = Notepad.
# Context menu "Start Mini-BASIC" runs python -m mini_basic (not ShellExecute Open,
# which showed the publisher warning and did not start the interpreter).
param(
    [string]$OpenCommand = ''
)

$ErrorActionPreference = 'Stop'
if (-not $OpenCommand) {
    $cmd = Join-Path $env:USERPROFILE 'bin\mini_basic.cmd'
    if (Test-Path $cmd) {
        $OpenCommand = "`"$cmd`" `"%1`""
    } else {
        $OpenCommand = 'cmd.exe /k python -m mini_basic "%1"'
    }
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
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell' -Name '(default)' -Value 'edit'

New-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\edit' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\edit' -Name '(default)' -Value 'Open in Notepad'
New-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\edit\command' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\edit\command' -Name '(default)' -Value 'notepad.exe "%1"'

Remove-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\open' -Recurse -Force -ErrorAction SilentlyContinue
New-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\run' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\run' -Name '(default)' -Value 'Start Mini-BASIC'
New-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\run\command' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\run\command' -Name '(default)' -Value $OpenCommand

Write-Host 'Registered .bas as source. Default=Notepad. Menu: Start Mini-BASIC.'
