@echo off
setlocal
cd /d "%~dp0"
if exist ".venv-win\Scripts\python.exe" (
  ".venv-win\Scripts\python.exe" scripts\run_app.py %*
  exit /b
)
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" scripts\run_app.py %*
  exit /b
)
py -3.11 -c "import sys; assert sys.version_info[:2] == (3, 11)" >nul 2>nul
if not errorlevel 1 (
  py -3.11 scripts\run_app.py %*
  exit /b
)
python -c "import sys; assert sys.version_info[:2] == (3, 11)" >nul 2>nul
if not errorlevel 1 (
  python scripts\run_app.py %*
  exit /b
)
echo Install CPython 3.11 and Node.js 24 or newer, then run start.cmd again.
exit /b 1
