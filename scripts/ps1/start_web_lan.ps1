# Serve progress on your home WiFi only.
# Run: powershell -File start_web_lan.ps1
# Phone (same WiFi): http://YOUR-PC-IP:8765/

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = (Get-Command python -ErrorAction Stop).Source
$Server = Join-Path $Root 'serve_progress_web.py'

$ip = (Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -ne 'WellKnown' } |
    Select-Object -First 1 -ExpandProperty IPAddress)

if (-not $ip) { $ip = 'YOUR-PC-IP' }

Write-Host "LAN URL: http://${ip}:8765/"
Write-Host 'Press Ctrl+C to stop.'
Set-Location $Root
& $Python $Server