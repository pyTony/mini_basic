# mini_basic install / setup script (self-contained)
# For end users: drop text parts + this script + README.md into a folder and run:
#   .\install.ps1 -ArchiveKind cli    # command-line only parts
#   .\install.ps1 -ArchiveKind dist   # full sample tree
#   .\install.ps1                     # auto: dist if present, else cli, else legacy
# Parts: mini_basic_text_cli_part*.txt  or  mini_basic_text_dist_part*.txt
#
# Live layout after reconstruct (modular runtime):
#   mini_basic/runtime.py              — facade + CLI/REPL
#   mini_basic/runtime_parts/*.py      — mixin modules (core, expr, execution, …)
#   mini_basic.py / mb.py              — entry shims
#   basics/  examples/  documentation/
#
# This script:
# 1. Reconstructs the full project tree from the text archive parts (pure PS, no python needed for setup)
# 2. Verifies the modular package (runtime_parts present; optional import smoke test)
# 3. Sets MINIBASIC_DIR environment variable permanently (User scope)
# 4. Creates ~/bin launchers (mini_basic / minibasic) that handle CWD + relative .bas paths
# 5. Initializes a git repo + .gitignore in the target (first run only)
#
# Works on Windows 10+ (PowerShell 5.1 or pwsh 7+). Requires Python 3 in PATH for running.
# Run as:  .\install.ps1   or   .\install.ps1 -Uninstall

param(
    [string]$TargetDir = "",
    [ValidateSet('auto', 'cli', 'dist')]
    [string]$ArchiveKind = 'auto',
    [switch]$Uninstall,
    [switch]$SkipReconstruct,
    [switch]$SkipGit
)

$ErrorActionPreference = 'Stop'

function Get-ScriptDir {
    if ($PSScriptRoot) { return $PSScriptRoot }
    if ($MyInvocation.MyCommand.Path) {
        return Split-Path -Parent $MyInvocation.MyCommand.Path
    }
    return (Get-Location).Path
}

$here = Get-ScriptDir

if ($Uninstall) {
    Write-Host "=== mini_basic uninstall ===" -ForegroundColor Cyan
    $target = [Environment]::GetEnvironmentVariable('MINIBASIC_DIR', 'User')
    if (-not $target) {
        $target = Join-Path $here "mini_basic"
    }
    $target = [System.IO.Path]::GetFullPath($target)

    if (Test-Path $target) {
        Remove-Item -Path $target -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Removed $target"
    } else {
        Write-Host "Target not present: $target"
    }

    $binDir = Join-Path $env:USERPROFILE "bin"
    foreach ($name in @("mini_basic.ps1", "minibasic.ps1", "mini_basic.cmd", "minibasic.cmd")) {
        $f = Join-Path $binDir $name
        if (Test-Path $f) {
            Remove-Item $f -Force -ErrorAction SilentlyContinue
        }
    }

    [Environment]::SetEnvironmentVariable('MINIBASIC_DIR', $null, 'User')
    Write-Host "Uninstall complete."
    return
}

Write-Host "=== mini_basic setup ===" -ForegroundColor Cyan
Write-Host "ArchiveKind: $ArchiveKind  (cli = command-line only; dist = full samples; auto = prefer dist then cli)"

# Locate the text archive parts.
# Supported locations (checked in order):
#   archive/   (recommended clean single subdirectory for distribution parts)
#   archives/
#   dist/
#   same directory as the installer
# Naming:
#   mini_basic_text_cli_part*.txt   — command-line only (smallest)
#   mini_basic_text_dist_part*.txt  — full curated distribution
#   mini_basic_text_part*.txt       — legacy pre-mode name (treated as dist)
$searchDirs = @(
    (Join-Path $here "archive"),
    (Join-Path $here "archives"),
    (Join-Path $here "dist"),
    $here
)

function Find-ArchiveParts {
    param(
        [string[]]$Dirs,
        [string]$Filter,
        [string]$Label
    )
    foreach ($d in $Dirs) {
        $found = Get-ChildItem -Path $d -Filter $Filter -ErrorAction SilentlyContinue | Sort-Object Name
        if ($found) {
            return @{ Files = @($found.FullName); Label = $Label; Dir = $d }
        }
    }
    return $null
}

$partFiles = @()
$resolvedKind = $null

if ($ArchiveKind -eq 'cli') {
    $hit = Find-ArchiveParts -Dirs $searchDirs -Filter 'mini_basic_text_cli_part*.txt' -Label 'cli'
    if ($hit) {
        $partFiles = $hit.Files
        $resolvedKind = 'cli'
    }
} elseif ($ArchiveKind -eq 'dist') {
    $hit = Find-ArchiveParts -Dirs $searchDirs -Filter 'mini_basic_text_dist_part*.txt' -Label 'dist'
    if ($hit) {
        $partFiles = $hit.Files
        $resolvedKind = 'dist'
    }
} else {
    # auto: prefer full dist when both present; else cli; else legacy
    $hit = Find-ArchiveParts -Dirs $searchDirs -Filter 'mini_basic_text_dist_part*.txt' -Label 'dist'
    if (-not $hit) {
        $hit = Find-ArchiveParts -Dirs $searchDirs -Filter 'mini_basic_text_cli_part*.txt' -Label 'cli'
    }
    if (-not $hit) {
        $hit = Find-ArchiveParts -Dirs $searchDirs -Filter 'mini_basic_text_part*.txt' -Label 'legacy'
    }
    if ($hit) {
        $partFiles = $hit.Files
        $resolvedKind = $hit.Label
    }
}

if (-not $partFiles -or $partFiles.Count -eq 0) {
    Write-Error @"
Could not find archive parts for ArchiveKind=$ArchiveKind
Looked in archive/, archives/, dist/, and $here
Expected filters:
  mini_basic_text_cli_part*.txt   (command-line only)
  mini_basic_text_dist_part*.txt  (full dist)
  mini_basic_text_part*.txt       (legacy)
Generate with: python tools/create_text_archive.py --mode cli|dist|all --outdir dist
"@
    exit 1
}
if ($resolvedKind -eq 'legacy') {
    Write-Host "Note: using legacy-named archive parts (mini_basic_text_part*.txt)." -ForegroundColor Yellow
}
Write-Host "Found $($partFiles.Count) text part(s) ($resolvedKind) for reconstruction."

# Default target: a clean "mini_basic" subdir next to the installer location
# (so running from a "package" folder puts everything under mini_basic\ subdir)
if (-not $TargetDir) {
    $TargetDir = Join-Path $here "mini_basic"
}

$TargetDir = [System.IO.Path]::GetFullPath($TargetDir)
Write-Host "Target: $TargetDir"

if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

# UTF-8 without BOM (important for .bas files, Python source, etc.)
# [System.Text.Encoding]::UTF8 would inject a leading \uFEFF BOM that breaks parsers.
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

# Self-contained reconstruction (no dependency on tools/reconstruct_from_text.py)
if (-not $SkipReconstruct) {
    Write-Host "Reconstructing the project from text parts..."

    $BEGIN_RE = '^=====+\s*BEGIN FILE:\s*(.+?)\s*=+\s*$'
    $END_RE   = '^=====+\s*END FILE\s*=+\s*$'
    $ESC_PREFIX = 'ARCHIVE-MARKER-ESCAPED: '

    $allText = ""
    foreach ($pf in $partFiles) {
        if (Test-Path $pf) {
            $allText += "`n" + [System.IO.File]::ReadAllText($pf)
        }
    }

    $lines = $allText -split "`r?`n"
    $currentPath = $null
    $current = New-Object System.Collections.Generic.List[string]
    $count = 0

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]

        if ($line -match $BEGIN_RE) {
            if ($currentPath -ne $null -and $current.Count -gt 0) {
                # flush stray previous (should not normally happen)
            }
            $currentPath = $Matches[1].Trim()
            # Defensive skip for bogus paths that can leak from example comments or
            # f-strings inside archived tools/create_text_archive.py (e.g. {item[0]}, {rel},
            # relative/path.py). These would otherwise create garbage files like {item[0]}
            # and a "relative" directory at the target root.
            if ($currentPath -match '[\{\}\$]' -or
                $currentPath -eq 'relative/path.py' -or
                $currentPath -match 'item\[0\]|rel\}|example' -or
                -not ($currentPath -match '[/\\.]' -or $currentPath -match '\.(py|bas|bbc|txt|md|toml)$')) {
                $currentPath = $null
                continue
            }
            $current.Clear()
            continue
        }

        if ($currentPath -ne $null -and ($line.Trim() -match $END_RE)) {
            $raw = ($current -join "`n")
            # Unescape any archived marker lines
            $unescLines = $raw -split "`n" | ForEach-Object {
                if ($_.StartsWith($ESC_PREFIX)) { $_.Substring($ESC_PREFIX.Length) } else { $_ }
            }
            $content = ($unescLines -join "`n")
            if ($content -and -not $content.EndsWith("`n")) { $content += "`n" }

            # Explicitly strip any leading UTF-8 BOM (U+FEFF) that might have been present
            # in the archive content or from previous bad writes. This prevents syntax errors
            # like "﻿PRINT ..." in .bas files.
            $content = $content -replace '^\uFEFF', ''

            $outPath = Join-Path $TargetDir $currentPath
            $parent = Split-Path -Parent $outPath
            if ($parent -and -not (Test-Path $parent)) {
                New-Item -ItemType Directory -Path $parent -Force | Out-Null | Out-Null
            }
            [System.IO.File]::WriteAllText($outPath, $content, $utf8NoBom)
            $count++
            $currentPath = $null
            $current.Clear()
            continue
        }

        if ($currentPath -ne $null) {
            $current.Add($line)
        }
    }

    # trailing unclosed
    if ($currentPath -ne $null -and $current.Count -gt 0) {
        if ($currentPath -match '[\{\}\$]' -or $currentPath -eq 'relative/path.py' -or $currentPath -match 'item\[0\]|rel\}|example') {
            $currentPath = $null
        } else {
            $raw = ($current -join "`n")
            $unescLines = $raw -split "`n" | ForEach-Object {
                if ($_.StartsWith($ESC_PREFIX)) { $_.Substring($ESC_PREFIX.Length) } else { $_ }
            }
            $content = ($unescLines -join "`n")
            $content = $content -replace '^\uFEFF', ''
            $outPath = Join-Path $TargetDir $currentPath
            $parent = Split-Path -Parent $outPath
            if ($parent -and -not (Test-Path $parent)) {
                New-Item -ItemType Directory -Path $parent -Force | Out-Null | Out-Null
            }
            [System.IO.File]::WriteAllText($outPath, $content, $utf8NoBom)
            $count++
        }
    }

    # (files written silently to keep output minimal and match documented flow)

    # Clean up any garbage files/directories that may have been created by previous
    # buggy parser versions (e.g. {item[0]}, {rel}, relative/ from example text).
    Get-ChildItem -Path $TargetDir -Include '{*', 'rel' -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^\{|^rel$' -or $_.FullName -like '*\relative' } |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    # Belt-and-suspenders: strip any remaining UTF-8 BOM from text source files.
    # This fixes files from previous installs that used WriteAllText with BOM.
    Get-ChildItem -Path $TargetDir -Recurse -Include *.bas,*.bbc,*.py,*.txt,*.md,*.toml,*.ps1 -File -ErrorAction SilentlyContinue | ForEach-Object {
        $bytes = [System.IO.File]::ReadAllBytes($_.FullName)
        if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
            $clean = [System.Text.Encoding]::UTF8.GetString($bytes, 3, $bytes.Length-3)
            [System.IO.File]::WriteAllText($_.FullName, $clean, $utf8NoBom)
        }
    }
}

# --- Verify modular runtime tree ---
$requiredPaths = @(
    'mini_basic\runtime.py',
    'mini_basic\runtime_parts\__init__.py',
    'mini_basic\runtime_parts\core.py',
    'mini_basic\runtime_parts\execution.py',
    'mini_basic\runtime_parts\expr.py',
    'mini_basic\__init__.py',
    'mini_basic\__main__.py',
    'mini_basic.py'
)
$missing = @()
foreach ($rel in $requiredPaths) {
    $full = Join-Path $TargetDir $rel
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) {
        $missing += $rel
    }
}
if ($missing.Count -gt 0) {
    Write-Host "ERROR: reconstructed tree is missing modular runtime files:" -ForegroundColor Red
    foreach ($m in $missing) { Write-Host "  - $m" -ForegroundColor Red }
    Write-Host "Regenerate archives with: python tools/create_text_archive.py --mode both --outdir dist" -ForegroundColor Yellow
    Write-Error "Install aborted: incomplete modular package (need mini_basic/runtime_parts/*)."
    exit 1
}
$mixinCount = @(Get-ChildItem -Path (Join-Path $TargetDir 'mini_basic\runtime_parts') -Filter '*.py' -File -ErrorAction SilentlyContinue).Count
Write-Host "Modular runtime OK ($mixinCount runtime_parts modules)."

# Optional import smoke (Python on PATH). Non-fatal if Python missing during pure-PS setup.
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    Push-Location $TargetDir
    try {
        $smoke = & python -c "from mini_basic import BASICInterpreter, main; BASICInterpreter(); print('import-ok')" 2>&1
        if ($LASTEXITCODE -ne 0 -or ($smoke -join '') -notmatch 'import-ok') {
            Write-Host "WARNING: Python import smoke failed:" -ForegroundColor Yellow
            Write-Host ($smoke | Out-String)
        } else {
            Write-Host "Python import smoke: OK"
        }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "Note: python not on PATH; skipped import smoke (tree files verified)." -ForegroundColor Yellow
}

# Set MINIBASIC_DIR permanently (User)
[Environment]::SetEnvironmentVariable('MINIBASIC_DIR', $TargetDir, 'User')
$env:MINIBASIC_DIR = $TargetDir
Write-Host "MINIBASIC_DIR set permanently to $TargetDir"

# Create launchers in ~/bin that:
# - cd into the project so working_dir for interpreter is correct for bundled paths
# - auto-resolve a .bas arg relative to the *caller's* CWD (so user files work) or fall back to project (so basics\ and examples\ work)
$binDir = Join-Path $env:USERPROFILE "bin"
if (-not (Test-Path $binDir)) {
    New-Item -ItemType Directory -Path $binDir -Force | Out-Null | Out-Null
}

$launcher = @'
$ErrorActionPreference = 'Stop'

$project = $env:MINIBASIC_DIR
if (-not $project -or -not (Test-Path $project)) {
    Write-Error "MINIBASIC_DIR not set or target missing. Re-run install.ps1 or set the variable."
    exit 1
}

$orig = Get-Location
$pass = @($args)

# Locate the first non-option argument (the target file) and resolve it if possible
for ($i = 0; $i -lt $pass.Count; $i++) {
    if (-not $pass[$i].StartsWith('-')) {
        $cand = $pass[$i]
        $resolved = $false

        # Prefer a file that exists relative to where the user typed the command
        $fromUser = Join-Path $orig.Path $cand
        if (Test-Path $fromUser -PathType Leaf) {
            $pass[$i] = (Resolve-Path $fromUser).Path
            $resolved = $true
        }

        if (-not $resolved) {
            # Fall back to one that exists inside the installed project (basics\, examples\ etc.)
            $fromProj = Join-Path $project $cand
            if (Test-Path $fromProj -PathType Leaf) {
                $pass[$i] = (Resolve-Path $fromProj).Path
            }
            # else leave relative; Push-Location below makes it resolve against project
        }
        break
    }
}

Push-Location $project
try {
    python -m mini_basic @pass
} finally {
    Pop-Location
}
'@

Set-Content -Path (Join-Path $binDir "mini_basic.ps1") -Value $launcher -Encoding UTF8
Set-Content -Path (Join-Path $binDir "minibasic.ps1") -Value $launcher -Encoding UTF8

# Create .cmd shims for reliable command discovery (works from cmd.exe and PowerShell
# because .cmd is in default PATHEXT). These forward to the .ps1 (which contains the
# CWD resolution and MINIBASIC_DIR logic).
$cmdShim = @'
@echo off
setlocal
set "SCRIPTNAME=%~n0.ps1"
set "PSCMD=pwsh"
where pwsh >nul 2>&1 || set "PSCMD=powershell"
%PSCMD% -NoProfile -ExecutionPolicy Bypass -File "%~dp0%SCRIPTNAME%" %*
'@
Set-Content -Path (Join-Path $binDir "mini_basic.cmd") -Value $cmdShim -Encoding ASCII
Set-Content -Path (Join-Path $binDir "minibasic.cmd") -Value $cmdShim -Encoding ASCII

# Ensure ~/bin is on user PATH (permanent + current session).
# Use robust check to avoid duplicates.
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if (-not $userPath) { $userPath = '' }
$pathParts = $userPath -split ';' | Where-Object { $_ }
$alreadyInPath = $pathParts | Where-Object { $_.TrimEnd('\') -ieq $binDir.TrimEnd('\') }
if (-not $alreadyInPath) {
    $newUserPath = ($pathParts + $binDir) -join ';'
    [Environment]::SetEnvironmentVariable('Path', $newUserPath, 'User')
    Write-Host "Added $binDir to user PATH"
}
if ($env:Path -notlike "*$binDir*") {
    $env:Path = ($env:Path -split ';' | Where-Object { $_ } | Where-Object { $_.TrimEnd('\') -ine $binDir.TrimEnd('\') }) -join ';'
    if ($env:Path) { $env:Path += ';' }
    $env:Path += $binDir
}

Write-Host "Launchers created in $binDir (with .cmd shims for reliable discovery)"

# Git init (only if no .git yet)
if (-not $SkipGit) {
    Push-Location $TargetDir
    try {
        if (-not (Test-Path ".git")) {
            Write-Host "Initializing Git..."
            git init | Out-Null

            git config --local user.name "mini_basic User" | Out-Null
            git config --local user.email "mini_basic@local" | Out-Null
            git config --local core.autocrlf false | Out-Null

            $gitignore = @"
__pycache__/
*.pyc
backup/
*.bak
mini_basic_text_dist_part*.txt
mini_basic_text_dev_part*.txt
mini_basic_text_part*.txt
test_reconstruct/
.vscode/
.idea/
*.swp
Thumbs.db
"@
            [System.IO.File]::WriteAllText((Join-Path $TargetDir ".gitignore"), $gitignore, $utf8NoBom)

            git add .gitignore | Out-Null
            git commit -m "chore: add .gitignore" | Out-Null

            git add . | Out-Null
            git commit -m "feat: initial clean project" | Out-Null

            Write-Host "Git repository initialized with first commit."
        } else {
            Write-Host "Git repo already exists in target."
        }
    } finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "=== Done! ===" -ForegroundColor Green
Write-Host "Project is at: $TargetDir"
Write-Host "Archive kind installed: $resolvedKind"
Write-Host "MINIBASIC_DIR set permanently."
Write-Host ""
Write-Host "Close this PowerShell window and open a **new** one (important), then try:"
Write-Host "  mini_basic basics\fact.bas"
Write-Host "  minibasic --help"
Write-Host "  mini_basic --display none examples\mini\hello_args.bas"
if ($resolvedKind -eq 'cli') {
    Write-Host ""
    Write-Host "CLI distribution notes (no pixel graphics):" -ForegroundColor Cyan
    Write-Host "  - No bbc_font/bbc_graphics; --display pygame is not available."
    Write-Host "  - Use --display terminal (default) or --display none."
    Write-Host "  - No games/graphics demo trees (use full dist for those)."
    Write-Host "  - See CLI_ONLY.txt in the project root."
    Write-Host "  - Better REPL: pip install -r requirements-repl.txt"
}
Write-Host ""
Write-Host "If 'mini_basic' is still not recognized after opening a new shell:"
Write-Host "  - Make sure $binDir is in your PATH (echo `$env:Path)"
Write-Host "  - Try running the full script once:  & `"$binDir\mini_basic.ps1`" --help"
Write-Host "  - Restart Windows Terminal / your terminal app completely, or sign out/in."
Write-Host ""
Write-Host "To uninstall later: .\install.ps1 -Uninstall"
Write-Host "To install CLI-only parts explicitly: .\install.ps1 -ArchiveKind cli"
Write-Host "To move later: move the folder and update the MINIBASIC_DIR env var."
Write-Host '  [Environment]::SetEnvironmentVariable("MINIBASIC_DIR", "C:\new\path", "User")'
