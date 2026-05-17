# CLAUDE.md - Kontekst dla Claude Code (lokalnie na PC Eryka)

> Ten plik jest automatycznie wczytywany przez Claude Code przy starcie sesji.
> Zawiera caly stan rozmowy z wersji webowej, decyzje architektoniczne i kolejne kroki.
> Dla nowego Claude'a: czytaj to PRZED rozpoczeciem pracy.

---

## Kim jest user

**Eryk Hajduczek** - tworca SaaS-u **Skala** (systemskala.pl). Niszowo: AI / personal brand /
passive income / side hustle dla polskiego rynku. Bedzie nagrywal talking-head shorty pod
TT/Reels/YT Shorts i kierowal widzow do oferty Skali.

**Wazne o komunikacji z Erykiem**:
- Pracuje na telefonie czesto, woli **krotkie odpowiedzi po polsku**.
- Nie czyta dlugich blokow tekstu. Tabele i bullet points OK.
- Preferuje **prowadzenie za reke krok po kroku** zamiast jednej ogromnej instrukcji.
- Nie zna szczegolow technicznych - tlumacz prosto, bez zargonu.
- Jak cos nie rozumie, mowi to wprost - wtedy uprosc jeszcze bardziej.

---

## Stan projektu - Faza 1.5 (lokalny tryb)

System generuje codziennie **3 skrypty viralowych shortow PL** na podstawie inspiracji
z kanalow YT/TT/IG, dostarcza je na Telegram do nagrania talking-head.

### Architektura

```
data/swipe-file.txt (linki do kanalow YT/TT/IG)
        |
        v
[Expand kanaly per platforma]
  - YT: top shorty >= CHANNEL_MIN_VIEWS (default 500k)
  - TT/IG: N najnowszych z profilu (wymaga cookies)
        |
        v
[Fetch metadata]
  - YT: yt-dlp + auto-subs PL (-> VTT -> tekst)
  - TT/IG: yt-dlp + cookies -> info.json -> pseudo-transkrypt (tytul + opis)
        |
        v
[Topic Picker] - persona/USP/pakiet z weekly rotation (icp.yaml)
        |
        v
[Generator x3] - rozny hook_variant per skrypt
        |
        v
[Critic loop] - max 3 iter, threshold 8/10 (Gemini lub Groq fallback)
        |
        v
[Delivery] - Telegram + commit scripts/YYYY-MM-DD/*.md
```

### Stack (caly darmowy)

- **LLM**: Gemini 2.5 Flash (~250-500 req/dzien free) + Groq Llama 3.3 70B (fallback)
- **Scrape**: yt-dlp (yt + tt + ig)
- **Orchestracja LOKALNIE**: Windows Task Scheduler (ONLOGON +30s)
- **Orchestracja CHMURA (opcja YT-only)**: GitHub Actions cron 05:00 UTC
- **Delivery**: Telegram bot (python-telegram-bot)
- **Storage**: pliki .md w `scripts/YYYY-MM-DD/`, commitowane do repo

### Branch i tryb pracy

- Branch: **`claude/viral-content-system-0Ksu3`** - WSZYSTKO commituj tu.
- NIE pushuj na main bez pytania.
- User pracuje **lokalnie na Windows**, wlacza PC rano, pipeline odpala sie sam przez
  Task Scheduler.

---

## Kluczowe decyzje uzytkownika

| Decyzja | Wybor | Dlaczego |
|---|---|---|
| Skad bierzemy inspiracje | YT + TT + IG (wszystkie 3) | User scrolluje TT/IG na codzien, chce mix |
| Format inputu | **Linki do KANALOW**, nie pojedynczych filmow | Mniej recznej pracy - "podaje linki do 5 profili" |
| Tryb hostingu | **Lokalnie na Windows** | Bo TT/IG wymagaja cookies = nie mozna z chmury bezpiecznie |
| Kiedy odpala | **Przy logowaniu do Windowsa (ONLOGON)** | User wlacza PC rano, nie ma 24/7 |
| Min views YT | 500 000 (configurable: CHANNEL_MIN_VIEWS) | Default, dostosuj jak kanaly mniejsze |
| Glos | Hybryda: Hormozi struktura + Eryk krotkie deklaracje + kontrarian hooki | Anti-guru, anti-FOMO |
| Dlugosc | 30-60s (75-150 slow PL) | Sweet spot dla TT/Reels |
| Triggery DM | NA RAZIE BRAK - CTA -> "link w bio" -> quiz/checkout | DM bot dopiero Faza 4 |

---

## Co user musi zrobic na PC (status setup'u)

Setup w `docs/SETUP-WINDOWS.md` (czyt jezeli user pyta o szczegoly). 9 krokow:

- [ ] 1. Zainstalowac Python 3.11+ z PATH (`python.org/downloads`)
- [ ] 2. Pobrac repo (ZIP albo git clone), branch `claude/viral-content-system-0Ksu3`
- [ ] 3. Zdobyc 4 darmowe klucze: Gemini, Groq, Telegram bot token, Telegram chat_id
- [ ] 4. Uruchomic `windows\install.bat` (tworzy venv, instaluje requirements)
- [ ] 5. Wpisac klucze do `.env`
- [ ] 6. Wyeksportowac cookies TT i IG przez rozszerzenie "Get cookies.txt LOCALLY",
       wrzucic do `data\cookies\tiktok.txt` i `data\cookies\instagram.txt`
       (REKOMENDACJA: zaloz drugie konto "obserwacyjne" TT/IG zeby chronic glowne)
- [ ] 7. Wkleic 3-10 linkow do kanalow w `data\swipe-file.txt`
- [ ] 8. Test: `windows\run-once.bat` - sprawdz Telegrama
- [ ] 9. Wlacz autostart: `install-autostart.bat` **jako administrator**

**Gdy user mowi "jestem na kroku N":** zaprowadz go przez kolejne kroki bez przeskakiwania.
Zapytaj co widzi na ekranie. Nie zakladaj ze cos jest oczywiste.

---

## Struktura repo (mapa dla Claude'a)

```
src/
  main.py                      # entry point: python -m src.main
  settings.py                  # pydantic settings z .env (klucze API, CHANNEL_MIN_VIEWS itp.)
  scrape/
    swipe_file.py              # parser linkow YT/TT/IG (6 typow: yt_channel/yt_video/tt_*/ig_*)
    youtube.py                 # yt-dlp dla YT: fetch_video + expand_channel (po views)
    social.py                  # yt-dlp dla TT/IG: fetch_social_video + expand_tiktok/instagram_channel
                               # Pseudo-transkrypt = title + description (TT/IG nie maja subow)
  transcribe/
    auto_subs.py               # parse VTT -> plain text (tylko YT)
  generate/
    pipeline.py                # Topic Picker (weekly rotation) + generate_one_script (LLM call)
  critic/
    pipeline.py                # critic agent: scores + verdict PASS/REGENERATE
  llm/
    router.py                  # Gemini primary + Groq fallback z retry
    providers.py               # konkretne wywolania API
  deliver/
    telegram_bot.py            # send_message do Telegrama
    git_commit.py              # save scripts/YYYY-MM-DD/*.md

config/                        # YAML configi (edytowalne, nie wymagaja kompilacji)
  product.yaml                 # pakiety Skali, ceny, USP, scarcity
  icp.yaml                     # persony Marek + Anna, weekly rotation
  user_voice.yaml              # glos Eryka, banned_phrases, sygnaturowe wzorce
  niche_keywords.yaml          # keywordy + whisper fixes
  competitors.yaml             # kanaly konkurencji (refek do Fazy 2)
  prompts/
    hook_generator.md
    body_generator.md
    cta_integrator.md
    style_adapter.md
    critic.md

data/
  swipe-file.txt               # INPUT: linki do kanalow (commitowane)
  cookies/                     # cookies TT/IG/YT (gitignored, tylko README.txt commitowany)
    README.txt                 # instrukcja eksportu cookies
  raw/                         # cache yt-dlp (gitignored)

windows/                       # Windows-specific tooling
  install.bat                  # venv + pip install
  run-once.bat                 # uruchom pipeline raz
  install-autostart.bat        # rejestruje task w Task Scheduler ONLOGON +30s
  uninstall-autostart.bat      # usuwa task

docs/
  SETUP.md                     # chmurowy tryb (tylko YT, GitHub Actions)
  SETUP-WINDOWS.md             # **gowny przewodnik dla Eryka** - lokalny tryb full

.github/workflows/daily.yml    # GitHub Actions cron (tylko jezeli user wybierze chmurowy tryb YT-only)
```

---

## Mapa wersji / fazy

- [x] **Faza 1**: MVP - YT swipe-file (recznie linki) + 1 LLM call + critic + Telegram
- [x] **Faza 1.5**: YT linki KANALOW + filtr views (chmurowy tryb dziala)
- [x] **Faza 1.5+** (aktualna): TT/IG kanaly + lokalny Windows mode + Task Scheduler
- [ ] **Faza 2**: Multi-agent (5 analyst + 5 generator), SQLite + sqlite-vec dla anti-repeat
- [ ] **Faza 3**: Lead magnet "Generator Hookow" + ManyChat triggery DM
- [ ] **Faza 4**: Conversion feedback loop, A/B testing, thumbnail generator

---

## Konwencje techniczne

- Python 3.11+, async/await wszedzie
- Type hints obowiazkowo
- `pydantic-settings` na konfiguracje z .env
- yt-dlp przez subprocess (`asyncio.create_subprocess_exec`), nie biblioteke
- Logging stdlib (logging.getLogger), poziom INFO default, DEBUG przez flage
- **Czeskie znaki w stringach PL OK** (nie unicode-escape)
- Nie commituj: `.env`, `data/cookies/*.txt`, `data/raw/`, `*.mp4`, `logs/`
- **Nie pushuj na main** - tylko `claude/viral-content-system-0Ksu3`

---

## Edge cases ktore juz obsluzylem

- TT/IG bez cookies -> warning + skip kanalu (nie crash)
- YT kanal ponizej CHANNEL_MIN_VIEWS -> warning + skip
- YT video bez subow PL -> fallback pl-orig / en, jak brak -> skip
- TT/IG pseudo-transkrypt < 80 chars -> skip
- Cookies wygasle -> "Login required" w stderr yt-dlp -> przyjazny komunikat w log
- Critic loop max 3 iter, jak wszystko fail -> wez best-so-far + warning

---

## Co user moze pytac (i jak odpowiadac)

**"Cookies wygasly co robic?"** -> wyeksportuj ponownie z przegladarki, nadpisz plik w
`data\cookies\`. Nic wiecej.

**"TT/IG dalej nic nie zwracaja"** -> sprawdz `logs\run-*.log` szukajac "yt-dlp failed".
Najczesciej: cookies stare, IG konto rate-limited (1-2h przerwy), TT kanal prywatny.

**"Chce zmienic godzine uruchomienia"** -> Task Scheduler -> `ViralContentEngine_Daily`
-> Triggers -> zmien z ONLOGON na Daily HH:MM.

**"Konto TT/IG zostalo zbanowane"** -> uzylismy glownego konta (ostrzegalem!). Zaloz nowe
"obserwacyjne", przepnij cookies. Konto glowne mozesz odzyskac przez appeal w aplikacji.

**"Chce dodac wiecej skryptow dziennie"** -> edytuj `.env` -> `SCRIPTS_PER_DAY=5` (max 5
ze wzgledu na limity Gemini free tier).

**"Skrypty brzmia nie-jak-ja"** -> edytuj `config/user_voice.yaml` (banned_phrases,
signature_patterns). Po edycji NIE trzeba nic kompilowac - kolejny run pickupuje.

---

## TODO ktore zostawilem na pozniej

- [ ] Faza 2: anti-repeat (SQLite + sqlite-vec) - zeby nie generowal podobnych hookow
- [ ] Faza 2: provider rotation w llm/router.py - smartszy fallback
- [ ] CI: GitHub Actions z testami pytest (na razie tylko smoke testy recznie)
- [ ] Whisper fallback dla shortow bez auto-subow (faster-whisper)
- [ ] Conversion tracking: which script -> which sale (po pierwszym viralu)

---

## Pliki do przeczytania PRZY STARCIE sesji (jak user nie powie inaczej)

1. Ten plik (CLAUDE.md) - mam pelny kontekst
2. `docs/SETUP-WINDOWS.md` - jak user pyta o instalacje
3. `data/swipe-file.txt` - co user juz wkleil
4. Ostatni log w `logs/run-*.log` - jak user mowi "nie dziala"

Nie czytaj wszystkich plikow konfiguracji ani src/ na start - tylko jak pytanie ich dotyczy.
