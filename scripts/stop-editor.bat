@echo off
REM ===========================================================
REM  video-auto-editor — Stop running servers
REM ===========================================================

setlocal
set BACKEND_PORT=8000
set FRONTEND_PORT=3000

echo.
echo Stopping vae backend (port %BACKEND_PORT%) and frontend (port %FRONTEND_PORT%)...

for /f "tokens=5" %%P in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":%BACKEND_PORT% "') do (
  echo   killing pid %%P
  taskkill /F /PID %%P >nul 2>nul
)
for /f "tokens=5" %%P in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":%FRONTEND_PORT% "') do (
  echo   killing pid %%P
  taskkill /F /PID %%P >nul 2>nul
)

REM also close the named cmd windows we opened from open-editor.bat
taskkill /F /FI "WINDOWTITLE eq vae backend*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq vae frontend*" >nul 2>nul

echo.
echo Done. (You can close this window.)
timeout /t 3 /nobreak >nul
endlocal
