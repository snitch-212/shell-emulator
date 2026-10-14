@echo off
rem Minimal VFS: a single file
cd /d "%~dp0.."
python tools\make_vfs.py > NUL
(echo vfs-info& echo exit) | run.bat --vfs build\vfs\minimal.zip
echo exit code: %ERRORLEVEL%
