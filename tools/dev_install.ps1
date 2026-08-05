# dev_install.ps1 - Text-based development installation for mini_basic
# Modeled on the end-user install.ps1, pointed at the dev archive.
#
# Usage (pure PS, like end-user):
#   Drop this + mini_basic_text_dev_part*.txt (+ README)
#   into a folder and run .\dev_install.ps1
#
# NOTE ON ARCHIVE STRUCTURE: create_text_archive.py's --mode dev produces a
# single, complete, standalone set of text parts -- it already contains
# everything the dist archive has (mini_basic/ including runtime_parts/ mixins,
# basics/, examples/, documentation/) *plus* development-only material
# (docs/, test/, scripts/, utils/, tools/). There is no separate "core"
# archive to layer dev extras on top of; the dev parts alone reconstruct the
# full dev tree. (backup/ is excluded from both archives.)
#
# Modular runtime after reconstruct:
#   mini_basic/runtime.py + mini_basic/runtime_parts/* + tools/split_runtime_mixins.py
#
# This produces a FULL DEVELOPMENT tree containing:
# - mini_basic/, basics/, examples/, documentation/ (same as the dist tree)
# - test/, scripts/, tools/, utils/, docs/ (development-only material)
#
# Options:
#   -TargetDir "path"   (default: mini_basic_dev next to this script)
#   -SkipReconstruct
#   -SkipGit
#   -Uninstall
#
# After install:
#   cd mini_basic_dev
#   python -m pytest -m phase1 -q
#   # or: python -m unittest discover -s test -p "test_*.py" -q

param(
    [string]$TargetDir = "",
    [switch]$Uninstall,
    [switch]$SkipReconstruct,
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
    if (Test-Path $target) {
        Remove-Item -Path $target -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Removed $target"
    } else {
        Write-Host "Target not present: $target"
    }
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
Write-Host "Reconstructs the full dev tree (core + test/scripts/tools/utils/docs) from mini_basic_text_dev_part*.txt"

# Locate the dev archive parts. Same search order as install.ps1.
$searchDirs = @(
    (Join-Path $here "archive"),
    (Join-Path $here "archives"),
    (Join-Path $here "dist"),
    $here
)

$devParts = @()
foreach ($d in $searchDirs) {
    $found = Get-ChildItem -Path $d -Filter "mini_basic_text_dev_part*.txt" -ErrorAction SilentlyContinue | Sort-Object Name
    if ($found) {
        $devParts = $found.FullName
        break
    }
}

if (-not $devParts -or $devParts.Count -eq 0) {
    Write-Error "Could not find mini_basic_text_dev_part*.txt (looked in archive/, archives/, dist/, and $here)"
    exit 1
}
Write-Host "Found $($devParts.Count) dev text part(s) for reconstruction."

if (-not $TargetDir) {
    $TargetDir = Join-Path $here "mini_basic_dev"
}
$TargetDir = [System.IO.Path]::GetFullPath($TargetDir)
Write-Host "Target dev tree: $TargetDir"

if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

if (-not $SkipReconstruct) {
    Write-Host "Reconstructing the dev tree from text parts..."

    $BEGIN_RE = '^=====+\s*BEGIN FILE:\s*(.+?)\s*=+\s*$'
    $END_RE   = '^=====+\s*END FILE\s*=+\s*$'
    $ESC_PREFIX = 'ARCHIVE-MARKER-ESCAPED: '

    $allText = ""
    foreach ($pf in $devParts) {
        if (Test-Path $pf) { $allText += "`n" + [System.IO.File]::ReadAllText($pf) }
    }

    $lines = $allText -split "`r?`n"
    $currentPath = $null
    $current = New-Object System.Collections.Generic.List[string]
    $count = 0

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]

        if ($line -match $BEGIN_RE) {
            $currentPath = $Matches[1].Trim()
            # Defensive skip for bogus paths leaking from example comments or
            # f-strings inside archived tools/create_text_archive.py.
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
            $unescLines = $raw -split "`n" | ForEach-Object {
                if ($_.StartsWith($ESC_PREFIX)) { $_.Substring($ESC_PREFIX.Length) } else { $_ }
            }
            $content = ($unescLines -join "`n")
            if ($content -and -not $content.EndsWith("`n")) { $content += "`n" }
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

        if ($currentPath -ne $null) { $current.Add($line) }
    }

    if ($currentPath -ne $null -and $current.Count -gt 0) {
        if ($currentPath -match '[\{\}\$]' -or $currentPath -eq 'relative/path.py' -or $currentPath -match 'item\[0\]|rel\}|example') {
            $currentPath = $null
        } else {
            $raw = ($current -join "`n")
            $unescLines = $raw -split "`n" | ForEach-Object {
                if ($_.StartsWith($ESC_PREFIX)) { $_.Substring($ESC_PREFIX.Length) } else { $_ }
            }
            $content = ($unescLines -join "`n") -replace '^\uFEFF', ''
            $outPath = Join-Path $TargetDir $currentPath
            $parent = Split-Path -Parent $outPath
            if ($parent -and -not (Test-Path $parent)) {
                New-Item -ItemType Directory -Path $parent -Force | Out-Null | Out-Null
            }
            [System.IO.File]::WriteAllText($outPath, $content, $utf8NoBom)
            $count++
        }
    }

    Write-Host "Files written: $count"

    Get-ChildItem -Path $TargetDir -Include '{*', 'rel' -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^\{|^rel$' -or $_.FullName -like '*\relative' } |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

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
    'mini_basic.py',
    'tools\split_runtime_mixins.py',
    'tools\create_text_archive.py'
)
$missing = @()
foreach ($rel in $requiredPaths) {
    $full = Join-Path $TargetDir $rel
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) {
        $missing += $rel
    }
}
if ($missing.Count -gt 0) {
    Write-Host "ERROR: reconstructed dev tree is missing required files:" -ForegroundColor Red
    foreach ($m in $missing) { Write-Host "  - $m" -ForegroundColor Red }
    Write-Host "Regenerate with: python tools/create_text_archive.py --mode both --outdir dist" -ForegroundColor Yellow
    Write-Error "Dev install aborted: incomplete modular package."
    exit 1
}
$mixinCount = @(Get-ChildItem -Path (Join-Path $TargetDir 'mini_basic\runtime_parts') -Filter '*.py' -File -ErrorAction SilentlyContinue).Count
Write-Host "Modular runtime OK ($mixinCount runtime_parts modules)."

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
}

[Environment]::SetEnvironmentVariable('MINIBASIC_DIR', $TargetDir, 'User')
$env:MINIBASIC_DIR = $TargetDir
Write-Host "MINIBASIC_DIR set to $TargetDir (dev tree)"

$binDir = Join-Path $env:USERPROFILE "bin"
if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir -Force | Out-Null }

# Launchers (same behaviour as install.ps1) so `mini_basic` works from a dev tree.
$launcher = @'
$ErrorActionPreference = 'Stop'
$project = $env:MINIBASIC_DIR
if (-not $project -or -not (Test-Path $project)) {
    Write-Error "MINIBASIC_DIR not set or target missing. Re-run dev_install.ps1 or set the variable."
    exit 1
}
$orig = Get-Location
$pass = @($args)
for ($i = 0; $i -lt $pass.Count; $i++) {
    if (-not $pass[$i].StartsWith('-')) {
        $cand = $pass[$i]
        $fromUser = Join-Path $orig.Path $cand
        if (Test-Path $fromUser -PathType Leaf) {
            $pass[$i] = (Resolve-Path $fromUser).Path
        } else {
            $fromProj = Join-Path $project $cand
            if (Test-Path $fromProj -PathType Leaf) {
                $pass[$i] = (Resolve-Path $fromProj).Path
            }
        }
        break
    }
}
Push-Location $project
try { python -m mini_basic @pass } finally { Pop-Location }
'@
Set-Content -Path (Join-Path $binDir "mini_basic.ps1") -Value $launcher -Encoding UTF8
Set-Content -Path (Join-Path $binDir "minibasic.ps1") -Value $launcher -Encoding UTF8
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
    if ($env:Path) { $env:Path += ';' }
    $env:Path += $binDir
}
Write-Host "Launchers created in $binDir"

if (-not $SkipGit) {
    Push-Location $TargetDir
    try {
        if (-not (Test-Path ".git")) {
            Write-Host "Initializing Git..."
            git init | Out-Null
            git config --local user.name "mini_basic Dev" | Out-Null
            git config --local user.email "mini_basic-dev@local" | Out-Null
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
            git commit -m "feat: initial dev tree" | Out-Null
            Write-Host "Git repository initialized with first commit."
        } else {
            Write-Host "Git repo already exists in target."
        }
    } finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "=== Dev install complete ===" -ForegroundColor Green
Write-Host "Project is at: $TargetDir"
Write-Host "MINIBASIC_DIR set permanently."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  cd $TargetDir"
Write-Host "  python -m mini_basic --help"
Write-Host "  python -m pytest -m phase1 -q"
Write-Host "  # or: python -m unittest discover -s test -p `"test_*.py`" -q"
Write-Host "  # re-split monorepo mixins: python tools/split_runtime_mixins.py"
Write-Host ""
Write-Host "To uninstall later: .\dev_install.ps1 -Uninstall"
