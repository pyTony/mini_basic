# Try Cloudflare quick tunnel; if it fails use start_web_localhost_run.ps1 instead.
# Run: powershell -File start_web_tunnel.ps1

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = (Get-Command python -ErrorAction Stop).Source
$Server = Join-Path $Root 'serve_progress_web.py'

$cf = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cf) {
    Write-Host 'cloudflared not in PATH.'
    Write-Host 'Try: powershell -File start_web_localhost_run.ps1'
    Write-Host 'Or share status.html from OneDrive - see WEB_PUBLISH.txt'
    exit 1
}

$existing = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
if (-not $existing) {
    Start-Process -FilePath $Python -ArgumentList $Server -WorkingDirectory $Root -WindowStyle Minimized
    Start-Sleep -Seconds 2
}

try {
    Invoke-WebRequest -Uri 'http://127.0.0.1:8765/status.html' -UseBasicParsing -TimeoutSec 5 | Out-Null
} catch {
    Write-Error 'Local server not on port 8765. Run: python serve_progress_web.py'
    exit 1
}

Write-Host 'Starting Cloudflare quick tunnel...'
Write-Host 'If you see error 1101, Cloudflare is down or blocked. Use instead:'
Write-Host '  powershell -File start_web_localhost_run.ps1'
Write-Host ''
& cloudflared tunnel --url http://127.0.0.1:8765
if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Host 'Cloudflare failed. Run: powershell -File start_web_localhost_run.ps1'
}