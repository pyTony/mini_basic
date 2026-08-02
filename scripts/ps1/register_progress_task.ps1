# Register a Windows scheduled task: poll status source .txt files.
# Rebuilds status.html only when sources change (or rare agent-staleness flag).
# Default interval: every 5 minutes (was every 1 minute full rewrite).
# Each run exits immediately — no process left open.
# Run once:  powershell -File register_progress_task.ps1
# Remove:    schtasks /delete /tn mini_basic_progress /f

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
# progress_heartbeat.py lives in scripts/, this file is scripts/ps1/
$Script = Join-Path (Split-Path -Parent $Root) 'progress_heartbeat.py'

function Test-RealPythonPath {
    param([string]$Path)
    if (-not $Path) { return $false }
    if ($Path -notmatch '\\pythonw?\.exe$') { return $false }
    if ($Path -like '*\WindowsApps\*') { return $false }
    return Test-Path $Path
}

function Resolve-Pythonw {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Python\bin\pythonw.exe'),
        (Join-Path $env:ProgramFiles 'Python312\pythonw.exe'),
        (Join-Path $env:ProgramFiles 'Python313\pythonw.exe'),
        (Join-Path $env:ProgramFiles 'Python314\pythonw.exe')
    )

    try {
        $pyList = & py -0p 2>$null
        foreach ($line in $pyList) {
            if ($line -match ':\s+(.+\\python\.exe)\s*$') {
                $pyExe = $Matches[1].Trim()
                if ($pyExe -notlike '*\WindowsApps\*') {
                    $candidates += (Join-Path (Split-Path $pyExe -Parent) 'pythonw.exe')
                }
            }
        }
    } catch {}

    foreach ($cmd in @('pythonw', 'python')) {
        $found = Get-Command $cmd -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
        if (Test-RealPythonPath (Join-Path (Split-Path $found -Parent) 'pythonw.exe')) {
            $candidates += (Join-Path (Split-Path $found -Parent) 'pythonw.exe')
        }
    }

    foreach ($candidate in $candidates | Select-Object -Unique) {
        if (Test-RealPythonPath $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    throw 'Could not find pythonw.exe outside WindowsApps.'
}

$Pythonw = Resolve-Pythonw
if ($Pythonw -like '*\WindowsApps\*') {
    throw "Refusing WindowsApps python: $Pythonw"
}

schtasks /delete /tn 'mini_basic_progress' /f 2>$null | Out-Null

# Quiet: no console spam under pythonw. Poll interval 5 minutes.
$arg = "`"$Pythonw`" `"$Script`" --quiet"
$result = schtasks /create /tn 'mini_basic_progress' /tr $arg /sc minute /mo 5 /f 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error $result
    exit 1
}

# Run on battery and catch up after sleep (default schtasks blocks on battery).
$task = Get-ScheduledTask -TaskName 'mini_basic_progress' -ErrorAction SilentlyContinue
if ($task) {
    $settings = $task.Settings
    $settings.AllowStartIfOnBatteries = $true
    $settings.StopIfGoingOnBatteries = $false
    $settings.StartWhenAvailable = $true
    $settings.DisallowStartIfOnBatteries = $false
    Set-ScheduledTask -TaskName 'mini_basic_progress' -Settings $settings | Out-Null
}

Write-Host "Registered: mini_basic_progress (every 5 min poll; rebuild only on .txt change)"
Write-Host "Pythonw:    $Pythonw"
Write-Host "Script:     $Script"
Write-Host "Stale agent check: every ~30 min if sources unchanged (see utils/status_sources.py)"
Write-Host "Tablet:     PHONE_PROGRESS.txt, status.html, SYNC_STAMP.txt"