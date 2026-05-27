# video-auto-editor — PowerShell launcher (alternative to .bat)
# Double-click won't run .ps1 by default; use:  pwsh -ExecutionPolicy Bypass -File open-editor.ps1
# (or right-click the .bat instead.)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backendPort = 8000
$frontendPort = 3000
$url = "http://localhost:$frontendPort"

Write-Host ""
Write-Host "============================================================"
Write-Host "  video-auto-editor   one-click launcher (PowerShell)"
Write-Host "============================================================"
Write-Host "  project: $root"
Write-Host ""

if (-not (Test-Path "$root\.venv\Scripts\python.exe")) {
    Write-Host "[!] Python venv missing. Run scripts\setup.bat first." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path "$root\web\frontend\node_modules")) {
    Write-Host "[!] Frontend node_modules missing. Run scripts\setup.bat first." -ForegroundColor Red
    exit 1
}

function Stop-PortListener {
    param([int]$Port)
    Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
        ForEach-Object {
            Write-Host "  killing existing pid $($_.OwningProcess) on :$Port"
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }
}

Write-Host "[1/3] freeing ports..."
Stop-PortListener -Port $backendPort
Stop-PortListener -Port $frontendPort

Write-Host "[2/3] starting backend on :$backendPort..."
Start-Process -FilePath "cmd.exe" -ArgumentList @(
    "/k",
    "title vae backend && cd /d `"$root`" && set PYTHONPATH=src && .venv\Scripts\python.exe -m uvicorn web.backend.app:app --host 127.0.0.1 --port $backendPort"
)

Write-Host "[3/3] starting frontend on :$frontendPort..."
Start-Process -FilePath "cmd.exe" -ArgumentList @(
    "/k",
    "title vae frontend && cd /d `"$root\web\frontend`" && npm run dev"
)

Start-Sleep -Seconds 6
Write-Host "Opening $url ..."
Start-Process $url

Write-Host ""
Write-Host "READY. Close the two extra terminals (or run scripts\stop-editor.bat) to shut down." -ForegroundColor Green
Start-Sleep -Seconds 4
