# Run after closing Cursor and any terminals open in mini_basic.
# Creates: C:\Users\Tony\mini_basic -> this OneDrive folder

$ErrorActionPreference = 'Stop'
$target = 'D:\1\OneDrive - FFWPU-Fin\mini_basic'
$link = 'C:\Users\Tony\mini_basic'

# Mirror files written before junction exists (safe to delete).
$stubOnlyNames = @(
    'FOLLOW_PROGRESS.txt',
    'PHONE_PROGRESS.txt',
    'PROGRESS.rss',
    'SYNC_STAMP.txt',
    'WHERE_IS_THE_PROJECT.txt',
    'RSS_FEED_URL.txt',
    'PHONE_README.txt',
    'RSS_SETUP.txt'
)

function Test-StubOnlyDirectory {
    param([string]$Path)
    $items = @(Get-ChildItem $Path -Force -ErrorAction SilentlyContinue)
    if ($items.Count -eq 0) {
        return $true
    }
    foreach ($item in $items) {
        if ($item.PSIsContainer) {
            return $false
        }
        if ($stubOnlyNames -notcontains $item.Name) {
            return $false
        }
    }
    return $true
}

function Clear-StubDirectory {
    param([string]$Path)
    Get-ChildItem $Path -Force -ErrorAction SilentlyContinue | Remove-Item -Force -Recurse
}

if (-not (Test-Path $target)) {
    Write-Error "Target missing: $target"
    exit 1
}

if (Test-Path $link) {
    $item = Get-Item $link -Force
    if ($item.LinkType -eq 'Junction') {
        $current = (Get-Item $link).Target
        if ($current -eq $target) {
            Write-Host "Junction already OK: $link -> $target"
            exit 0
        }
        Write-Error "Existing junction points elsewhere: $current"
        exit 1
    }

    if (Test-StubOnlyDirectory -Path $link) {
        $count = @(Get-ChildItem $link -Force -ErrorAction SilentlyContinue).Count
        if ($count -gt 0) {
            Write-Host "Removing $count stub mirror file(s) from $link ..."
            Clear-StubDirectory -Path $link
        }
    }
    else {
        $names = (Get-ChildItem $link -Force | Select-Object -ExpandProperty Name) -join ', '
        Write-Error "Refusing: $link contains non-stub items: $names"
        exit 1
    }

    $removed = $false
    try {
        Remove-Item $link -Force
        $removed = $true
    }
    catch {
        $backup = "$link._stub_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Write-Host "Folder locked; trying rename -> $backup"
        try {
            Rename-Item $link $backup -Force
            $removed = $true
        }
        catch {
            $removed = $false
        }
    }
    if (-not $removed) {
        Write-Error @"
Cannot remove or rename $link — it is locked (Cursor or a terminal).

1. Close Cursor completely (File -> Exit)
2. Close any PowerShell windows whose path is mini_basic
3. Run again: .\finish_junction.ps1

Stub mirror files were already deleted; only the empty folder remains.
"@
        exit 1
    }
}

cmd /c mklink /J "$link" "$target" | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Error 'mklink failed. Close Cursor/terminals using mini_basic, then run again.'
    exit 1
}

if (Test-Path "$link\README.md") {
    Write-Host "Done. $link now points at OneDrive."
}
else {
    Write-Error 'Junction created but README.md not visible — check paths.'
    exit 1
}