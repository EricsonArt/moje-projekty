# DZIEN DOBRY ERYK - czytaj to pierwsze rano

System jest gotowy. Stan na rano (przygotowane noca):

## Co dziala juz teraz (bez Twojego klikniecia)

- **YouTube z chmury** = pelnia gotowe. Wystarczy odpalic workflow recznie - sprawdz Telegram za 5 min.
- **Sekrety**: GEMINI, GROQ, TELEGRAM tokens - masz dodane
- **Kanaly w swipe-file**: 6 TT (Twoje wybory) + 3 YT (backup zeby cos zaskoczylo)

## Co NIE dziala bez Twojego dzialania

- **TikTok i Instagram** - wymaga JEDNEJ z 3 opcji ponizej. Pipeline pominie TT/IG i polecisz z YT, dopoki nie wybierzesz.

---

## Wybierz jedna z 3 opcji dla TT/IG

### Opcja A: APIFY (zalecane - chmura, ~2 min Twojej pracy)

**Plus**: dziala z chmury, bez Twojego PC, Apify sam ogarnia TT/IG ze swojej infrastruktury (nie banuje)
**Minus**: rejestracja na zewnetrznym serwisie. Free $5 kredytow/mc - dla Ciebie wystarczy spokojnie (~10k filmow/mc darmowo)

Kroki:
1. Otworz: **https://console.apify.com/sign-up?asrc=developers**
2. Zarejestruj sie przez Google (najszybciej)
3. Po zalogowaniu: **https://console.apify.com/account/integrations** -> Twoj API token jest na gorze. Kliknij oczko zeby pokazac, skopiuj.
4. Dodaj jako secret w GitHubie: **https://github.com/EricsonArt/moje-projekty/settings/secrets/actions/new**
   - Name: `APIFY_TOKEN`
   - Secret: wklej token
5. Odpal workflow: **https://github.com/EricsonArt/moje-projekty/actions/workflows/daily.yml** -> Run workflow (branch: `claude/viral-content-system-0Ksu3`)

**Po 5 min: skrypty z TT/IG/YT na Telegramie.**

---

### Opcja B: COOKIES W SECRETS (chmura, 100% darmowe, ale refresh co 1-2 tyg)

**Plus**: zero kosztow, dziala z chmury
**Minus**: Twoje cookies na GitHubie (zaszyfrowane, ale jednak), trzeba refresh co tydzien-dwa

Kroki:
1. W Chrome zainstaluj rozszerzenie **"Get cookies.txt LOCALLY"** (TYLKO z LOCALLY w nazwie!):
   https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
2. Wejdz na **tiktok.com** zalogowany -> klik ikonke rozszerzenia (gora prawo) -> "Export As" -> "Netscape" -> pobiera plik
3. **Otworz pobrany plik w Notatniku, zaznacz wszystko (Ctrl+A), skopiuj (Ctrl+C)**
4. Dodaj jako secret: **https://github.com/EricsonArt/moje-projekty/settings/secrets/actions/new**
   - Name: `TIKTOK_COOKIES`
   - Secret: wklej zawartosc (Ctrl+V)
5. Powtorz dla Instagrama (wejdz instagram.com zalogowany, eksport, wklej jako `INSTAGRAM_COOKIES`)
6. Odpal workflow: https://github.com/EricsonArt/moje-projekty/actions/workflows/daily.yml -> Run workflow

REKOMENDACJA: zaloz drugie konto TT/IG (5 min na telefonie), zaloguj sie nim w przegladarce, jego cookies daj systemowi. Twoje glowne konto bezpieczne.

---

### Opcja C: LOKALNIE NA PC (twoj komputer, 100% darmowe, 15 min)

Patrz `DZISIAJ.md` - START.bat robi wszystko sam, prowadzi za reke.

---

## Jak nie wybierzesz nic = workflow odpali sie z samym YT

Cron jest skonfigurowany na codziennie 5 UTC (06/07 PL). Z samych YT kanalow dostaniesz 3 skrypty kazdego dnia.

## Pierwszy test TERAZ

Po wybraniu opcji (A/B/C) wejdz na:
**https://github.com/EricsonArt/moje-projekty/actions/workflows/daily.yml**

Klik **"Run workflow"** (po prawej) -> Branch: `claude/viral-content-system-0Ksu3` -> zielony **"Run workflow"**.

Czekaj 3-5 min. Sprawdz Telegrama.

## Jak cos nie zadziala

1. Wejdz na zakladce Actions -> klik na ostatni run -> zobacz logi
2. Pisz do Claude'a (web) ze screenshotem bledu - zdiagnozuje
3. Workflow tez wysle Ci alert na Telegram jak padnie

---

## Status checklist (sprawdz na zimno)

- [x] Kod scraperow gotowy (TT/IG przez Apify lub cookies)
- [x] Workflow GitHub Actions hardened (preflight checks, friendly errors)
- [x] Cron skonfigurowany na codziennie 5 UTC
- [x] Sekrety GEMINI, GROQ, TELEGRAM masz dodane
- [x] swipe-file ma 9 aktywnych linkow (6 TT + 3 YT backup)
- [ ] Wybrales opcje A/B/C dla TT/IG
- [ ] Odpaliles pierwszy workflow recznie

## Jak chcesz wlaczyc auto-cron codziennie

Cron jest aktywny TYLKO gdy kod jest w branchu `main`. Aktualnie jest na `claude/viral-content-system-0Ksu3`.

Zeby wlaczyc cron:
1. Otworz PR: **https://github.com/EricsonArt/moje-projekty/compare/main...claude/viral-content-system-0Ksu3**
2. Klik "Create pull request" -> "Create pull request"
3. Na PR klik "Merge pull request" -> "Confirm merge"
4. Od jutra rano cron sam ruszy o 05:00 UTC

Ale najpierw odpal workflow recznie raz - upewnij sie ze dziala zanim wlaczysz auto.
