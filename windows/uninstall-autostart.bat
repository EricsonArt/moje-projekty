@echo off
REM Usuwa zadanie z Task Scheduler. Pipeline przestaje odpalac sie sam.

set "TASK_NAME=ViralContentEngine_Daily"

schtasks /Query /TN "%TASK_NAME%" >nul 2>&1
if errorlevel 1 (
    echo Zadanie "%TASK_NAME%" nie istnieje - nic do usuniecia.
    pause
    exit /b 0
)

schtasks /Delete /TN "%TASK_NAME%" /F
if errorlevel 1 (
    echo BLAD przy usuwaniu. Sprobuj jako administrator.
    pause
    exit /b 1
)

echo OK. Zadanie usuniete. Pipeline nie bedzie sie juz odpalal automatycznie.
echo Mozesz nadal odpalac recznie windows\run-once.bat.
pause
