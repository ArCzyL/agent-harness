@echo off
rem agent-harness Windows launcher
setlocal
set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%agent-harness" %*
endlocal
