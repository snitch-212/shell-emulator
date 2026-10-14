@echo off
rem VFS with 3+ nesting levels: load, vfs-save, reload the copy
cd /d "%~dp0.."
python tools\make_vfs.py > NUL
(echo vfs-info& echo vfs-save build\deep-copy.zip& echo exit) | run.bat --vfs build\vfs\deep.zip
echo exit code: %ERRORLEVEL%
echo === reload saved copy ===
(echo vfs-info /projects& echo exit) | run.bat --vfs build\deep-copy.zip
echo exit code: %ERRORLEVEL%
