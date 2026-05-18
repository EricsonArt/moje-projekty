@echo off
REM Odpalenie pipeline'u raz. Wywoluj recznie LUB z Task Schedulera.

setlocal
cd /d "%~dp0\.."

REM Aktywuj virtualenv
if not exist ".venv\Scripts\activate.bat" (
    echo BLAD: brak virtualenv. Uruchom najpierw windows\install.bat
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat

REM Log do pliku + ekran
set "LOG_DIR=logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\run-%date:~-4%-%date:~3,2%-%date:~0,2%.log"

echo === Run started: %date% %time% === >> "%LOG_FILE%"
python -m src.main 2>&1 | tee -a "%LOG_FILE%" 2>nul
if errorlevel 1 (
    REM tee na Windows moze nie byc - fallback bez tee
    python -m src.main >> "%LOG_FILE%" 2>&1
)
set EXIT_CODE=%errorlevel%
echo === Run finished: %date% %time% (exit=%EXIT_CODE%) === >> "%LOG_FILE%"

if "%1"=="--no-pause" goto end
echo.
echo Log zapisany do: %LOG_FILE%
pause
:end
exit /b %EXIT_CODE%
