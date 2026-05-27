@echo off
REM ===========================================================
REM  video-auto-editor — One-click launcher (Windows)
REM  Double-click me to start the editor.
REM ===========================================================

setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%.." >nul
set "ROOT=%CD%"
popd >nul

set "BACKEND_PORT=8000"
set "FRONTEND_PORT=3000"
set "FRONTEND_URL=http://localhost:%FRONTEND_PORT%"

title video-auto-editor

echo.
echo ============================================================
echo   video-auto-editor   one-click launcher
echo ============================================================
echo   project: %ROOT%
echo.

REM --- preflight ---
if not exist "%ROOT%\.venv\Scripts\python.exe" (
  echo [!] Python venv not found at "%ROOT%\.venv\"
  echo     Run scripts\setup.bat once first.
  echo.
  pause
  exit /b 1
)
if not exist "%ROOT%\web\frontend\node_modules" (
  echo [!] Frontend node_modules missing.
  echo     Run scripts\setup.bat once first.
  echo.
  pause
  exit /b 1
)

REM --- free ports ---
echo [1/3] checking ports...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":%BACKEND_PORT% "') do (
  echo     killing existing backend pid %%P on :%BACKEND_PORT%
  taskkill /F /PID %%P >nul 2>nul
)
for /f "tokens=5" %%P in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":%FRONTEND_PORT% "') do (
  echo     killing existing frontend pid %%P on :%FRONTEND_PORT%
  taskkill /F /PID %%P >nul 2>nul
)

REM --- launch helper scripts in new windows (no nested-quote headaches) ---
echo [2/3] starting backend on :%BACKEND_PORT%...
start "vae backend" "%SCRIPT_DIR%_run-backend.bat"

echo [3/3] starting frontend on :%FRONTEND_PORT%...
start "vae frontend" "%SCRIPT_DIR%_run-frontend.bat"

echo.
echo Waiting a few seconds for servers to warm up...
timeout /t 6 /nobreak >nul

echo Opening browser: %FRONTEND_URL%
start "" "%FRONTEND_URL%"

echo.
echo ============================================================
echo   READY
echo ============================================================
echo   Two extra terminal windows opened:
echo     - "vae backend"  : Python / FastAPI server
echo     - "vae frontend" : Next.js dev server
echo.
echo   To stop everything: close those two windows
echo                       OR run  scripts\stop-editor.bat
echo.
echo   You can close THIS window now.
echo ============================================================
timeout /t 4 /nobreak >nul
endlocal
