---
description: Wygeneruj N viralowych skryptow short-form dla brandu Skala
---

Wywolaj skill `skala-viral` (zdefiniowany w `.claude/skills/skala-viral/SKILL.md`)
i wykonaj jego pelny workflow z 6 krokami.

Zacznij OD RAZU od KROK 1 (AskUserQuestion z 4 pytaniami o ilosc/ton/CTA/research).
NIE pytaj uzytkownika o nic poza tym co jest w skillu.

Jesli uzytkownik podal argumenty do tego commanda (np. `/viral 5 hormozi hard`),
zinterpretuj je i pomin odpowiadajace pytania:
- pierwsza liczba 1-10 = scripts_per_run
- slowo "balanced/anti_guru/hormozi/storyteller" = tone
- slowo "soft/mid/hard/vip" = cta_intensity
- slowo "swipe/manual/apify" = research_mode

Args od uzytkownika: $ARGUMENTS
