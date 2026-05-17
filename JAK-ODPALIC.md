# JAK TO ODPALIC (chmura, ~10 min)

Tryb chmurowy = system chodzi na GitHub Actions, bez Twojego PC. Tylko YouTube.
Dla TT/IG i tak musisz lokalnie - patrz `docs/SETUP-WINDOWS.md` po fakcie.

---

## KROK 1: Dodaj 4 sekrety na GitHubie (5 min)

Klikasz w 4 linki ponizej. Kazdy otwiera od razu okno dodania nowego sekretu.

### Najpierw zdobadz wartosci (15 min jezeli jeszcze nie masz):

| Sekret | Skad | Format |
|---|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey -> Create API key | `AIza...` |
| `GROQ_API_KEY` | https://console.groq.com/keys -> Create API Key | `gsk_...` |
| `TELEGRAM_BOT_TOKEN` | Telegram: @BotFather -> /newbot | `1234567890:ABC...` |
| `TELEGRAM_CHAT_ID` | Telegram: @userinfobot -> /start | `123456789` (sama liczba) |

**Telegram WAZNE**: po stworzeniu bota napisz mu w Telegramie "test" - bez tego pierwsza wiadomosc nie przejdzie.

### Potem dodaj je w GitHubie:

Wejdz na: **https://github.com/EricsonArt/moje-projekty/settings/secrets/actions/new**

(Jezeli przekierowuje na login - zaloguj sie i wroc na ten link)

Dla **kazdego z 4 sekretow** powtorz:
1. **Name**: wpisz dokladnie nazwe (np. `GEMINI_API_KEY`)
2. **Secret**: wklej wartosc
3. Klik **"Add secret"**
4. Klik **"New repository secret"** zeby dodac kolejny

Po 4 sekretach powinienes widziec liste na: https://github.com/EricsonArt/moje-projekty/settings/secrets/actions

---

## KROK 2: Wklej linki do kanalow YT (3 min)

Wejdz na: **https://github.com/EricsonArt/moje-projekty/edit/claude/viral-content-system-0Ksu3/data/swipe-file.txt**

(To otwiera plik `data/swipe-file.txt` w edytorze GitHuba, na branchu `claude/viral-content-system-0Ksu3`.)

### Co tam wpisac:

Pod sekcja `=== Twoje kanaly ===` wstaw linki do **3-5 polskich kanalow YouTube** ktore robia viralowe Shorty w Twojej niszy.

Format - kazdy link w osobnej linijce, **bez znaku `#`** na poczatku:
```
https://www.youtube.com/@kanal1
https://www.youtube.com/@kanal2
https://www.youtube.com/@kanal3
```

### Jak znalezc kanaly w 2 minuty:

1. Wejdz na YouTube
2. Wpisz w wyszukiwarke: `AI biznes shorts polska` (lub `personal brand shorts`, `pasywny dochod shorts`)
3. Klik na **3-5 filmow ktore maja >100k views**
4. Z kazdego filmu klik **nazwa kanalu** na gorze (pod tytulem filmu)
5. Skopiuj URL z paska adresu (powinien byc postaci `https://www.youtube.com/@nazwa`)
6. Wklej do `data/swipe-file.txt`

### Zapisz:

Na dole strony GitHuba: zielony przycisk **"Commit changes..."** -> upewnij sie ze branch to `claude/viral-content-system-0Ksu3` -> **"Commit changes"**.

---

## KROK 3: Odpal workflow recznie (1 min)

Wejdz na: **https://github.com/EricsonArt/moje-projekty/actions/workflows/daily.yml**

1. Po prawej stronie klik niebieski przycisk **"Run workflow"**
2. W rozwijanym menu **Branch** wybierz: `claude/viral-content-system-0Ksu3`
3. Klik zielony **"Run workflow"** na dole

Czekaj 3-5 min. Strona sama nie odswieza - F5 raz na minute.

Jak workflow skonczy sie zielonym haczkiem ✓:
- Sprawdz Telegrama (powinien byc 1 summary + 3 wiadomosci ze skryptami)
- Sprawdz folder na GitHubie: https://github.com/EricsonArt/moje-projekty/tree/claude/viral-content-system-0Ksu3/scripts

Jak workflow padl czerwonym X:
- Klik na run zeby zobaczyc logi
- Najczestsze przyczyny opisane w `docs/SETUP.md` rozdzial 7

---

## KROK 4: Wlacz codzienny cron (opcjonalnie, 30 sek)

Jezeli chcesz zeby workflow odpalal sie sam codziennie o 06:00 PL (zima), trzeba zmergowac branch do `main`.

Na razie pomin - testujmy recznie kilka razy zanim wpuscimy do glownego brancha. Powiedz mi jak zechcesz to wlaczyc na stale.

---

## Status checklist:

- [ ] GEMINI_API_KEY dodany jako secret
- [ ] GROQ_API_KEY dodany jako secret
- [ ] TELEGRAM_BOT_TOKEN dodany jako secret
- [ ] TELEGRAM_CHAT_ID dodany jako secret
- [ ] data/swipe-file.txt ma min 3 linki do kanalow YT (bez `#` na poczatku)
- [ ] Workflow odpalony recznie - dostalem skrypty na Telegram

---

## Co kiedy chcesz dolozyc TikTok / Instagram:

Wtedy MUSI byc lokalnie - chmura nie da rady (TT/IG wymaga zalogowanego konta).
Patrz: `docs/SETUP-WINDOWS.md` (lokalny tryb dla Windows).
