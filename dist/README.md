# Gotowy APK do instalacji

**Najnowsza wersja:** [`ReelSaver-1.2-release.apk`](./ReelSaver-1.2-release.apk) (~1.3 MB)

## Co nowego w 1.2

- **Tryb publiczny — bez ryzyka bana konta IG.** Apka otwiera w tle
  stronę `snapinsta.app` (popularny IG downloader), wstawia twój link,
  klika Pobierz i przechwytuje gotowy URL filmu. Dokładnie to, co byś
  robił ręcznie. Nie używa twojej sesji IG.
- Tryb zalogowany pozostaje opcjonalny — tylko jeśli chcesz pobierać
  prywatne posty (do tego trzeba twojej sesji, nie ma cudów).
- Przełącznik trybu na ekranie głównym apki.

## Co nowego w 1.1 (poprzednie)

- Logowanie do Instagrama (WebView) i pobieranie z `i.instagram.com/api`.
- Transkrypcja przez Whisper + tłumaczenie przez GPT-4o-mini.

## Domyślne ustawienia

- **Tryb pobierania IG: Publiczny** (bezpieczny).
- **Auto-transkrypcja: wyłączona**. Włącz w ustawieniach po wpisaniu klucza
  OpenAI.

## Instalacja

1. Otwórz tę stronę w przeglądarce na telefonie.
2. Stuknij plik APK powyżej → **Pobierz**.
3. Otwórz pobrany plik. Jeśli system zablokuje: **Ustawienia** → zezwól
   przeglądarce na instalowanie nieznanych aplikacji → wróć i **Zainstaluj**.
4. Po instalacji: zezwól na powiadomienia.
5. Otwórz dowolny Reels → **Udostępnij → ReelSaver**.

> **Aktualizacja z 1.0/1.1:** ten sam podpis (debug keystore tej maszyny).
> Powinno się zainstalować jako update. Jeśli Android marudzi „inny podpis",
> odinstaluj poprzednią i postaw 1.2 czysto.

## Jak działa tryb publiczny

1. W IG stuknij **Udostępnij → ReelSaver**.
2. Apka otwiera ukryte okno z `snapinsta.app`, wstawia twój link
   przez JavaScript i klika **Pobierz**.
3. Kiedy snapinsta zwraca link MP4, apka go przechwytuje i pobiera
   wprost do galerii (`Movies/ReelSaver`).
4. Okno snapinsta zamyka się automatycznie.

Jeśli snapinsta wymaga captchy — zobaczysz ją, klikniesz, dalej leci
automatycznie. Jeśli `snapinsta.app` jest chwilowo offline — pobieranie
nie zadziała; zwróć uwagę i daj znać, dorzucę alternatywne serwisy.

## Tryb zalogowany — kiedy włączać

Tylko jeśli realnie chcesz pobierać posty z **prywatnych** profili,
do których jesteś zalogowany. Loguj się z **konta zapasowego**.
Apka nie wysyła twoich ciasteczek nigdzie poza Instagram.

## Klucz OpenAI (transkrypcja)

Klucz: https://platform.openai.com/api-keys. Wklej w sekcji
**Transkrypcja**. Koszty: ~0.006 USD/minutę audio + ułamki centa
za tłumaczenie. Limit Whispera: **25 MB** (Reelsy/TikToki się mieszczą).

## TikTok

TikTok pobiera się wprost (publicznie, bez logowania) — niezależnie
od wybranego trybu IG.
