@echo off
REM Rejestruje pipeline w Windows Task Scheduler do uruchomienia przy logowaniu uzytkownika.
REM Po pierwszym uruchomieniu pipeline odpali sie sam ~30 sekund po zalogowaniu sie do Windowsa.

setlocal
cd /d "%~dp0\.."
set "PROJECT_DIR=%cd%"
set "TASK_NAME=ViralContentEngine_Daily"
set "RUN_SCRIPT=%PROJECT_DIR%\windows\run-once.bat"

echo === Rejestracja zadania w Task Scheduler ===
echo Task: %TASK_NAME%
echo Skrypt: %RUN_SCRIPT%
echo Trigger: przy zalogowaniu sie uzytkownika
echo.

REM Usun stary jezeli istnieje
schtasks /Query /TN "%TASK_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo Stare zadanie istnieje - usuwam...
    schtasks /Delete /TN "%TASK_NAME%" /F >nul
)

REM Stworz nowe: trigger ONLOGON, opoznienie 30s, najwyzszy priorytet
schtasks /Create /TN "%TASK_NAME%" ^
    /TR "\"%RUN_SCRIPT%\" --no-pause" ^
    /SC ONLOGON ^
    /DELAY 0000:30 ^
    /RL HIGHEST ^
    /F

if errorlevel 1 (
    echo.
    echo BLAD przy rejestracji zadania.
    echo Mozliwe przyczyny:
    echo  - brak uprawnien (uruchom jako Administrator: prawy klik bat-a -^> "Uruchom jako administrator")
    echo  - inna restrykcja systemu
    pause
    exit /b 1
)

echo.
echo OK. Zadanie zarejestrowane.
echo Od teraz: po kazdym zalogowaniu sie do Windowsa, ~30s pozniej, pipeline odpali sie automatycznie.
echo Po 5-10 min dostaniesz skrypty na Telegram.
echo.
echo Zeby sprawdzic: Start -^> wpisz "Task Scheduler" -^> Task Scheduler Library -^> znajdz "%TASK_NAME%"
echo Zeby USUNAC: uruchom windows\uninstall-autostart.bat
pause
