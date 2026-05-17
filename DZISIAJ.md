# Co zrobic dzisiaj

**Najpierw przeczytaj `PORANEK.md`** - tam jest pelny status i 3 opcje dla TT/IG.

## Szybki podsumowanie (2 minuty)

System jest skonfigurowany:
- Sekrety masz dodane (GEMINI, GROQ, TELEGRAM)
- swipe-file ma 9 aktywnych zrodel (6 TT + 3 YT backup)
- Workflow gotowy do uruchomienia

## Najszybsza sciezka (5 min)

1. Wejdz: https://github.com/EricsonArt/moje-projekty/actions/workflows/daily.yml
2. Klik **"Run workflow"** -> Branch: `claude/viral-content-system-0Ksu3` -> **"Run workflow"**
3. Za 3-5 min sprawdz Telegram

**Bez wybierania opcji TT/IG** dostaniesz skrypty wygenerowane z YouTube kanalow (backup). To dowod ze pipeline LLM+Telegram dziala.

## Zeby TT/IG tez dzialal

Patrz `PORANEK.md` - opcja A (Apify, najlatwiej), B (cookies w secrets) lub C (lokalnie).

## Pelny przewodnik lokalnego trybu (opcja C)

Patrz `docs/SETUP-WINDOWS.md` i skrypt `windows/START.bat`.
