@echo off
rem cbm-init Windows launcher alias
setlocal
set SCRIPT_DIR=%~dp0
python "%SCRIPT_DIR%agent-harness" init %*
endlocal
