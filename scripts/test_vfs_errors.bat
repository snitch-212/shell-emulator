@echo off
rem VFS loading errors and the default VFS
cd /d "%~dp0.."
python tools\make_vfs.py > NUL
echo === file not found ===
call run.bat --vfs build\vfs\missing.zip < NUL
echo exit code: %ERRORLEVEL%
echo === not a ZIP archive ===
call run.bat --vfs build\vfs\broken.zip < NUL
echo exit code: %ERRORLEVEL%
echo === directory instead of archive ===
call run.bat --vfs build\vfs < NUL
echo exit code: %ERRORLEVEL%
echo === no --vfs: default VFS in memory ===
(echo vfs-info& echo exit) | run.bat
echo exit code: %ERRORLEVEL%
