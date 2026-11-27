@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python scripts\run_app.py %*
) else (
  py -3 scripts\run_app.py %*
)
endlocal
