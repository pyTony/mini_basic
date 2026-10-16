<#
.SYNOPSIS
    Strips line numbers + cleans spacing bugs from BASIC files.
    Works on both Windows PowerShell 5.1 and PowerShell 7+ (no BOM).
#>

param(
    [Parameter(Mandatory=$true)][string]$InputFile,
    [Parameter(Mandatory=$false)][string]$OutputFile = ""
)

if (-not (Test-Path $InputFile)) {
    Write-Error "File not found: $InputFile"
    exit 1
}
if ($OutputFile -eq "") {
    $OutputFile = [System.IO.Path]::ChangeExtension($InputFile, ".clean.bas")
}

$lines = Get-Content $InputFile -Encoding UTF8
$cleanLines = @()

foreach ($line in $lines) {
    $clean = $line -replace '^\s*\d+\s+', ''
    $clean = $clean -replace ' % ', '%'
    $clean = $clean -replace ' %=', '%='
    $clean = $clean -replace '% =', '%='
    $clean = $clean -replace ' \+ = ', ' += '
    $clean = $clean -replace ' - = ', ' -= '
    $clean = $clean -replace ' \* = ', ' *= '
    $clean = $clean -replace ' / = ', ' /= '
    $clean = $clean -replace '(\w)\s+%', '$1%'

    if ($clean.Trim() -ne "") { $cleanLines += $clean }
}

# Write without BOM (works on PS 5.1 and PS 7+)
[System.IO.File]::WriteAllLines($OutputFile, $cleanLines, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "Created clean file: $OutputFile"
Write-Host "Total lines: $($cleanLines.Count)"
