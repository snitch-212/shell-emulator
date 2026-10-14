@echo off
rem Check --script: comments and errors, exit, missing file
cd /d "%~dp0.."
echo === --script with comments and errors ===
call run.bat --script examples\stage2.txt < NUL
echo exit code: %ERRORLEVEL%
echo === --script with exit 3 ===
call run.bat --script examples\exit_code.txt < NUL
echo exit code: %ERRORLEVEL%
echo === --script: file does not exist ===
call run.bat --script examples\missing.txt < NUL
echo exit code: %ERRORLEVEL%
