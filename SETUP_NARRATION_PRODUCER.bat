@echo off
setlocal
cd /d "%~dp0"
set "TOOL=%~dp0tools\narration-producer"
where py >nul 2>nul && (set "PY=py -3") || (where python >nul 2>nul && set "PY=python")
if not defined PY (
 echo Python 3 is unavailable. Install Python 3 for Windows, then run this setup again.
 pause & exit /b 1
)
%PY% --version 2>nul | findstr /R "Python 3\." >nul || (echo Python 3 is required.& pause & exit /b 1)
if not exist "%TOOL%\.venv\Scripts\python.exe" %PY% -m venv "%TOOL%\.venv"
if errorlevel 1 (echo The private environment could not be created.& pause & exit /b 1)
"%TOOL%\.venv\Scripts\python.exe" -m pip install -r "%TOOL%\requirements.txt"
if errorlevel 1 (echo Requirements could not be installed. Check your internet connection.& pause & exit /b 1)
if not exist "%TOOL%\.env" copy "%TOOL%\.env.example" "%TOOL%\.env" >nul
findstr /X /C:"ELEVENLABS_API_KEY=" "%TOOL%\.env" >nul && (
 echo Paste your key after the equals sign exactly like this: ELEVENLABS_API_KEY=...
 start "" notepad.exe "%TOOL%\.env"
)
echo Setup is complete and is safe to run again.
pause
