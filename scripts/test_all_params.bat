@echo off
rem Check all parameters together, help and unknown parameter
cd /d "%~dp0.."
echo === --vfs and --script together ===
call run.bat --vfs vfs\example.zip --script examples\exit_code.txt
echo exit code: %ERRORLEVEL%
echo === --help ===
call run.bat --help
echo exit code: %ERRORLEVEL%
echo === unknown parameter ===
call run.bat --colour red < NUL
echo exit code: %ERRORLEVEL%
