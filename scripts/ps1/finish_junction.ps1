# Optional: create a Windows directory junction so a short path points at this clone.
# Pass both paths for this machine. There are no host-specific defaults.
#
# Example:
#   .\finish_junction.ps1 -Target (Get-Location) -Link "$env:USERPROFILE\mini_basic"

param(
    [Parameter(Mandatory = $true)]
    [string]$Target,
    [Parameter(Mandatory = $true)]
    [string]$Link
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $Target)) {
    Write-Error "Target missing: $Target"
    exit 1
}

if (Test-Path $Link) {
    $item = Get-Item $Link -Force
    if ($item.LinkType -eq 'Junction') {
        $current = (Get-Item $Link).Target
        if ($current -eq $Target) {
            Write-Host "Junction already OK: $Link -> $Target"
            exit 0
        }
        Write-Error "Existing junction points elsewhere: $current"
        exit 1
    }
    Write-Error "Refusing: $Link already exists and is not a junction."
    exit 1
}

cmd /c mklink /J "$Link" "$Target" | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Error 'mklink failed. Close programs using the link path, then run again.'
    exit 1
}

if (Test-Path (Join-Path $Link 'README.md')) {
    Write-Host "Done. $Link now points at $Target."
}
else {
    Write-Error 'Junction created but README.md not visible — check paths.'
    exit 1
}
