# SETUP - krok po kroku (15-30 min)

Wszystko ponizej jest **darmowe**. Klucze API jednorazowo zakladasz, pozniej dziala
automatycznie.

---

## 1. Klucze API

### 1.1 Gemini (Google AI Studio) - GLOWNY LLM

1. Idz na **https://aistudio.google.com/apikey**
2. Zaloguj sie kontem Google
3. Klik **"Create API key"** -> wybierz dowolny projekt (lub stworz nowy)
4. Skopiuj klucz - zaczyna sie od `AIza...`
5. To bedzie `GEMINI_API_KEY`

Limit: ~250-500 requestow dziennie (wystarcza spokojnie na 3 skrypty/dzien z critic loop).

### 1.2 Groq Cloud - FALLBACK LLM

1. Idz na **https://console.groq.com/keys**
2. Sign up (Github/Google login)
3. Klik **"Create API Key"** -> nazwij np. "skala-viral"
4. Skopiuj klucz - zaczyna sie od `gsk_...`
5. To bedzie `GROQ_API_KEY`

Limit: ~30 requestow/min, 14k tokenow/min. Wystarcza.

### 1.3 Telegram bot - DELIVERY

1. W Telegramie znajdz **@BotFather**
2. Wyslij `/newbot`
3. Wymysl nazwe (np. "Skala Viral Scripts")
4. Wymysl username (musi konczyc sie `_bot`, np. `skala_viral_bot`)
5. BotFather zwroci token postaci `1234567890:ABCdef...`
6. To jest `TELEGRAM_BOT_TOKEN`

Teraz jeszcze potrzebujesz **swojego chat_id**:

1. W Telegramie znajdz **@userinfobot**
2. Wyslij `/start`
3. Bot odpowie cos jak `Id: 123456789`
4. To liczba to jest `TELEGRAM_CHAT_ID`

WAZNE: **wyslij wiadomosc** do swojego nowego bota (`@skala_viral_bot`) - cokolwiek, np. "hi".
Bez tego pierwsza wiadomosc nie przejdzie (Telegram wymaga, zeby user zaczyna konwersacje).

### 1.4 YouTube Data API (OPCJONALNE - tylko Faza 2)

Na razie nie potrzebne. W Fazie 1 uzywamy swipe-file.txt (recznie wklejone linki).

---

## 2. Konfiguracja - lokalnie vs GitHub Actions

### 2.1 Lokalnie (do testow)

```bash
cd /home/user/moje-projekty
cp .env.example .env
```

Edytuj `.env` w edytorze, wklej klucze:

```
GEMINI_API_KEY=AIza...
GROQ_API_KEY=gsk_...
TELEGRAM_BOT_TOKEN=1234567890:ABCdef...
TELEGRAM_CHAT_ID=123456789
```

### 2.2 GitHub Actions (production - codzienny cron)

1. Idz na repo na GitHub -> **Settings** -> **Secrets and variables** -> **Actions**
2. Klik **"New repository secret"** dla kazdego:
   - `GEMINI_API_KEY` = (Twoj klucz Gemini)
   - `GROQ_API_KEY` = (Twoj klucz Groq)
   - `TELEGRAM_BOT_TOKEN` = (Twoj token bota)
   - `TELEGRAM_CHAT_ID` = (Twoj chat_id)
3. Workflow `.github/workflows/daily.yml` automatycznie ich uzywa

---

## 3. Wypelnienie swipe-file.txt (KANALY, nie pojedyncze filmy)

Edytuj `data/swipe-file.txt` i wklej **min 3 linki do KANALOW YT** z Twojej niszy.
System sam pobierze z kazdego kanalu top shorty (>= 500k views domyslnie) i z nich
codziennie wylosuje 3 do inspiracji.

**Jak znalezc dobre kanaly**:
- Idz na YouTube
- Wpisz "AI biznes shorts" / "passive income polska" / "personal brand shorts"
- Wejdz na kilka filmow, klik nazwa kanalu
- Sprawdz w zakladce "Shorts" czy maja regularnie wideo z 500k+ views
- Skopiuj URL kanalu postaci `https://www.youtube.com/@nazwa`

**Format pliku** (1 link na linijke):
```
# komentarz ignorowany
https://www.youtube.com/@kanal1
https://www.youtube.com/@kanal2
https://www.youtube.com/@kanal3
```

**Dostrajanie progu views**:
- Domyslnie pipeline bierze tylko shorty z **>= 500 000 wyswietlen**.
- Jezeli kanaly sa mniejsze i pipeline mowi "zero shorts >= 500000 views" -
  dodaj do .env (lokalnie) lub do GitHub Secrets:
  ```
  CHANNEL_MIN_VIEWS=200000
  ```
- Mozesz tez podniesc do `1000000` dla ostrzejszej selekcji.

**Refresh**: zmieniaj kanaly co 2-3 tygodnie zeby system nie wpadl w 1 styl.

---

## 4. Pierwszy test lokalny

```bash
cd /home/user/moje-projekty
pip install -r requirements.txt
python -m src.main --debug
```

Co powinno sie dziac (logi w terminalu):
1. `Configs loaded` - YAML-e wczytane
2. `Swipe file: 5 links found` - widzi Twoje linki
3. `yt-dlp fetching ...` - sciaga subs PL
4. `Usable sources after transcription: 5`
5. `Topic for 2026-MM-DD: persona=marek usp=auto_publishing ...`
6. `Script 1 iter 1 verdict=PASS scores={...}` - critic dal zielone
7. `Delivered 3 scripts to Telegram chat ...`

**Sprawdz telefon**: dostajesz 1 summary + 3 wiadomosci z hookami.
**Sprawdz repo**: `scripts/2026-MM-DD/` ma 3 pliki .md.

---

## 5. Wlaczenie cron'a (GitHub Actions)

Po pushu na branch (`claude/viral-content-system-0Ksu3` lub `main`), workflow
automatycznie rusza codziennie o **05:00 UTC** (06:00 PL zima / 07:00 PL lato).

Mozesz tez recznie:
1. Idz na repo -> **Actions** -> **"Daily viral scripts"**
2. Klik **"Run workflow"** -> branch -> **"Run workflow"**
3. Pojdz na kawe, za 5-10 min Telegram cie powiadomi

---

## 6. Co potrzebujesz miec, zeby zadzialalo

| Item | Required? | Jak |
|---|---|---|
| GEMINI_API_KEY | TAK | aistudio.google.com/apikey |
| GROQ_API_KEY | TAK (fallback) | console.groq.com/keys |
| TELEGRAM_BOT_TOKEN | TAK | @BotFather |
| TELEGRAM_CHAT_ID | TAK | @userinfobot |
| data/swipe-file.txt z 3+ linkami do KANALOW YT | TAK | Edycja recznie |
| yt-dlp w PATH | TAK | `pip install` lub apt |
| Python 3.11+ | TAK | sprawdz `python3 --version` |
| YOUTUBE_API_KEY | NIE (Faza 2) | console.cloud.google.com |

---

## 7. Co jezeli cos nie dziala

Zobacz `docs/TROUBLESHOOTING.md` (TODO - dodaje w Fazie 2).

Najczestsze problemy:
- **"No LLM API keys set"** -> sprawdz `.env`, czy klucze sa wpisane
- **"No usable transcripts"** -> linki w swipe-file.txt nie maja auto-subs PL (zmien linki)
- **Telegram brak wiadomosci** -> wyslij swojemu botowi cokolwiek najpierw (handshake)
- **Critic ciagle REGENERATE** -> obejrzyj wygenerowane skrypty w `scripts/`, popraw prompty w `config/prompts/`
