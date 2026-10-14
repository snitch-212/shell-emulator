@echo off
rem Run the emulator: run.bat [emulator options]
set "PYTHONPATH=%~dp0src"
rem Test VFS archives are generated on first launch (stage 3 and later)
if exist "%~dp0tools\make_vfs.py" if not exist "%~dp0build\vfs\deep.zip" python "%~dp0tools\make_vfs.py" "%~dp0build\vfs" > NUL
python -m shell_emulator %*
