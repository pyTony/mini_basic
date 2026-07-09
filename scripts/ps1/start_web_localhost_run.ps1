# Internet URL from home PC via localhost.run (no Cloudflare account).
# Requires: OpenSSH client (built into Windows 10+).
# Run: powershell -File start_web_localhost_run.ps1
# Copy the https://....lhr.life URL shown for your phone.

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = (Get-Command python -ErrorAction Stop).Source
$Server = Join-Path $Root 'serve_progress_web.py'

$existing = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
if (-not $existing) {
    Start-Process -FilePath $Python -ArgumentList $Server -WorkingDirectory $Root -WindowStyle Minimized
    Start-Sleep -Seconds 2
}

try {
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8765/status.html' -UseBasicParsing -TimeoutSec 5
    if ($r.StatusCode -ne 200) { throw 'bad status' }
} catch {
    Write-Error 'Local server not responding on port 8765. Run: python serve_progress_web.py'
    exit 1
}

Write-Host 'Starting localhost.run tunnel to http://127.0.0.1:8765 ...'
Write-Host 'Look for a line like: https://xxxxxxxx.lhr.life'
Write-Host 'Open that URL on your phone (any network). Ctrl+C to stop.'
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:127.0.0.1:8765 nokey@localhost.run