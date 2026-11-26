@echo off
setlocal
set "ROOT=%~dp0"
set "PYTHON="
if exist "%ROOT%.venv-agent-ui\Scripts\python.exe" set "PYTHON=%ROOT%.venv-agent-ui\Scripts\python.exe"
if not defined PYTHON if exist "%ROOT%.venv-win\Scripts\python.exe" set "PYTHON=%ROOT%.venv-win\Scripts\python.exe"
if not defined PYTHON if exist "%ROOT%.venv\Scripts\python.exe" set "PYTHON=%ROOT%.venv\Scripts\python.exe"
if not defined PYTHON set "PYTHON=python"

cd /d "%ROOT%" || exit /b 1
if not exist "astra-frontend\node_modules\.bin\vite.cmd" (
    call npm.cmd --prefix astra-frontend ci
    if errorlevel 1 exit /b 1
)
call npm.cmd --prefix astra-frontend run build
if errorlevel 1 exit /b 1

if not defined ASTRA_PORT set "ASTRA_PORT=8000"
echo Open http://127.0.0.1:%ASTRA_PORT%/ after startup. Press Ctrl+C to stop.
"%PYTHON%" -m uvicorn exam_baseline.api.app:create_web_app --factory --app-dir src --host 127.0.0.1 --port "%ASTRA_PORT%"
exit /b %errorlevel%
