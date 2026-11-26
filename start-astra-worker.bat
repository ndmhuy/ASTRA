@echo off
setlocal
set "ASTRA_AGENT_ENABLED=true"
set "ASTRA_AGENT_TRANSPORT=worker"
set "ASTRA_AGENT_FALLBACK_ENABLED=false"
set "EXAM_DEMO_MODE=1"
set "EXAM_PROVIDER=mock"
set "EXAM_MODEL=mock-fixture-v1"
call "%~dp0start-astra.bat"
exit /b %errorlevel%
