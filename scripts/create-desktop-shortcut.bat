@echo off
REM Create a desktop shortcut named "video-auto-editor" that runs open-editor.bat.

setlocal
cd /d "%~dp0\.."
set ROOT=%CD%
set TARGET=%ROOT%\scripts\open-editor.bat
set ICON_DIR=%ROOT%\scripts
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT=%DESKTOP%\video-auto-editor.lnk

echo Creating shortcut on Desktop -> %SHORTCUT%

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%TARGET%'; $s.WorkingDirectory = '%ROOT%'; $s.WindowStyle = 1; $s.Description = 'Open the video-auto-editor GUI in your browser'; $s.Save()"

if exist "%SHORTCUT%" (
  echo Done. Desktop shortcut created.
) else (
  echo [!] Failed to create shortcut.
)
echo.
pause
endlocal
