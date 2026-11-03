@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 -m venv .build-venv
goto install
:usepython
python -m venv .build-venv
:install
if errorlevel 1 goto error
.build-venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto error
.build-venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --onedir --name WolfVsRabbit --add-data "assets;assets" main.py
if errorlevel 1 goto error
echo Ready: dist\WolfVsRabbit\WolfVsRabbit.exe
pause
exit /b 0
:error
echo Build failed. See error above.
pause
exit /b 1
