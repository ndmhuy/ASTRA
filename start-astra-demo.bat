@echo off
setlocal
set "EXAM_DEMO_MODE=1"
set "EXAM_PROVIDER=mock"
set "EXAM_MODEL=mock-fixture-v1"
set "ASTRA_AGENT_ENABLED=false"
call "%~dp0start-astra.bat"
exit /b %errorlevel%
