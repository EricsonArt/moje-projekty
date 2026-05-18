# DZIEN DOBRY ERYK - status systemu rano

System dziala. Wczoraj wygenerowal pierwsze 3 skrypty (sprawdz scripts/2026-05-18/).
Przez noc dodalem **wszystkie 5 faz z listy C** (suwaki, panel, multi-platform, trending, ratings).

## Co dziala JUZ TERAZ (bez Twojego klikniecia)

✅ **Pipeline z Apify dla TT** - 6 Twoich TT kanalow scrape'owanych co dzien rano
✅ **Cron 05:00 UTC** - codzienne automatyczne uruchamianie (poniedzialek-niedziela)
✅ **6 suwakow w preferences** - edytujesz `config/preferences.yaml` na repo, pipeline czyta przy nastepnym runie
✅ **Telegram delivery** - 3 skrypty na Telegram (trafia rano)
✅ **Critic loop** - max 3-5 iteracji per skrypt z auto-poprawkami
✅ **Multi-platform output** - opcjonalnie 3 wersje per skrypt (TT/Reels/Shorts), toggle w preferences
✅ **Ratings learning** - jak ocenisz skrypty 👍/👎, system uczy sie czego unikac
✅ **Trending hooks** - opcjonalnie codziennie analiza top viralowych hookow z konkurencji

## Co wymaga TWOJEGO klikniecia (15-20 min jednorazowo)

### KROK 1: Wdroz Web Panel na Vercel (~10 min)

Panel pozwala edytowac suwaki + kliknac "Wygeneruj teraz" + zobaczyc skrypty z historii.

1. Otworz: **https://vercel.com/new**
2. Zaloguj sie (Github login - to samo konto co repo)
3. Klik **"Import Git Repository"** -> wybierz **EricsonArt/moje-projekty**
4. WAZNE: **"Root Directory"** -> klik **"Edit"** -> wpisz: **`panel`** (NIE main, NIE root!)
5. Sekcja **"Environment Variables"** - dodaj 3:
   - `GITHUB_TOKEN` = stworz go na: https://github.com/settings/tokens/new?scopes=repo,workflow&description=Skala%20Viral%20Panel
     (zaznacz scope: **repo** i **workflow**, klik "Generate token", skopiuj ghp_...)
   - `PANEL_PIN` = wymysl 4-6 cyfrowy PIN (np. `1234`)
   - `RATING_TOKEN` = wymysl losowy string 32 znakow (np. `xQ7vKj9mLpN3rF8sA2dH5gT6yU4eR1wB`)
6. Klik **"Deploy"**
7. Po 2 min Vercel da Ci URL typu **`https://moje-projekty-xxx.vercel.app`** - skopiuj go

### KROK 2: Dodaj URL panelu do GitHub Secrets/Variables (~2 min)

Zeby Telegram dodawal linki w wiadomosciach (👍/👎/Edytuj):

1. https://github.com/EricsonArt/moje-projekty/settings/secrets/actions/new
   - Name: **`RATING_TOKEN`**
   - Value: **dokladnie ta sama wartosc co w Vercel** (np. `xQ7vKj9mLpN3rF8sA2dH5gT6yU4eR1wB`)
   - Klik "Add secret"

2. https://github.com/EricsonArt/moje-projekty/settings/variables/actions/new
   - Name: **`PANEL_URL`**
   - Value: URL z Vercel (np. `https://moje-projekty-xxx.vercel.app`)
   - Klik "Add variable"

### KROK 3: Test panelu (~3 min)

1. Otworz URL z Vercel
2. Wpisz PIN -> wchodzisz w panel
3. Zobaczysz 6 suwakow + przycisk "Wygeneruj teraz" + liste skryptow
4. Klik **"🚀 Wygeneruj teraz"** -> workflow startuje
5. Czekaj 3-5 min, sprawdz Telegram - teraz wiadomosci powinny miec **buttony 👍/👎/Edytuj** na dole

## Co masz w panelu

### Suwaki

| Suwak | Zakres | Default | Co robi |
|---|---|---|---|
| Ilość skryptów | 1-10 | 3 | Ile skryptów na 1 run |
| **Intensywność CTA** | 0-100% | 30% | 0=pure value, 100=hard sell |
| **Podobieństwo do inspiracji** | 0-100% | 40% | 0=oryginał, 100=klon |
| **Effort level** | 1-10 | 6 | 1-4=fast, 5-7=std, 8-10=thorough (multi-attempt z 3 kandydatów) |
| Długość filmu | 15-90s | 45s | Target sec/word count |
| Ton | dropdown | balanced | anti_guru/hormozi/storyteller/kontrarian/balanced |

### Buttony w Telegramie (po setup panelu)

Pod każdym skryptem na Telegramie:
- **👍 Świetne** → click → system pamięta że ten hook+styl Ci pasuje → next gen używa go jako wzorzec
- **👎 Słabe** → click → system uczy się czego unikać
- **⚙️ Edytuj preferencje** → otwiera panel z suwakami

Pod summary (gora wiadomosci):
- **🚀 Wygeneruj kolejne** → trigger workflow z chmury
- **⚙️ Suwaki** → otwiera panel

### Toggle features (edytuj w preferences.yaml lub przez panel jutro)

- `multi_platform.enabled: true` → generator robi 3 wersje per skrypt (TT 30s, Reels 45s, Shorts 60s) z różnymi hashtagami
- `trending_hooks.enabled: true` → rano pojawia się dodatkowa wiadomość z top 5 viralowych hooków z konkurencji
- `ratings.use_history_in_prompts: true` → ratings wpływają na generację (default ON)

## Status checklist

- [x] System pipeline TT (Apify) - dziala z chmury, codziennie 05:00 UTC
- [x] Suwaki w config/preferences.yaml - dziala
- [x] Web Panel kod gotowy w panel/ - wdroz na Vercel (krok 1 wyzej)
- [x] Inline buttons w Telegram - aktywne po setup PANEL_URL (krok 2)
- [x] Multi-platform output - kod gotowy, toggle w preferences
- [x] Trending hooks - kod gotowy, toggle w preferences
- [x] Ratings learning - aktywne automatycznie, jak klikasz 👍/👎
- [ ] Wdroz panel na Vercel (KROK 1) - musisz Ty
- [ ] Dodaj PANEL_URL + RATING_TOKEN do GitHub (KROK 2) - musisz Ty
- [ ] Test panel + buttony (KROK 3)

## Uczciwe ostrzezenia

1. **Token Telegram bota ktory mi pokazales jest "spalony"** - kiedys (dzisiaj/jutro) zrob `/revoke` w BotFather, wygeneruj nowy, zaktualizuj secret w repo.
2. **GITHUB_TOKEN** ktory wygenerujesz dla Vercel - **nie share'uj** nikomu. Jest scope'owany do tego repo, ale dalej daje pelen dostep. Ja go nie potrzebuje znac.
3. **Apify free credit $5/mc** - jak skonczysz, workflow zacznie zwracac 402 Payment Required. Sprawdz: https://console.apify.com/billing - aktualnie wystarczy spokojnie na codzienny scrape 6 TT kanalow.

## Jak cos nie dziala

1. Workflow padl - https://github.com/EricsonArt/moje-projekty/actions
2. Klik na ostatni run -> "generate" -> step z czerwonym X -> przeczytaj logi
3. Najczestsze przyczyny w "Common issues" sekcji w `docs/SETUP.md`
4. Albo wyslij mi screen logow - zfixuje

## Co dalej

System teraz **uczy sie z Twoich ratingow**. Im wiecej 👍/👎 dasz, tym lepsze skrypty.
Po 2-3 tygodniach mozesz zobaczyc co dziala (folder `scripts/`), zaktualizowac kanaly w
swipe-file, dodac IG kanaly, podniesc effort_level do 8 dla weekendowych "premium" gen runs.

Powodzenia z nagrywaniem! 🎬
