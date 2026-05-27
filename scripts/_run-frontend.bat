@echo off
REM Internal: run the Next.js dev server. Called by open-editor.bat.
title vae frontend
cd /d "%~dp0\..\web\frontend"
call npm run dev
pause
