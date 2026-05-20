---
name: skala-viral
description: |
  Generuje viralowe skrypty short-form (TikTok/Instagram Reels/YT Shorts) dla brandu
  Skala (Eryk Hajduczek, systemskala.pl). Use when uzytkownik prosi o "skrypt",
  "viral", "filmik", "reel", "short", "content na social", "wygeneruj X skryptow",
  "skrypt na TT/IG", lub gdy uzywa slash command /viral. Pyta o parametry przez
  AskUserQuestion (ilosc, ton, dlugosc, CTA intensity, copy similarity, sposob
  researchu), laduje kontekst z config/, opcjonalnie scrape'uje wzorce viralowe
  (Apify/manual/swipe-file), generuje N skryptow w strukturze Hormozi PL z hookiem
  pattern-interrupt + 3 krokami + CTA, zapisuje do scripts/YYYY-MM-DD/.
---

# Skala Viral Skrypt Engine

Ten skill zastepuje pelen pipeline (Python + GitHub Actions + Vercel panel) jednym
flow w Claude Code. Generuje viralowe skrypty pod brand **Skala** w 6 krokach.

## CO TO JEST SKALA (kontekst minimum)

- **Founder**: Eryk Hajduczek (840k+ YT, 36k+ TT)
- **Domena**: systemskala.pl  
- **Tagline**: "Twoj biznes dziala, kiedy ty spisz"
- **Co robi**: AI generuje filmiki + AI tworzy produkt cyfrowy + auto-publishing na 4 platformy. Setup 10 minut.
- **4 pakiety**: Filmiki (1198 zl), Produkty (898 zl), **KOMPLET** (1498 zl - default), VIP (7997 zl one-time, 5 miejsc)
- **Lejek**: link w bio → quiz 7 pytan → segmentacja → systemskala.pl/dostep
- **Ceny Founders**: -40% vs regular, lock-in dozywotni dla pierwszych 50 osob

**ICP primary (Marek 70%)**: 35-50, 8-25k zl/mies, solopreneur/freelancer/manager,
nie chce pokazywac twarzy, cringe'uje na guru-mowke, kupuje liczby + ROI + risk reversal.

**ICP secondary (Anna 30%)**: 38-55, korpo lub mala firma uslugowa, kupuje storytelling
+ empatia + bezpieczenstwo (30 dni zwrotu).

Pelne dane w `config/product.yaml`, `config/icp.yaml`, `config/user_voice.yaml`.

---

## WORKFLOW (6 KROKOW)

### KROK 1: Spytaj uzytkownika o parametry

Uzyj **AskUserQuestion** z 4 pytaniami w **jednym wywolaniu** (multiSelect=false kazde):

1. **"Ile skryptow chcesz wygenerowac?"** header="Ilosc"
   - "1 skrypt" / "3 skrypty (Recommended)" / "5 skryptow" / "10 skryptow"

2. **"Jaki ton?"** header="Ton"
   - "Balanced - AI sam wybiera (Recommended)"
   - "Anti-guru - kontrarian, bezposredni"
   - "Hormozi PL - agitate→solve→CTA, mocny push"
   - "Storyteller - osobiste historie, dla Anny"

3. **"Jak mocne CTA / dlugosc?"** header="CTA + dlugosc"
   - "Value-only, 45s (Recommended dla trust building) - 95% konkretnej wartosci, ZERO sprzedazy, na koncu tylko 'wiecej na profilu' albo 'co Ty robisz inaczej?'"
   - "Soft CTA, 45s - 90% wartosc, mily push do quizu w bio"
   - "Mid CTA, 45s - polowa edukacja, polowa sprzedaz Komplet"
   - "Hard CTA, 30s - kazde zdanie sprzedaje, scarcity Founders"
   - "VIP CTA, 60s - transformacja, hook na 5 miejsc 1:1"

4. **"Skad brac inspiracje viralowe?"** header="Research"
   - "Bez scrape - uzyj swipe-file + signature hooks (Recommended, najszybsze)"
   - "Manual URLs - ja wkleje 3-10 linkow do viralowych TT/IG"
   - "Apify scrape - uruchom python -m src.scrape.apify (wymaga APIFY_TOKEN w env)"

**Mapowanie odpowiedzi na parametry wewnetrzne:**
- `scripts_per_run` = 1/3/5/10
- `tone` = balanced/anti_guru/hormozi/storyteller
- `cta_intensity` = value_only(5)/soft(20)/mid(50)/hard(80)/vip(95)
- `target_seconds` = 30/45/60
- `copy_similarity` = 40 (default, jak user chce inaczej moze zmienic w follow-up)
- `research_mode` = swipe/manual/apify

---

### KROK 2: Zaladuj kontekst

Read te pliki rownolegle (jedno wywolanie z multiple Read):
- `config/product.yaml` - pelne packages, USPs, scarcity, risk_reversal, funnel
- `config/icp.yaml` - Marek + Anna voice_notes, buying_triggers, weekly_rotation
- `config/user_voice.yaml` - banned_phrases, signature_phrases, signature_hooks, hook_hard_rules, body_structure, cta_slots
- `data/swipe-file.txt` - linki do viralowych kanalow

Jesli plik `config/prompts/hook_generator.md` istnieje, doczytaj rowniez te 5:
- `config/prompts/hook_generator.md`
- `config/prompts/body_generator.md`
- `config/prompts/cta_integrator.md`
- `config/prompts/style_adapter.md`
- `config/prompts/critic.md`

Wykorzystaj je jako PROMPT FRAGMENTS przy generowaniu. Jesli ich nie ma, uzyj
inline patterns z tego skill'a (sekcje DODATKI ponizej).

---

### KROK 3: Research viralowych wzorcow (opcjonalnie)

**Tryb "swipe"** (default, najszybszy):
- Wczytaj `data/swipe-file.txt`
- Wymien linki, ale powiedz uzytkownikowi: "Uzywam swipe-file + signature hooks
  jako wzorzec. Bez realnego scrape - hooks budowane z patterns z user_voice.yaml."
- Nie ma nic do scrape - uzywasz wzorcow inline.

**Tryb "manual"**:
- Spytaj uzytkownika: "Wklej 3-10 URL-i do viralowych shortow ktore ci sie podobaja
  (TikTok/IG/YT). Po jednym na linie."
- Po otrzymaniu URL-i:
  - Dla TT URL: uzyj WebFetch z prompt "Wyciagnij hook (pierwsze 2 zdania transkrypcji),
    cala transkrypcje, ilosc views, ilosc lajkow. Format JSON."
  - Dla IG/YT: analogicznie
  - Zbierz {url, hook, transcript, views, likes} dla kazdego.
- Wyciagnij PATTERN: ktorych hookow uzywaja? Jakie struktury body? Jakie CTA?
- Uzyj tego pattern jako inspirację (skala podobienstwa = copy_similarity).

**Tryb "apify"**:
- Sprawdz czy `APIFY_TOKEN` jest w env: `[ -n "$APIFY_TOKEN" ] && echo OK || echo MISSING`
- Jesli MISSING: powiedz "Brak APIFY_TOKEN w env. Wracam do trybu swipe."
- Jesli OK: uruchom `python -m src.scrape.apify --niche skala --limit 20` (jesli ten
  moduł istnieje - sprawdz `find src/scrape -name "apify*"`)
- Wynik: lista {url, hook, transcript, views} dla 20 viralow.

---

### KROK 4: Generuj N skryptow

Dla **kazdego z N skryptow** wykonaj te kroki:

**4a. Wybierz USP + persona + CTA severity**

Z `config/icp.yaml` weekly_rotation - znajdz dzisiejszy dzien tygodnia (`date +%a` ->
mon/tue/wed/thu/fri/sat/sun), wez wpis dla tego dnia.

ALBO: ROTUJ przez N skryptow zeby kazdy mial inny USP + persona:
- Skrypt 1: Marek + USP "auto_publishing" + Pakiet 1 + CTA soft
- Skrypt 2: Marek + USP "ai_product" + Pakiet 3 + CTA mid
- Skrypt 3: Anna + USP "full_loop" + Pakiet 3 + CTA low (storytelling)
- Skrypt 4: Marek + USP "viral_basis" + Pakiet 1 + CTA mid
- Skrypt 5: Marek + USP "auto_publishing" + Pakiet 4 (VIP) + CTA high
- (cykluj jesli wiecej niz 5)

Z `config/product.yaml` weź:
- `usps[wybrany].long` - wpleciesz w body
- `packages[wybrany].price_founders_label` - w CTA
- `scarcity[]` - wybierz wpis pasujacy do severity
- `risk_reversal[]` - 1 frazy jesli CTA mid/hard

**4b. Wybierz HOOK pattern**

Z `signature_hooks` w user_voice.yaml masz 10 typow. Rotuj zeby kazdy skrypt mial
inny hook type. Hook musi:
- max 12 slow
- max 8 sekund mowienia
- zaczynac sie pattern interruptem (liczba/szok/kontrarian/pytanie/cytat)
- NIE zaczynac sie od `forbidden_starts` (Czesc/Hej/Witam/Dzisiaj/itd)
- NIE zawierac `banned_phrases`

10 typow hookow (skopiuj z user_voice.yaml + tutaj ponizej):

```
kontrarian:     "Twoj X NIE potrzebuje [popular advice]. Oto co dziala."
liczba:         "[Konkretna liczba] [grupa] [robi szokujaca rzecz]."
shock_claim:    "Kazdy filmik 5000 views. Bez wyjatku."
transformation: "Nie mam czasu na social media i wlasnie dlatego zarabiam [X]."
founder_line:   "Twoj biznes dziala, kiedy ty spisz."
curiosity_gap:  "Pokaze ci dlaczego twoj content NIE dziala (i co dziala zamiast)."
before_after:   "Rok temu publikowalem recznie. Teraz [X] - i robie wiecej views."
social_proof:   "[X] osob juz to ma. [Y] z nich [konkretny wynik] w [Z] dni."
problem_call:   "Jezeli [palace problem] - to nie twoja wina. System tak dziala."
hot_take:       "Niepopularna opinia: [contrarian truth o niszy]."
```

**4c. Generuj BODY (Hormozi PL)**

Struktura: `HOOK -> AGITATE (1-2 zdania bolu) -> SOLVE (3 numerowane kroki) -> PATTERN_INTERRUPT -> CTA`

Constraints:
- Total words: 75-150 (target dla 30-60s mowienia)
- Total seconds: ~target_seconds z parametrow
- Jezyk: zawsze "ty" (nigdy "wy" w pojedynczym), bezposredni, anti-guru
- Wpleciesz 1 voice_anchor ("Nie ma cudow", "Trzy systemy", "24/7", etc)
- Wpleciesz 1 sygnaturowa fraze (signature_phrases) JESLI naturalnie pasuje
- Persona Marek: liczby/ROI/MRR/lejek/rate
- Persona Anna: storytelling/empatia/krok-po-kroku/bezpiecznie

**SPECJALNE REGULY DLA value_only (intensity 0-15):**

Body MUSI byc PURE VALUE - widz wynosi konkretna wiedze nawet jak nigdy nie zobaczy Skali:
- **3 kroki SOLVE = framework/lessons/observations**, NIE opis produktu Skali
- Konkretne LICZBY (statystyki, koszty, czasy, %, ROI) - cytuj z rynku, nie ze Skali
- Konkretne PRZYKLADY (anegdoty, case studies, "ostatnio klient mi powiedzial...")
- **Maksymalnie 1 wzmianka o Skali** w body, jako "ja sam to mam zautomatyzowane" -
  NIE jako pitch. To anegdota a nie reklama. Zero cen, zero pakietow, zero "link w bio".
- Frameworks z nazwa: "Trzy filary contentu", "Reguly 80/20 w viralach", "Trzy
  pytania ktore zadaje sobie przed nagraniem" - to ZAPAMIETUJE sie i buduje autorytet
- Pattern interrupt mocniejszy - widz ma poczuc ZE NAUCZYL SIE czegos w 45 sekund

Wzorce hookow w value_only:
- "Wczoraj zobaczyles 100 filmikow. Zapamietales 2. Wiem dlaczego."
- "97% tworcow popelnia ten jeden blad. Powiem ci ktory."
- "Trzy reguly viralu ktorych nikt nie mowi glosno."
- "Powiem ci cos co kosztowalo mnie [konkretna liczba] do nauczenia."

Body example dla value_only (NIE TO ZAPISZ - to wzorzec):
```
HOOK: "97% tworcow popelnia ten jeden blad."

AGITATE: Nagrywasz 30 filmikow w miesiacu. Trzy maja 1000 views, reszta 200.
Mysleisz "to algorytm" - to nie algorytm.

SOLVE (3 kroki = real framework):
1. Pierwszy bial - nagrywasz POMYSL, nie HOOK. Hook to pierwsze dwa slowa
   ktore lamia scroll. Bez tego widz nigdy nie dojedzie do meritum.
2. Drugi blad - mowisz "dzisiaj pokaze" zamiast wbic od razu w temat.
   Algorytm widzi 2-sekundowy retention drop i wylacza filmik.
3. Trzeci - CTA na koncu. Algorytm liczy "completion rate". CTA "link w bio"
   zmniejsza completion bo widz wychodzi przed koncem.

PATTERN INTERRUPT: Ja sam to mam zautomatyzowane - generator analizuje 1000
viralow dziennie i wyciaga te wzorce za mnie. Ale wzorzec dziala niezaleznie
od tego czy uzywasz narzedzia, czy nagrywasz recznie.

CTA: Save sobie ten filmik - bedziesz wracal.
```

Jak widzisz - Skala wspomniana RAZ jako anegdota. 90% wartosci to konkretne
lessons ktore Marek/Anna moze uzyc OD JUTRA bez kupowania niczego.

**4d. CTA - dopasuj do intensity**

**value_only (intensity 0-15)** - TRUST BUILDING MODE:
NIE sprzedajesz. NIE wspominasz pakietow, cen, miejsc, quizu. Produkt moze
wyskoczyc raz w body jako "ja sam to mam zautomatyzowane" / "moj system to robi"
ale to ANEGDOTA, nie reklama. Na koncu wybierz JEDNO z:
- "Save sobie ten filmik na potem - bedziesz tu wracal."
- "Daj znac w komentarzu co Ty robisz inaczej."
- "Subskrybuj jak chcesz wiecej takich obserwacji."
- "Wiecej takich rzeczy na moim profilu."
- "Komentarz: 'tak' jak chcesz wiecej tego typu."
- LUB ZERO CTA - zakoncz konkretna mysla / pattern interruptem (najmocniejsze
  dla trust-building, widz sam Cie znajdzie)

NIE wspominaj o systemskala.pl, NIE wspominaj o "linku w bio", NIE wspominaj
o cenach. Trust mode = ZERO sprzedazy.

**soft (intensity 15-35)**:
> "Wbij w bio, zrob quiz w 60 sekund, zobaczysz ktory z 4 modeli pasuje do ciebie."

**mid (intensity 35-70)**:
> "Link w bio prowadzi do quizu - 7 pytan, masz darmowy plan. 50 miejsc Founders zostalo."

**hard (intensity 70-90)**:
> "Cena Founders -40% zlocked-in dozywotnio. Pakiet Komplet 1498 zl miesiac zamiast 7990. Link w bio."

**vip (intensity 90-100)**:
> "Otwieram 5 miejsc VIP. 3 miesiace jeden-na-jeden. Gwarancja 5 tysiecy zarobku albo kontynuacja gratis. Aplikuj w bio."

Dorzuc 1 element risk_reversal jesli intensity >= mid.

**4e. CAPTION + HASHTAGS + B-ROLL**

Caption (pod filmem): 2-4 zdania, summary obietnicy + CTA do quizu.

Hashtags: 18 tagow, mix:
- 50% niche-PL: #sidehustlepolska #aidlabiznesu #automatyzacjabiznesu #przedsiebiorcapl #solopreneurpl #onlinebusinesspl #pasywnydochod #aimarketing
- 30% broad PL+EN: #fyp #foryoupage #shorts #reels #viraltips #aitools #contentcreator #personalbranding
- 20% branded: #skala #systemskala #erykhajduczek #automatyzacja

B-roll suggestions: 3-5 propozycji shotow dla CapCut (np. "sek 5-8: shot Telegrama z 3 nowymi skryptami").

**4f. Critic pass (auto-review)**

Przed zapisaniem - sprawdz kazdy skrypt:
- [ ] Hook nie zaczyna sie od forbidden_starts
- [ ] Brak banned_phrases w body i CTA
- [ ] Hook max 12 slow, max 8 sek mowienia
- [ ] Body 75-150 slow
- [ ] Struktura HOOK->AGITATE->3 KROKI->PATTERN_INTERRUPT->CTA jest widoczna
- [ ] Persona-fit: Marek dostaje liczby, Anna dostaje storytelling

**Jesli intensity = soft/mid/hard/vip:**
- [ ] CTA zawiera link/quiz/checkout

**Jesli intensity = value_only:**
- [ ] CTA NIE zawiera "link w bio", NIE zawiera "quiz", NIE zawiera "Founders",
      NIE zawiera "Pakiet", NIE zawiera cen w PLN
- [ ] Maksymalnie 1 wzmianka o Skali w body (jako anegdota, nie pitch)
- [ ] 3 kroki SOLVE = real framework/lessons ktore widz moze uzyc bez kupowania
- [ ] CTA jest community-driven (save/comment/follow) lub w ogóle ZERO CTA

Jesli ktorys check fail - regeneruj ten skrypt (max 3 proby).

---

### KROK 5: Zapisz pliki

Stworz folder `scripts/YYYY-MM-DD/` (data dzisiejsza, format ISO).

Dla kazdego skryptu zapisz osobny plik:
`scripts/YYYY-MM-DD/NN-{hook_type}.md`

Gdzie NN = 01, 02, 03... i hook_type = founder_line/liczba/kontrarian/etc.

**Format pliku** (markdown):

```markdown
# Skrypt {NN}: {hook_type}

**Persona**: {marek|anna}  
**USP**: {auto_publishing|ai_product|full_loop|viral_basis}  
**Pakiet**: {1|2|3|4}  
**CTA intensity**: {soft|mid|hard|vip}  
**Ton**: {balanced|anti_guru|hormozi|storyteller}  
**Target dlugosc**: {target_seconds}s  
**Wygenerowany**: {timestamp ISO}

---

## HOOK (0-{hook_seconds}s)
> {hook tekst, max 12 slow}

**Tekst na ekranie**: `{krotki overlay, 3-5 slow}`

## BODY ({hook_seconds}-{body_end}s)

**Agitate**: {1-2 zdania bolu}

**Solve** (3 kroki):
1. {krok 1, 1 zdanie}
2. {krok 2, 1 zdanie}
3. {krok 3, 1 zdanie}

**Pattern interrupt**: {1 zdanie ktore lamie tempo - cytat/liczba/przyklad}

## CTA ({cta_start}-{target_seconds}s)
> {cta tekst}

---

## CAPTION
```
{2-4 zdania caption pod filmem}
```

## HASHTAGS
```
{18 hashtagow w jednej linii oddzielonych spacjami}
```

## B-ROLL SUGGESTIONS
- sek X-Y: {opis shotu}
- sek X-Y: {opis shotu}
- sek X-Y: {opis shotu}

## CRITIC SCORE
- Hook: PASS/FAIL ({powod jesli fail})
- Banned phrases: PASS/FAIL
- Struktura Hormozi: PASS/FAIL
- Persona-fit: PASS/FAIL
- Total: X/4
```

---

### KROK 6: Summary w chat

Po wszystkim - krotki message do uzytkownika:

```
✅ Wygenerowano {N} skryptow w scripts/YYYY-MM-DD/

1. {hook_type} ({persona}) - Pakiet {N} - Critic {X}/4
   "{pierwsze slowa hooka...}"
2. {hook_type} ({persona}) - ...
3. ...

📂 Pelne pliki: scripts/{YYYY-MM-DD}/

Co dalej:
- Otworz pliki w VS Code / czytaj `cat scripts/{data}/01-*.md`
- Nagraj pierwszy ktory ci sie podoba - 5 min pracy
- Jak chcesz wiecej / inne parametry - powiedz "wygeneruj kolejne X"
- Jak chcesz zaostrzyc krytyk - zwieksz effort_level (powiedz "effort 9")
```

---

## DODATKI - PEŁNE LIBRARY (referencja gdy configi nie istnieja)

### Banned phrases (NIE wolno uzyc)

Guru-PL cringe:
- "ostatnia szansa", "tylko dzisiaj", "OSTRZEGAM"
- "zostan milionerem", "wolnosc finansowa", "rzuc etat"
- "diamentowy mindset", "alfa", "kiss your job goodbye"

Kalka z angielskiego:
- "pozwol mi" (let me), "tutaj jest" (here is)
- "spojrz na to" (look at this), "to znaczy ze" (uzyj "czyli")

YouTube boomer-PL:
- "Witam serdecznie", "Mam nadzieje ze sie podobalo"
- "Subskrybujcie i lapcie kciuki", "Do zobaczenia w nastepnym"

FOMO cringe:
- "zegar tyka", "nie przegap", "obowiazkowo"

### Forbidden hook starts

NIE zaczynaj hooka od: "Czesc", "Hej", "Witam", "Dzisiaj", "Dzien dobry", "Drogi",
"W tym filmie", "Pokaze ci jak", "Mam dla was"

### Signature phrases Eryka (wpleciesz 1 jesli pasuje)

- "Twoj biznes dziala, kiedy ty spisz"
- "10 minut. Raz. Zero pracy potem."
- "Trzy systemy. Jedno ustawienie. Praca 24/7."
- "Nie ma cudow - jest system."
- "Ja sam testowalem to na 840 tysiacach subow."

### Voice anchors (wpleciesz 1 w body)

"Nie ma cudow", "Trzy systemy", "Jedno ustawienie", "24/7", "Bez logowania
do aplikacji", "10 minut setupu", "Konkretnie", "Pokaze ci to na liczbach"

### Hashtag pool (do mieszania 18 tagow)

**Niche PL (50%)**:
#sidehustlepolska #aidlabiznesu #automatyzacjabiznesu #przedsiebiorcapl
#solopreneurpl #onlinebusinesspl #pasywnydochod #aimarketing #marketingdigital
#biznesonlinepl #marketingpl

**Broad PL+EN (30%)**:
#fyp #foryoupage #shorts #reels #viraltips #aitools #contentcreator
#personalbranding #passiveincome #onlinebusiness #faceless #ai #automation

**Branded (20%)**:
#skala #systemskala #erykhajduczek #automatyzacja #aiwbiznesie

### Effort levels (jakosc vs szybkosc)

Jesli user mowi "effort N" lub w follow-up - mapuj:
- **1-4 (Fast)**: 1 iter generowania per skrypt, brak critic pass
- **5-7 (Standard, default)**: Generuj raz + critic pass + ewentualna regeneracja jesli FAIL
- **8-10 (Thorough)**: Wygeneruj 3 warianty per skrypt → wybierz najlepszy wg critic → polish style

### Multi-platform adaptacja (jesli user zapyta)

Domyslnie format = TikTok/Reels (45s, pionowy, captions). Jesli user mowi
"adaptuj na X":
- **YouTube Shorts**: dluzsze do 60s, mocniejszy hook (algorytm Search'a)
- **LinkedIn video**: dluzsze 60-90s, mniej slangu, wiecej liczb
- **Instagram Reels**: identycznie jak TT ale captions w karuzeli + 1 hashtag w komentarzu

---

## EDGE CASES

**Q: User nie odpowiada na AskUserQuestion (pomija)?**
A: Uzyj defaultow: 3 skrypty / balanced / soft CTA 45s / swipe mode.

**Q: User chce edytowac juz wygenerowany skrypt?**
A: Read pliku, zaproponuj 2-3 alternatywne hooki/CTA, zapytaj ktory uzyc, zapisz nadpisujac.

**Q: User chce inny jezyk?**
A: Brand voice jest w POLSKIM. Jesli user prosi EN - powiedz "Skala robi PL content,
ale moge zrobic EN wersje jako proba - powiedz ktory ze skryptow przetlumaczyc."

**Q: User chce konkretnyl niszy (nie skala)?**
A: Mowic: "Ten skill jest pod brand Skala. Dla innej niszy - musialbys przygotowac
analogiczne configi w config/ (product/icp/voice). Chcesz zebym to zrobil?"

**Q: Co jesli scripts/YYYY-MM-DD/ juz istnieje?**
A: Suffix `-v2`, `-v3` w nazwie folderu LUB napisz "Juz masz X skryptow z dzisiaj.
Nadpisac? Dolozyc? Suffix -v2?"

---

## NA KOŃCU - przypomnij siebie tych regul:

1. **NIGDY nie pisz "Czesc dzisiaj pokaze"** - to instant fail.
2. **Hook MUSI byc pattern interruptem** - liczba, szok, kontrarian, pytanie, cytat.
3. **W trybach soft/mid/hard/vip - CTA kieruje do BIO/QUIZU** - NIE do checkout direkt.
4. **W trybie value_only - ZERO sprzedazy.** Produkt to anegdota raz w body, nigdy w CTA.
   Domyslny tryb dla **trust-building stage** = value_only.
5. **Marek dostaje liczby. Anna dostaje storie.** Nigdy odwrotnie.
6. **Banned phrases = fail.** Jesli wypadnie w generowaniu - regeneruj.
7. **Pakiet 3 (KOMPLET) to 70% domyslnych CTA.** Pakiet 4 (VIP) tylko 10% i tylko hi-trust hooki.
8. **Founders -40% scarcity** - uzywaj naturalnie, nie spamuj. NIE w value_only.

## TRUST-BUILDING DOCTRINE (priorytet dla Eryka teraz)

Eryk jest w fazie **budowania zaufania**, nie konwersji. To znaczy:

- Domyslny mode = **value_only** (chyba ze user explicite poprosi inaczej)
- Kazdy skrypt MUSI dac konkretna wiedze nawet jak widz nigdy nie zobaczy Skali
- 3 kroki SOLVE = **real framework**, NIE feature list produktu
- Skala wspomniana max RAZ w body jako anegdota ("ja sam to mam zautomatyzowane" w
  kontekscie - to brzmi naturalnie i podswiadomie buduje pozycje eksperta)
- CTA = community-driven (save / comment / follow) lub ZERO CTA
- Hook musi obiecywac REAL LEARNING ("3 reguly", "97% bledow", "to czego nikt nie mowi") -
  to lamie scroll lepiej niz "pokaze ci jak"
- Pattern interrupt na koncu - mocny insight ktory widz wynosi i opowie kolezance

Ta doktryna obowiazuje DOMYSLNIE az do momentu gdy Eryk powie "wlaczamy sprzedaz".
