@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 launcher.py --build
goto finished
:usepython
python launcher.py --build
:finished
if errorlevel 1 goto error
echo Ready: dist\WolfVsRabbit\WolfVsRabbit.exe
pause
exit /b 0
:error
echo Build failed. Please read the error above.
pause
exit /b 1
