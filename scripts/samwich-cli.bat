@echo off
setlocal
set PYTHONPATH=%~dp0
set script_dir=%~dp0
set script_path=%script_dir%entrypoint.py
python %script_path% %*
endlocal
