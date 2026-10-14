@echo off
rem VFS with several files including a binary one
cd /d "%~dp0.."
python tools\make_vfs.py > NUL
(echo vfs-info& echo exit) | run.bat --vfs build\vfs\multi.zip
echo exit code: %ERRORLEVEL%
