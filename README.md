# Viral Content Engine - Skala

Codziennie o 7:00 dostajesz na Telegram **3 gotowe skrypty viralowych shortow PL**,
inspirowane realnymi viralami konkurencji, dostosowane do glosu Eryka Hajduczka
i prowadzace widza do oferty SaaS-u **Skala** (systemskala.pl).

## Co to robi w 1 zdaniu

Bierze 3-10 **kanalow YT/TikTok/Instagram konkurencji**, automatycznie wyciaga z nich top
shorty (YT po views, TT/IG najnowsze), analizuje ich wzorce hookow -> generuje 3 oryginalne
skrypty 30-60s z hookiem + body (Hormozi PL) + CTA do pakietu Skala -> wysyla ci na Telegram
do nagrania talking-head.

## Dwa tryby pracy

- **Lokalnie na PC (Windows)** - pelne wsparcie YT + TT + IG. Wymaga cookies z Twojej
  przegladarki dla TT/IG. Setup: [docs/SETUP-WINDOWS.md](docs/SETUP-WINDOWS.md).
- **Chmura (GitHub Actions)** - tylko YouTube (TT/IG wymagaja logowania ktore nie dziala
  z chmury bez ryzyka bana). Setup: [docs/SETUP.md](docs/SETUP.md).

## Stack (caly darmowy)

- **LLM**: Gemini 2.5 Flash + Groq Llama 3.3 70B (fallback)
- **Scrape**: yt-dlp (YouTube Shorts auto-subs PL)
- **Orchestracja**: GitHub Actions cron 05:00 UTC
- **Delivery**: Telegram bot
- **Storage**: pliki .md w `scripts/YYYY-MM-DD/` (commitowane do repo)

## Quick start

- **Tryb lokalny Windows (TT+IG+YT)**: [docs/SETUP-WINDOWS.md](docs/SETUP-WINDOWS.md) (~30-45 min)
- **Tryb chmurowy (tylko YT)**: [docs/SETUP.md](docs/SETUP.md) (~15 min)

Test lokalny:
```bash
pip install -r requirements.txt
cp .env.example .env  # uzupelnij klucze
python -m src.main
```

Co masz na koncu:
- Telegram: 3 wiadomosci z hookami, pelnymi skryptami, b-rollem, hashtagami
- Repo: `scripts/2026-MM-DD/01-*.md`, `02-*.md`, `03-*.md`

## Edycja zachowania

Caly system sterowany YAML-ami w `config/`:
- `product.yaml` - pakiety, ceny, USP, scarcity Skali
- `icp.yaml` - persony Marek + Anna, weekly rotation
- `user_voice.yaml` - glos Eryka, zakazane frazy, sygnaturowe wzorce
- `competitors.yaml` - kanaly konkurencji (Faza 2+)
- `niche_keywords.yaml` - keywordy + whisper fixes
- `prompts/*.md` - 5 promptow LLM (edytujesz bezposrednio)

Po edycji nie trzeba nic kompilowac - kolejny run pickup'uje zmiany.

## Status implementacji

- [x] **Faza 1**: MVP - 1 LLM call generation + critic loop, swipe-file YT, Telegram delivery
- [ ] **Faza 2**: Multi-agent (5 analyst + 5 generator), SQLite + sqlite-vec, provider rotation
- [ ] **Faza 3**: Lokalny scraper TT/IG (cookies), lead magnet "Generator Hookow"
- [ ] **Faza 4**: Conversion feedback loop, A/B testing, thumbnail generator

## Architektura

```
data/swipe-file.txt (kanaly YT) -> expand: top shorty >=500k views -> yt-dlp scrape + auto-subs
                              |
                              v
                       transcribe (.vtt -> text)
                              |
                              v
              Topic Picker (weekly rotation z icp.yaml)
                              |
                              v
                3x Generator (rozny hook_type per skrypt)
                              |
                              v
                  Critic loop (max 3 iter, threshold 8/10)
                              |
                              v
                Telegram delivery + commit do /scripts/
```

## Co system NIE zrobi (uczciwie)

- Nie nagra wideo (talking-head, Twoja twarz/glos)
- Nie zmontuje (CapCut + 10 min recznie)
- Nie zagwarantuje virala (realistic 1/20-30 prob, ale to 10x lepiej niz bez systemu)
- Nie wykryje trending audio (TT trending sounds nie sa w API)

## Docs

- [docs/SETUP.md](docs/SETUP.md) - krok po kroku setup (15-30 min)
