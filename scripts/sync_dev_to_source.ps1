# Copy selected files from one checkout to another on this machine.
# Both directories must be passed in. Missing items are skipped.
#
# Example:
#   .\sync_dev_to_source.ps1 -SourceDir D:\work\mini_basic -TargetDir D:\mirror\mini_basic

param(
    [Parameter(Mandatory = $true)]
    [string]$SourceDir,
    [Parameter(Mandatory = $true)]
    [string]$TargetDir,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $SourceDir)) { throw "Source dev tree not found: $SourceDir" }
if (-not (Test-Path $TargetDir)) { throw "Target source tree not found: $TargetDir" }

Write-Host "Syncing dev tree -> source tree"
Write-Host "From: $SourceDir"
Write-Host "To:   $TargetDir"

# Directories and files to sync (relative to source)
$itemsToSync = @(
    "mini_basic",           # the package
    "basics",
    "examples",
    "scripts",
    "lib",
    "utils",
    "documentation",
    "tools",
    "test",                 # tests and corpus (large but needed for full work)
    "README.md",
    "DEVELOPMENT*.md",
    "GIT_QUICKSTART.md",
    "RUNTIME_VERSION_HISTORY.md",
    "docs",
    "requirements*.txt",
    "dev_install.ps1",
    "status.html",          # for remote status check
    "CURRENT_TASK.txt",
    "FEATURES_DONE.txt",
    "USER_APPROVAL*.txt",
    "CORPUS_AUDIT.txt",
    "AGENT_POLICY.txt"
)

$excludePatterns = @(
    "__pycache__",
    "*.pyc",
    ".coverage",
    "*.log",
    "regression_cov.log",
    "coverage_report.txt",
    "tokei_*.txt",
    ".resource_*.json",
    "dist",
    "archives",
    "*_text_part*.txt"   # generated; regenerate in target if needed
)

$copied = 0
foreach ($item in $itemsToSync) {
    $srcPath = Join-Path $SourceDir $item
    $dstPath = Join-Path $TargetDir $item

    if (-not (Test-Path $srcPath)) {
        Write-Host "  Skip (not found): $item"
        continue
    }

    if ($DryRun) {
        Write-Host "  [DRY] Would copy: $item"
        continue
    }

    # Simple copy (for dirs use -Recurse)
    if (Test-Path $srcPath -PathType Container) {
        # Mirror dir, excluding patterns
        robocopy $srcPath $dstPath /MIR /XD __pycache__ dist archives /XF *.pyc *.log *.txt *.json /NFL /NDL /NJH /NJS | Out-Null
        Write-Host "  Synced dir: $item"
    } else {
        Copy-Item $srcPath $dstPath -Force
        Write-Host "  Synced file: $item"
    }
    $copied++
}

Write-Host "`nSync complete. Items processed: $copied"
Write-Host "Review changes in the target tree, then commit there if desired."

if ($DryRun) {
    Write-Host "(Dry run - no files copied)"
}