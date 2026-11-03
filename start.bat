@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto run
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 -m venv .venv
if errorlevel 1 goto error
goto install
:usepython
python -m venv .venv
if errorlevel 1 goto error
:install
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
:run
.venv\Scripts\python.exe -c "import pygame" >nul 2>nul
if errorlevel 1 goto install
.venv\Scripts\python.exe main.py
if errorlevel 1 goto error
exit /b 0
:error
echo Launch failed. See the error above. Python 3.10+ and Internet are needed for first setup.
pause
exit /b 1
