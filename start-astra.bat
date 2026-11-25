@echo off
setlocal
set "ROOT=%~dp0"
set "PYTHON="
if exist "%ROOT%.venv-agent-ui\Scripts\python.exe" set "PYTHON=%ROOT%.venv-agent-ui\Scripts\python.exe"
if not defined PYTHON if exist "%ROOT%.venv-win\Scripts\python.exe" set "PYTHON=%ROOT%.venv-win\Scripts\python.exe"
if not defined PYTHON if exist "%ROOT%.venv\Scripts\python.exe" set "PYTHON=%ROOT%.venv\Scripts\python.exe"
if not defined PYTHON set "PYTHON=python"

echo Using Python: %PYTHON%
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING" /C:":5173 .*LISTENING"') do taskkill /F /PID %%a >nul 2>&1
start "ASTRA Backend (8000)" /D "%ROOT%" cmd /k ""%PYTHON%" -m uvicorn exam_baseline.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir "%ROOT%src""
start "ASTRA Frontend (Vite)" /D "%ROOT%astra-frontend" cmd /k "npm.cmd run dev -- --host 127.0.0.1"

echo.
echo ASTRA is starting in two windows:
echo   Backend : http://127.0.0.1:8000
echo   Frontend: http://127.0.0.1:5173
echo.
pause
