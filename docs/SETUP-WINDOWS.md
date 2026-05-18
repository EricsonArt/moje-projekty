# Setup Windows - krok po kroku

System dziala lokalnie na Twoim PC. Codziennie po zalogowaniu sie do Windowsa
pipeline odpala sie automatycznie i 5-10 min pozniej dostajesz skrypty na Telegram.

**Czas calego setupu: 30-45 min jednorazowo.**

---

## Czego potrzebujesz

- Komputer z Windows 10 lub 11
- Konto Telegram
- Konta Google, TikTok, Instagram (zalogowane w przegladarce)
- Chrome / Edge / Firefox

---

## KROK 1: Zainstaluj Python (5 min)

1. Wejdz na **https://www.python.org/downloads/**
2. Klik wielki zolty przycisk **"Download Python 3.12.x"**
3. Uruchom instalator
4. **WAZNE - na pierwszym ekranie ZAZNACZ kratke "Add python.exe to PATH"** (na samym dole okna)
5. Klik **"Install Now"** -> czekaj az skonczy -> **"Close"**

Sprawdz czy dziala:
- Wcisnij `Win+R` -> wpisz `cmd` -> Enter
- W oknie wpisz `python --version` i Enter
- Powinno wyswietlic `Python 3.12.x`

Jezeli pisze "python nie jest rozpoznawana komenda" - zainstaluj jeszcze raz i ZAZNACZ kratke z PATH.

---

## KROK 2: Pobierz projekt na PC (3 min)

**Opcja A (latwiejsza) - bez gita:**
1. Wejdz na repo na GitHub: `https://github.com/EricsonArt/moje-projekty`
2. Przelacz branch na `claude/viral-content-system-0Ksu3` (przycisk lewy gora)
3. Zielony przycisk **"Code"** -> **"Download ZIP"**
4. Rozpakuj na np. `C:\skala-viral`

**Opcja B - z gitem (jezeli umiesz):**
```
git clone https://github.com/EricsonArt/moje-projekty.git C:\skala-viral
cd C:\skala-viral
git checkout claude/viral-content-system-0Ksu3
```

---

## KROK 3: Zdobadz 4 klucze API (15 min)

To te same klucze co przy wersji chmurowej. Wszystkie darmowe.

### 3.1 Gemini
1. Wejdz na **https://aistudio.google.com/apikey** -> zaloguj Gmailem
2. Klik **"Create API key"** -> skopiuj klucz `AIza...`

### 3.2 Groq
1. Wejdz na **https://console.groq.com/keys** -> zarejestruj (Google login)
2. Klik **"Create API Key"** -> nazwij "skala" -> skopiuj klucz `gsk_...`

### 3.3 Telegram bot
1. W Telegramie wyszukaj **@BotFather** (niebieska odznaczka)
2. Napisz `/newbot`, wymysl nazwe (np. "Skala Viral"), username (np. `skala_viral_bot`)
3. Skopiuj token postaci `1234567890:ABCdef...`
4. **WAZNE**: otworz Twojego bota w Telegramie i napisz mu "test" (musi odebrac pierwsza wiadomosc od Ciebie)

### 3.4 Twoj chat_id
1. W Telegramie wyszukaj **@userinfobot** -> napisz `/start`
2. Skopiuj liczbe ktora zwroci (np. `123456789`)

---

## KROK 4: Uruchom instalator (3 min)

1. Otworz folder z projektem (`C:\skala-viral` albo gdzie masz)
2. Wejdz do folderu `windows`
3. Podwojny klik na **`install.bat`**
4. Czekaj az skonczy (instaluje yt-dlp i pakiety Pythona, ~2 min)
5. Naciśnij dowolny klawisz zeby zamknac

Skrypt utworzy plik `.env` w folderze projektu.

---

## KROK 5: Wpisz klucze do .env (3 min)

1. W folderze projektu znajdz plik **`.env`** (kropka na poczatku, bez rozszerzenia)
2. Otworz w Notatniku (prawy klik -> "Otworz za pomoca" -> Notatnik)
3. Wpisz Twoje klucze w odpowiednie miejsca:
```
GEMINI_API_KEY=AIza...
GROQ_API_KEY=gsk_...
TELEGRAM_BOT_TOKEN=1234567890:ABCdef...
TELEGRAM_CHAT_ID=123456789
```
4. **Zapisz** (Ctrl+S) i zamknij

---

## KROK 6: Wyeksportuj cookies dla TikToka i Instagrama (10 min)

Pipeline musi byc "zalogowany" Twoim kontem zeby scrape'owac TT/IG. Robimy to przez
eksport ciasteczek z przegladarki.

### 6.1 Zainstaluj rozszerzenie

W Chrome / Edge / Firefox zainstaluj **"Get cookies.txt LOCALLY"**:
- Chrome: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
- Firefox: szukaj w sklepie dodatkow

**UWAGA**: musi byc wersja z **"LOCALLY"** w nazwie - inne wersje wysylaja Twoje cookies przez internet (NIEBEZPIECZNE).

### 6.2 Wyeksportuj cookies TikToka

1. Wejdz na **tiktok.com**, zaloguj sie (jezeli juz nie jestes)
2. Bedac na tiktok.com klik ikonke rozszerzenia (gora po prawej, ciasteczko)
3. Klik **"Export As" -> "Netscape"** (pobierze plik `tiktok.com_cookies.txt`)
4. Zmien nazwe pliku na **`tiktok.txt`**
5. Wrzuc do folderu **`data\cookies\`** w projekcie

### 6.3 Wyeksportuj cookies Instagrama

1. Wejdz na **instagram.com**, zaloguj sie
2. Klik ikonke rozszerzenia -> **"Export As" -> "Netscape"**
3. Zmien nazwe na **`instagram.txt`**
4. Wrzuc do **`data\cookies\`**

### Bezpieczenstwo
- Folder `data\cookies\` jest w `.gitignore` - NIGDY nie idzie na GitHuba
- Cookies = sesja logowania. Nie wysylaj nikomu tych plikow
- Odswiezaj co 1-2 tygodnie (TT/IG czasem wygasaja sesje)

### Polecenie
Zaloz drugie konto "obserwacyjne" na TT i IG (5 min na telefonie), zaloguj sie nim
w przegladarce i to jego cookies daj systemowi. Jezeli kiedys konto dostanie ostrzezenie
od platformy - nie bedzie to Twoje glowne konto.

---

## KROK 7: Wpisz linki do kanalow (5 min)

1. Otworz plik **`data\swipe-file.txt`** w Notatniku
2. Usun przykladowe linki (te z `#` na poczatku) lub dodaj swoje pod nimi (bez `#`)
3. Wklej **3-10 linkow** do kanalow z Twojej niszy:

```
# === Moje kanaly ===
https://www.youtube.com/@nazwa_yt_kanalu
https://www.tiktok.com/@nazwa_tt_kanalu
https://www.instagram.com/nazwa_ig_kanalu

# Mozesz tez wkleic pojedyncze filmy (bez auto-filtru views):
https://youtube.com/shorts/abc123
https://www.tiktok.com/@nazwa/video/1234567
https://www.instagram.com/reel/ABC123/
```

4. Zapisz (Ctrl+S)

**Jak wybrac kanaly:** wejdz na TT/IG/YT, znajdz tworcow z Twojej niszy ktorych shorty
regularnie maja viralowe zasiegi (>500k views na YT, duzo na TT/IG). 3-5 kanalow na start
spokojnie wystarczy.

---

## KROK 8: Test - odpal pipeline raz recznie (5 min)

1. W folderze projektu wejdz do `windows`
2. Podwojny klik na **`run-once.bat`**
3. Otworzy sie czarne okno - czekasz 5-10 minut
4. W oknie zobaczysz duzo logow - normalne. Pod koniec powinno byc cos jak:
   ```
   Delivered 3 scripts to Telegram chat ...
   Done. Output: scripts/2026-MM-DD/
   ```
5. Sprawdz Telegrama - powinienes miec 1 summary + 3 wiadomosci ze skryptami
6. Sprawdz folder `scripts\2026-MM-DD\` - sa 3 pliki .md

**Jezeli cos nie zadzialalo** - zobacz log w folderze `logs\` i zobacz Troubleshooting na dole.

---

## KROK 9: Wlacz automatyczne uruchamianie (3 min)

Jezeli dziala test, podepnij to do startu Windowsa:

1. W folderze `windows` znajdz **`install-autostart.bat`**
2. **Prawy klik** -> **"Uruchom jako administrator"** (wazne!)
3. Powinno wyswietlic "OK. Zadanie zarejestrowane."
4. Naciśnij dowolny klawisz zeby zamknac

Od teraz: **przy kazdym zalogowaniu sie do Windowsa, ~30s pozniej pipeline odpala sie sam**.
Pojawi sie krotko czarne okno - normalne, znika po chwili. Skrypty leca na Telegram po 5-10 min.

**Zeby wylaczyc:** uruchom `windows\uninstall-autostart.bat`.

---

## Co teraz robisz codziennie

- Wlaczasz PC rano
- Po 5-10 min Telegram pika
- 3 gotowe skrypty do nagrania talking-head
- Co 2-3 tygodnie odswiezasz kanaly w `data\swipe-file.txt` (zmieniasz pulę inspiracji)
- Co 1-2 tygodnie odswiezasz cookies TT/IG (jak sesja wygasa)

---

## Troubleshooting

### "yt-dlp nie znaleziono"
Uruchom ponownie `windows\install.bat`. Sprawdz czy nie ma bledow w czerwonym tekscie.

### "No cookies for tiktok / instagram"
Sprawdz czy plik `data\cookies\tiktok.txt` istnieje i jest niepustym plikiem.
Sprawdz nazwe pliku (musi byc dokladnie `tiktok.txt`, nie `tiktok_cookies.txt`).

### "Login required" / "Cookies expired"
Sesja TT/IG wygasla. Wejdz na strone, zaloguj sie ponownie, wyeksportuj cookies od nowa,
nadpisz plik.

### "No usable transcripts" dla YT
Wybrane Shorty nie maja auto-subow PL. Wpisz w `data\swipe-file.txt` inne kanaly
albo dorzuc kilka pojedynczych linkow do shortow PL ktore wiesz ze maja podpisy.

### "Zero shorts >= 500000 views" dla YT
Kanaly w swipe-file sa za male. Dodaj do `.env`:
```
CHANNEL_MIN_VIEWS=100000
```
i zapisz. Albo dodaj wieksze kanaly.

### Telegram nie dostaje wiadomosci
- Czy wyslales botowi cokolwiek? (musi byc handshake)
- Czy `TELEGRAM_CHAT_ID` to liczba (Twoj id), nie nazwa bota?
- Sprawdz log w `logs\run-*.log` na koncu jest linia "Telegram" - co tam pisze?

### Pipeline odpala sie, ale 0 skryptow
Sprawdz log. Najprawdopodobniej:
- Wszystkie kanaly TT/IG bez cookies -> dodaj cookies LUB tylko YT
- Wszystkie YT kanaly ponizej `CHANNEL_MIN_VIEWS` -> obniz prog

### Chce zmienic godzine uruchomienia
Domyslnie pipeline odpala sie 30s po **zalogowaniu sie do Windowsa**. Jezeli chcesz np.
codziennie o 7:00 (niezaleznie od logowania): otworz Task Scheduler -> znajdz
`ViralContentEngine_Daily` -> Properties -> Triggers -> zmien z "At log on" na "Daily 07:00".

---

## Co system NIE robi

- Nie nagra filmu (musisz nagrac talking-head)
- Nie zmontuje (CapCut 10 min)
- Nie zagwarantuje virala (realistic 1/20-30 trafia)
- Nie wykryje trending audio TT (nie ma takiego API publicznego)
