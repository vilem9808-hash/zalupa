@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 launcher.py
goto finished
:usepython
python launcher.py
:finished
if not errorlevel 1 exit /b 0
echo Please read the error above.
pause
exit /b 1
