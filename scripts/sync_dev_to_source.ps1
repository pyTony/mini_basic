# sync_dev_to_source.ps1
# Periodic / manual sync of local dev tree development to the OneDrive source tree.
#
# Purpose: Support independent operation in the local dev tree (Programming/mini_basic)
# while keeping the full source tree (OneDrive) up to date for remote checks,
# full corpus work, text archive generation, etc.
#
# Run manually or via scheduled task.
# It copies key development artifacts, excluding generated/temporary files.
# After copy, you can commit in the source tree if using git there.

param(
    [string]$SourceDir = "C:\Users\Tony\Programming\mini_basic",
    [string]$TargetDir = "C:\Users\Tony\mini_basic",
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
Write-Host "Review changes in source tree, then run git add/commit there if desired."
Write-Host "For status.html remote check, the copy above includes it."

if ($DryRun) {
    Write-Host "(Dry run - no files copied)"
}