@echo off
rem Run the emulator without parameters (empty input)
cd /d "%~dp0.."
echo === no parameters ===
call run.bat < NUL
echo exit code: %ERRORLEVEL%
