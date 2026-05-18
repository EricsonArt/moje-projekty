@echo off
REM Jeden skrypt do uruchomienia wszystkiego.
REM Dziala jako: installer (pierwszy raz) + runner (kolejne razy).

setlocal enabledelayedexpansion
cd /d "%~dp0\.."
set "PROJECT_DIR=%cd%"

echo.
echo ====================================================
echo   VIRAL CONTENT ENGINE - Start
echo ====================================================
echo.

REM === 1. Sprawdz Python ===
python --version >nul 2>&1
if errorlevel 1 (
    echo [BLAD] Python nie jest zainstalowany.
    echo.
    echo Otwieram strone python.org w przegladarce.
    echo Pobierz i zainstaluj Python 3.11+ ZAZNACZAJAC "Add to PATH" na pierwszym ekranie.
    echo Po instalacji uruchom ten skrypt jeszcze raz.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python zainstalowany.

REM === 2. Venv ===
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Tworze srodowisko virtualenv (pierwszy raz, ~30 sek)...
    python -m venv .venv
    if errorlevel 1 (
        echo [BLAD] Nie udalo sie stworzyc venv.
        pause
        exit /b 1
    )
)
call .venv\Scripts\activate.bat

REM === 3. Instalacja zaleznosci ===
if not exist ".venv\.deps_installed" (
    echo [INFO] Instaluje pakiety Python (pierwszy raz, ~2 min)...
    python -m pip install --upgrade pip >nul 2>&1
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [BLAD] Instalacja pakietow padla.
        pause
        exit /b 1
    )
    type nul > .venv\.deps_installed
)
echo [OK] Zaleznosci zainstalowane.

REM === 4. Plik .env ===
if not exist ".env" (
    copy .env.example .env >nul
    echo.
    echo [WAZNE] Stworzylem plik .env - musisz wpisac 4 klucze API.
    echo Otwieram go w Notatniku - wklej:
    echo   GEMINI_API_KEY=AIza...
    echo   GROQ_API_KEY=gsk_...
    echo   TELEGRAM_BOT_TOKEN=...
    echo   TELEGRAM_CHAT_ID=...
    echo Zapisz (Ctrl+S), zamknij Notatnik, ten skrypt ruszy dalej.
    echo.
    notepad .env
    pause
)

REM Walidacja .env - czy klucze sa wpisane
findstr /B "GEMINI_API_KEY=AIza" .env >nul
if errorlevel 1 (
    findstr /B "GEMINI_API_KEY=" .env | findstr /V "GEMINI_API_KEY=$" | findstr /V "GEMINI_API_KEY= " >nul
    if errorlevel 1 (
        echo [BLAD] GEMINI_API_KEY pusty w .env - wpisz klucz i uruchom ponownie.
        notepad .env
        pause
        exit /b 1
    )
)
echo [OK] .env z kluczami.

REM === 5. Sprawdz swipe-file ===
findstr /B "https://" data\swipe-file.txt >nul
if errorlevel 1 (
    echo.
    echo [WAZNE] data\swipe-file.txt nie ma aktywnych linkow.
    echo Otwieram w Notatniku - wklej kanaly TT/IG/YT na dole, np:
    echo   https://www.tiktok.com/@nazwa
    echo   https://www.instagram.com/nazwa
    echo Zapisz (Ctrl+S), zamknij Notatnik.
    notepad data\swipe-file.txt
    pause
)

REM === 6. Sprawdz cookies (jak sa linki TT/IG) ===
findstr /B "https://www.tiktok.com" data\swipe-file.txt >nul
set TT_NEEDED=%errorlevel%
findstr /B "https://www.instagram.com" data\swipe-file.txt >nul
set IG_NEEDED=%errorlevel%

if "%TT_NEEDED%"=="0" if not exist "data\cookies\tiktok.txt" (
    echo.
    echo [WAZNE] Masz linki TT w swipe-file, ale brak data\cookies\tiktok.txt
    echo Otwieram instrukcje cookies w przegladarce + folder cookies w Explorerze.
    echo Wyeksportuj cookies z zalogowanej przegladarki, zapisz jako tiktok.txt w tym folderze.
    start "" "data\cookies"
    start https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
    echo.
    echo Po wrzuceniu pliku tiktok.txt - nacisnij dowolny klawisz.
    pause
)

if "%IG_NEEDED%"=="0" if not exist "data\cookies\instagram.txt" (
    echo.
    echo [WAZNE] Masz linki IG w swipe-file, ale brak data\cookies\instagram.txt
    echo Wyeksportuj cookies z zalogowanego instagram.com, zapisz jako instagram.txt w data\cookies\
    start "" "data\cookies"
    echo Po wrzuceniu pliku - nacisnij dowolny klawisz.
    pause
)

REM === 7. URUCHOM ===
echo.
echo ====================================================
echo   Uruchamiam pipeline (5-10 min)...
echo ====================================================
echo.

set "LOG_DIR=logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\run-%date:~-4%-%date:~3,2%-%date:~0,2%-%time:~0,2%%time:~3,2%.log"
set "LOG_FILE=%LOG_FILE: =0%"

python -m src.main 2>&1
set EXIT_CODE=%errorlevel%

echo.
if "%EXIT_CODE%"=="0" (
    echo ====================================================
    echo   SUKCES! Sprawdz Telegrama - powinny byc 3 skrypty.
    echo   Pliki tez zapisane w scripts\
    echo ====================================================
) else (
    echo ====================================================
    echo   BLAD - exit code %EXIT_CODE%. Log powyzej.
    echo   Wyslij screen do Claude'a, zdiagnozuje.
    echo ====================================================
)
echo.
pause
exit /b %EXIT_CODE%
