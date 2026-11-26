@echo off
setlocal
set "EXAM_DEMO_MODE=1"
call "%~dp0start-astra.bat"
exit /b %errorlevel%
