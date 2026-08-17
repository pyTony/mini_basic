# Register .bas as Mini-BASIC *source* (text), not as unsigned software.
# Default action is Edit (Notepad). Right-click -> Run with Mini-BASIC to execute.
# Downloads files with Mark of the Web no longer hit "publisher could not be verified"
# when a menu only wanted the listing text.
param(
    [string]$OpenCommand = ''
)

$ErrorActionPreference = 'Stop'
if (-not $OpenCommand) {
    $cmd = Join-Path $env:USERPROFILE 'bin\mini_basic.cmd'
    if (Test-Path $cmd) {
        $OpenCommand = "`"$cmd`" `"%1`""
    } else {
        $OpenCommand = 'cmd.exe /c python -m mini_basic "%1"'
    }
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
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\edit' -Name '(default)' -Value 'Edit with Notepad'
New-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\edit\command' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\edit\command' -Name '(default)' -Value 'notepad.exe "%1"'

New-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\open' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\open' -Name '(default)' -Value 'Run with Mini-BASIC'
New-Item -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\open\command' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Classes\MiniBasicProgram\shell\open\command' -Name '(default)' -Value $OpenCommand

Write-Host 'Registered .bas as Mini-BASIC source (Edit=Notepad). PerceivedType=text.'
