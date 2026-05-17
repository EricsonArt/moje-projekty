@echo off
REM Instalator pipeline'u dla Windows. Uruchom raz, na poczatku.
REM Wymagania wstepne: Python 3.11+ zainstalowany (sprawdz: python --version)

setlocal
cd /d "%~dp0\.."

echo === Viral Content Engine - Installer ===
echo.

echo [1/4] Sprawdzam Python...
python --version
if errorlevel 1 (
    echo BLAD: Python nie jest zainstalowany lub nie jest w PATH.
    echo Pobierz Python 3.11+ z https://www.python.org/downloads/
    echo WAZNE: podczas instalacji zaznacz "Add Python to PATH".
    pause
    exit /b 1
)

echo.
echo [2/4] Tworze virtualenv ".venv"...
if not exist ".venv" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat

echo.
echo [3/4] Instaluje zaleznosci (yt-dlp, llm clients, telegram, ...)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo BLAD: instalacja pakietow padla. Sprawdz polaczenie internetowe.
    pause
    exit /b 1
)

echo.
echo [4/4] Sprawdzam czy .env istnieje...
if not exist ".env" (
    copy .env.example .env >nul
    echo Utworzono .env z .env.example
    echo.
    echo TERAZ EDYTUJ plik .env i wpisz swoje 4 klucze:
    echo   - GEMINI_API_KEY
    echo   - GROQ_API_KEY
    echo   - TELEGRAM_BOT_TOKEN
    echo   - TELEGRAM_CHAT_ID
) else (
    echo Plik .env juz istnieje - zostawiam.
)

echo.
echo ======================================
echo Instalacja zakonczona. Co dalej:
echo  1. Edytuj plik .env (wpisz klucze API)
echo  2. Edytuj plik data\swipe-file.txt (wklej linki do kanalow)
echo  3. Jezeli uzywasz TT/IG: wrzuc cookies do data\cookies\ (patrz tamtejsze README.txt)
echo  4. Uruchom windows\run-once.bat zeby przetestowac
echo  5. Uruchom windows\install-autostart.bat zeby pipeline odpalal sie sam przy logowaniu
echo ======================================
pause
