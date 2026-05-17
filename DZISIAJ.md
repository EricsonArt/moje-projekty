# Co zrobic teraz (TT/IG, lokalnie)

**Czas: 10-15 min. Bez instalacji niczego z palca.**

---

## 1. Pobierz repo

Wejdz na: **https://github.com/EricsonArt/moje-projekty/archive/refs/heads/claude/viral-content-system-0Ksu3.zip**

Zapisuje sie ZIP. Rozpakuj go np. na pulpicie. Otworz rozpakowany folder.

(Wewnatrz powinienes widziec foldery: `src`, `windows`, `data`, plus pliki .md.)

---

## 2. Zainstaluj Pythona (jezeli nie masz)

Sprawdz czy masz: w Start menu wpisz `cmd` -> Enter -> w czarnym oknie napisz `python --version`.

- Jezeli pokaze "Python 3.11.x" lub wyzej - **masz, idz do kroku 3**.
- Jezeli pokaze "nie rozpoznano" - pobierz: **https://www.python.org/downloads/**
  - **WAZNE**: na pierwszym ekranie zaznacz kratke **"Add python.exe to PATH"**
  - Klik "Install Now"

---

## 3. Odpal START.bat

W rozpakowanym folderze wejdz do podfolderu **`windows`** i **podwojny klik** na **`START.bat`**.

Skrypt sam:
1. Zainstaluje pakiety (~2 min)
2. Otworzy plik `.env` w Notatniku - wpisz tam 4 klucze ktore masz (Gemini, Groq, Telegram token, Telegram chat_id), zapisz (Ctrl+S), zamknij
3. Otworzy `data\swipe-file.txt` w Notatniku - **TT/IG kanaly juz tam masz, zostaw**, zapisz, zamknij
4. Powie ze potrzebne cookies (jak masz TT/IG kanaly) - otworzy sklep Chrome z rozszerzeniem + folder gdzie wrzucic

---

## 4. Cookies (najwazniejsze!)

Skrypt sam Ci to pokaze, ale w skrocie:

1. W Chrome zainstaluj rozszerzenie **"Get cookies.txt LOCALLY"** (link otworzy sie sam)
2. Wejdz na **tiktok.com** w przegladarce -> upewnij sie ze jestes **zalogowany**
3. Klik ikonke rozszerzenia (gora prawo) -> **"Export As"** -> **"Netscape"**
4. Zapisany plik nazywa sie `tiktok.com_cookies.txt` lub podobnie - **zmien nazwe na `tiktok.txt`**
5. Wrzuc do folderu `data\cookies\` ktory skrypt sam otworzy

Powtorz dla Instagrama: zaloguj sie na instagram.com, eksport, nazwa `instagram.txt`, wrzuc.

**REKOMENDACJA SECURITY:** Uzywaj DRUGIEGO konta TT/IG (zalozysz je w 2 min), nie glownego. Glowne konto mozes stracic jak platforma uzna to za bota.

---

## 5. Wracaj do START.bat

Po wrzuceniu cookies - nacisnij Enter w czarnym oknie. Pipeline ruszy.

Po 5-10 min: **3 skrypty na Telegramie**.

---

## Kolejne uruchomienia

Wystarczy znowu podwojnie kliknac `windows\START.bat`. Wszystko zapamietane.

Mozesz tez ustawic zeby odpalal sie sam codziennie - wtedy uruchom raz `windows\install-autostart.bat` jako administrator (prawy klik -> Uruchom jako administrator).
