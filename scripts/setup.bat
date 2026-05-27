@echo off
REM ===========================================================
REM  video-auto-editor — First-time setup (Windows)
REM  Run me once before open-editor.bat.
REM ===========================================================

setlocal
cd /d "%~dp0\.."
set ROOT=%CD%

title video-auto-editor setup

echo.
echo ============================================================
echo   video-auto-editor   first-time setup
echo ============================================================
echo.

REM --- check Python ---
python --version >nul 2>nul
if errorlevel 1 (
  echo [!] Python not found on PATH.
  echo     Install Python 3.10+ from https://www.python.org/
  echo.
  pause
  exit /b 1
)

REM --- check Node ---
node --version >nul 2>nul
if errorlevel 1 (
  echo [!] Node.js not found on PATH.
  echo     Install Node 20+ from https://nodejs.org/
  echo.
  pause
  exit /b 1
)

REM --- check ffmpeg ---
ffmpeg -version >nul 2>nul
if errorlevel 1 (
  echo [!] FFmpeg not found on PATH.
  echo     Run in a new shell:  winget install Gyan.FFmpeg
  echo     Then open a fresh terminal and rerun this setup.
  echo.
  pause
  exit /b 1
)

REM --- venv ---
if not exist "%ROOT%\.venv\Scripts\python.exe" (
  echo [1/3] creating Python venv at .venv ...
  python -m venv .venv
  if errorlevel 1 (
    echo [!] venv creation failed.
    pause
    exit /b 1
  )
) else (
  echo [1/3] venv already exists, skipping.
)

REM --- pip deps ---
echo [2/3] installing Python deps (pydantic, fastapi, uvicorn, ffmpeg-python, ...)
"%ROOT%\.venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
"%ROOT%\.venv\Scripts\python.exe" -m pip install --quiet pydantic pytest click
"%ROOT%\.venv\Scripts\python.exe" -m pip install --quiet -r "%ROOT%\web\backend\requirements.txt"
if errorlevel 1 (
  echo [!] pip install failed.
  pause
  exit /b 1
)

REM --- node deps ---
echo [3/3] installing frontend deps (npm install)...
cd /d "%ROOT%\web\frontend"
call npm install --no-audit --no-fund --loglevel=error
if errorlevel 1 (
  echo [!] npm install failed.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo   SETUP COMPLETE
echo ============================================================
echo   Next: double-click  scripts\open-editor.bat
echo ============================================================
echo.
pause
endlocal
