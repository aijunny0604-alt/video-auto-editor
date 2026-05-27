@echo off
REM Internal: run the FastAPI backend. Called by open-editor.bat.
title vae backend
cd /d "%~dp0\.."
set "PYTHONPATH=src"
".venv\Scripts\python.exe" -m uvicorn web.backend.app:app --host 127.0.0.1 --port 8000
pause
