# Gotowy APK do instalacji

**Najnowsza wersja:** [`ReelSaver-1.1-release.apk`](./ReelSaver-1.1-release.apk) (~1.3 MB)

## Co nowego w 1.1

- **Logowanie do Instagrama (WebView)** — pobiera Reelsy też z prywatnych
  profili, do których masz dostęp. Po zalogowaniu apka używa wewnętrznego
  API mobilnej apki IG.
- **Transkrypcja** — Whisper (OpenAI) + tłumaczenie GPT-4o-mini na
  wybrany język. Włącz w ustawieniach apki, podaj klucz OpenAI.
- Lepsza obsługa CDN-ów Instagrama (poprawne `Referer`).

## Instalacja

1. Otwórz tę stronę w przeglądarce na telefonie.
2. Stuknij plik APK powyżej → **Pobierz**.
3. Otwórz pobrany plik (z paska powiadomień lub z folderu Pobrane).
4. Jeśli system zablokuje: **Ustawienia** → zezwól danej przeglądarce na
   instalowanie nieznanych aplikacji → wróć i **Zainstaluj**.
5. Po instalacji: zezwól na powiadomienia, otwórz apkę, **zaloguj się
   do Instagrama** (z konta zapasowego — patrz ostrzeżenie niżej).

> Aktualizacja z 1.0 — kluczem podpisującym jest standardowy debug keystore
> Android Studio. Jeśli twój debug keystore się różni od mojego (np.
> instalujesz pierwszy raz na świeżym telefonie po wcześniejszej wersji
> 1.0 zbudowanej gdzie indziej), Android odmówi update'u — odinstaluj 1.0
> i zainstaluj 1.1 od zera.

## Klucz OpenAI

Transkrypcja wymaga klucza z https://platform.openai.com/api-keys.
Wklej go w apce w sekcji **Transkrypcja**. Koszty: ~0.006 USD/minutę audio
+ ułamki centa za tłumaczenie. Limit pliku Whisper: **25 MB** (Reelsy/TikToki
mieszczą się prawie zawsze).

## Ostrzeżenia

- **Logowanie do IG = ryzyko bana konta.** Instagram wykrywa
  zautomatyzowane pobieranie plików. Używaj **konta zapasowego**, nie
  głównego. Apka nie wysyła nigdzie twoich ciasteczek poza serwery
  Instagrama.
- Klucz OpenAI trzymany jest w SharedPreferences telefonu (nie w chmurze).
  Jeśli zgubisz telefon, wyrejestruj klucz w panelu OpenAI.
- TikTok działa publicznie bez logowania.
