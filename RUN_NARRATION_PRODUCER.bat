@echo off
setlocal
cd /d "%~dp0"
set "PY=%~dp0tools\narration-producer\.venv\Scripts\python.exe"
if not exist "%PY%" (
 echo Setup has not been completed.
 choice /M "Run setup now"
 if not errorlevel 2 call "%~dp0SETUP_NARRATION_PRODUCER.bat"
)
if not exist "%PY%" (echo Setup is required before the Producer can run.& pause & exit /b 1)
echo Tomb World Narration Producer: http://127.0.0.1:8765
echo Closing this window stops the Producer.
"%PY%" "%~dp0tools\narration-producer\server.py"
echo The Producer has stopped.
pause
