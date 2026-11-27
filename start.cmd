@echo off
setlocal
cd /d "%~dp0"
if exist ".venv-win\Scripts\python.exe" (
  ".venv-win\Scripts\python.exe" scripts\run_app.py %*
  exit /b
)
where py >nul 2>nul
if errorlevel 1 (
  python scripts\run_app.py %*
) else (
  py -3.11 scripts\run_app.py %*
)
endlocal
