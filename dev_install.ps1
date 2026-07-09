# dev_install.ps1 - Text-based development installation for mini_basic
# Modeled exactly on the end-user install.ps1 for consistency.
#
# Usage (pure PS, like end-user):
#   Drop this + core mini_basic_text_part0*.txt + mini_basic_dev_text_part*.txt (+ README, DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md) into a folder.
#   .\dev_install.ps1
#
# The dev text parts (generated from the extras we copied: status files, pipeline doc, examples, test, scripts, lib, utils, etc.)
# are reconstructed on top of the core end-user tree.
# This ensures the full dev package includes the status implementation, pipeline docs, and all agent/LLM context files.
#
# This produces a FULL DEVELOPMENT tree containing:
# - All end-user / core files (reconstructed from the 3 core text parts)
# - Dev extras (the files previously copied for LLM/agent context + status pipeline):
#   * examples/ (full)
#   * test/ (full harness + corpus + probes)
#   * scripts/ (full, including heartbeat, ps1 scheduled helpers, compare, verify)
#   * lib/ (BBC libraries + fonts)
#   * utils/ (status_updater, user_approval, agent_resource, etc.)
#   * All status / agent / tracking files: AGENT_*.txt, CURRENT_TASK.txt, STATUS.txt,
#     PROGRESS.txt, WORK_LOG.txt, CORPUS_AUDIT.txt, COMPARE_REPORT.txt, DEBUG_STEP.txt,
#     FEATURES_DONE.txt, FOLLOW_PROGRESS.txt, RESOURCE_CHECK.txt, USER_APPROVAL*.txt etc.
#   * Full documentation/ (feature matrices, etc.)
#
# Options:
#   -UsePythonBuilder   : Prefer python tools/reconstruct_from_text.py (robust, if Python present)
#   -TargetDir "path"
#   -SkipReconstruct
#   -Uninstall
#
# The Python builder option allows using the same archive format but with better parsing
# and future extensions for dev-only files.
#
# After install:
#   cd mini_basic
#   python -m unittest discover -s test -p "test_*.py" -q   # or run_regression.py
#   python scripts/verify_resources.py
#   powershell -File scripts/ps1/register_progress_task.ps1   # for autonomous heartbeat
#   # Then follow DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md for agent/LLM work.

param(
    [string]$TargetDir = "",
    [switch]$Uninstall,
    [switch]$SkipReconstruct,
    [switch]$UsePythonBuilder,
    [switch]$SkipGit
)

$ErrorActionPreference = 'Stop'

function Get-ScriptDir {
    if ($PSScriptRoot) { return $PSScriptRoot }
    if ($MyInvocation.MyCommand.Path) { return Split-Path -Parent $MyInvocation.MyCommand.Path }
    return (Get-Location).Path
}

$here = Get-ScriptDir

if ($Uninstall) {
    Write-Host "=== mini_basic DEV uninstall ===" -ForegroundColor Cyan
    $target = [Environment]::GetEnvironmentVariable('MINIBASIC_DIR', 'User')
    if (-not $target) { $target = Join-Path $here "mini_basic_dev" }
    $target = [System.IO.Path]::GetFullPath($target)
    if (Test-Path $target) { Remove-Item -Path $target -Recurse -Force -ErrorAction SilentlyContinue }
    # Also clean launchers if present
    $binDir = Join-Path $env:USERPROFILE "bin"
    foreach ($name in @("mini_basic.ps1","minibasic.ps1","mini_basic.cmd","minibasic.cmd")) {
        $f = Join-Path $binDir $name
        if (Test-Path $f) { Remove-Item $f -Force -ErrorAction SilentlyContinue }
    }
    [Environment]::SetEnvironmentVariable('MINIBASIC_DIR', $null, 'User')
    Write-Host "Dev uninstall complete."
    return
}

Write-Host "=== mini_basic DEVELOPMENT setup ===" -ForegroundColor Cyan
Write-Host "This includes core + dev extras (examples, test, scripts, lib, utils, full status pipeline, agent files, etc.)"

# Locate parts: core first, then dev extras (dev_text_part*.txt or in archives/dist)
$searchDirs = @(
    (Join-Path $here "archives"),
    (Join-Path $here "dist"),
    $here
)

$coreParts = @()
$devParts = @()
foreach ($d in $searchDirs) {
    $p1 = Join-Path $d "mini_basic_text_part01.txt"
    if (Test-Path $p1) {
        $coreParts = @(
            (Join-Path $d "mini_basic_text_part01.txt"),
            (Join-Path $d "mini_basic_text_part02.txt"),
            (Join-Path $d "mini_basic_text_part03.txt")
        ) | Where-Object { Test-Path $_ }
        break
    }
}

foreach ($d in $searchDirs) {
    $dev = Get-ChildItem -Path $d -Filter "mini_basic_dev_text_part*.txt" -ErrorAction SilentlyContinue | Sort-Object Name
    if ($dev) { $devParts = $dev.FullName; break }
}
if (-not $devParts) {
    # fallback
    foreach ($d in $searchDirs) {
        $dev = Get-ChildItem -Path $d -Filter "dev_text_part*.txt" -ErrorAction SilentlyContinue | Sort-Object Name
        if ($dev) { $devParts = $dev.FullName; break }
    }
}

if (-not $coreParts -or $coreParts.Count -eq 0) {
    Write-Warning "Core text parts not found. Will try to proceed with dev parts only or Python builder."
}

if (-not $TargetDir) {
    $TargetDir = Join-Path $here "mini_basic_dev"
}
$TargetDir = [System.IO.Path]::GetFullPath($TargetDir)
Write-Host "Target dev tree: $TargetDir"

if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Reconstruct-FromParts {
    param([string[]]$PartFiles, [string]$OutDir)
    if (-not $PartFiles -or $PartFiles.Count -eq 0) { return 0 }

    $allText = ""
    foreach ($pf in $PartFiles) {
        if (Test-Path $pf) { $allText += "`n" + [System.IO.File]::ReadAllText($pf) }
    }

    $BEGIN_RE = '^=====+\s*BEGIN FILE:\s*(.+?)\s*=+\s*$'
    $END_RE   = '^=====+\s*END FILE\s*=+\s*$'
    $ESC_PREFIX = 'ARCHIVE-MARKER-ESCAPED: '

    $lines = $allText -split "`r?`n"
    $currentPath = $null
    $current = New-Object System.Collections.Generic.List[string]
    $count = 0

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match $BEGIN_RE) {
            $currentPath = $Matches[1].Trim()
            if ($currentPath -match '[\{\}\$]' -or $currentPath -eq 'relative/path.py' -or -not ($currentPath -match '[/\\.]')) {
                $currentPath = $null; continue
            }
            $current.Clear()
            continue
        }
        if ($currentPath -ne $null -and ($line.Trim() -match $END_RE)) {
            $raw = ($current -join "`n")
            $unesc = $raw -split "`n" | ForEach-Object { if ($_.StartsWith($ESC_PREFIX)) { $_.Substring($ESC_PREFIX.Length) } else { $_ } }
            $content = ($unesc -join "`n") -replace '^\uFEFF', ''
            if ($content -and -not $content.EndsWith("`n")) { $content += "`n" }
            $outPath = Join-Path $OutDir $currentPath
            $parent = Split-Path -Parent $outPath
            if ($parent -and -not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
            [System.IO.File]::WriteAllText($outPath, $content, $utf8NoBom)
            $count++
            $currentPath = $null
            $current.Clear()
            continue
        }
        if ($currentPath -ne $null) { $current.Add($line) }
    }
    if ($currentPath -ne $null -and $current.Count -gt 0) {
        # trailing
        $raw = ($current -join "`n")
        $unesc = $raw -split "`n" | ForEach-Object { if ($_.StartsWith($ESC_PREFIX)) { $_.Substring($ESC_PREFIX.Length) } else { $_ } }
        $content = ($unesc -join "`n") -replace '^\uFEFF', ''
        $outPath = Join-Path $OutDir $currentPath
        $parent = Split-Path -Parent $outPath
        if ($parent -and -not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
        [System.IO.File]::WriteAllText($outPath, $content, $utf8NoBom)
        $count++
    }
    return $count
}

if (-not $SkipReconstruct) {
    Write-Host "Reconstructing dev tree..."

    $usePython = $false
    if ($UsePythonBuilder) {
        $py = Get-Command python -ErrorAction SilentlyContinue
        if ($py) { $usePython = $true }
    }

    if ($usePython -and (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host "Using Python builder (tools/reconstruct_from_text.py) ..."
        $allParts = @()
        if ($coreParts) { $allParts += $coreParts }
        if ($devParts) { $allParts += $devParts }
        $partsArg = ($allParts | ForEach-Object { "`"$_`"" }) -join ' '
        $cmd = "python tools/reconstruct_from_text.py $partsArg --output `"$TargetDir`""
        Write-Host $cmd
        Invoke-Expression $cmd
    } else {
        Write-Host "Using pure PowerShell reconstruction (core + dev parts)..."
        if ($coreParts) {
            $c = Reconstruct-FromParts -PartFiles $coreParts -OutDir $TargetDir
            Write-Host "Core files written: $c"
        }
        if ($devParts) {
            $c = Reconstruct-FromParts -PartFiles $devParts -OutDir $TargetDir
            Write-Host "Dev extra files written: $c"
        }
    }

    # Clean obvious garbage
    Get-ChildItem -Path $TargetDir -Include '{*', 'rel' -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^\{|^rel$' -or $_.FullName -like '*\relative' } |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

# Set env (same as end-user, but point to dev tree name if different)
[Environment]::SetEnvironmentVariable('MINIBASIC_DIR', $TargetDir, 'User')
$env:MINIBASIC_DIR = $TargetDir
Write-Host "MINIBASIC_DIR set to $TargetDir (dev tree)"

# Optional: create dev-friendly launchers in ~/bin (reuse end-user logic or extend)
$binDir = Join-Path $env:USERPROFILE "bin"
if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir -Force | Out-Null }

Write-Host ""
Write-Host "Dev install complete."
Write-Host "Next steps for development / LLM work:"
Write-Host "  cd $TargetDir"
Write-Host "  # Read the guide"
Write-Host "  # Get-Content DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md"
Write-Host "  python scripts/verify_resources.py"
Write-Host "  # Register autonomous heartbeat (status updates every 60s with no user interaction)"
Write-Host "  powershell -File scripts/ps1/register_progress_task.ps1"
Write-Host "  # Run safe regression or full tests"
Write-Host "  python test/run_regression.py -v"
Write-Host ""
Write-Host "See DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md for the full autonomous TODO pipeline, user-check gates, and how LLMs continue work."