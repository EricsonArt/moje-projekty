# ReelSaver

Aplikacja na Androida do zapisywania filmów z Instagrama (Reels) i TikToka
przez systemowy „Udostępnij". Bez bąbelków, bez nakładek na ekranie, bez
usługi dostępności.

## Jak działa

1. W Instagramie / TikToku stuknij **Udostępnij** (strzałka).
2. Z arkusza Androida wybierz **ReelSaver**.
3. Apka pobierze plik MP4 i zapisze w `Movies/ReelSaver/` (galeria).
4. Po zakończeniu pojawia się powiadomienie — stuknij, aby otworzyć film.

Apka nie ma żadnego stałego UI nakładającego się na inne aplikacje.
Ekran główny pokazuje tylko instrukcję i komunikaty o błędach.

## Wymagania

- Android 8.0 (API 26) lub nowszy.
- Połączenie z internetem.
- Powiadomienia (Android 13+ poprosi o zgodę przy pierwszym uruchomieniu).

## Budowanie APK

### Z Android Studio

1. Otwórz katalog projektu w Android Studio (Hedgehog 2023.1.1 lub nowsze).
2. Poczekaj, aż Gradle pobierze zależności i SDK.
3. **Build → Build APK(s)** — APK wyląduje w
   `app/build/outputs/apk/debug/app-debug.apk`.

### Z linii poleceń

Wymaga zainstalowanego Android SDK i ustawionego `ANDROID_HOME`
(lub `local.properties` z `sdk.dir=<ścieżka>`).

```bash
# Debug (do testów):
./gradlew :app:assembleDebug
# → app/build/outputs/apk/debug/app-debug.apk

# Release (zminifikowana, podpisana kluczem debug):
./gradlew :app:assembleRelease
# → app/build/outputs/apk/release/app-release.apk
```

## Instalacja na telefonie

1. Włącz **Instalowanie z nieznanych źródeł** dla menedżera plików /
   przeglądarki, której użyjesz do otwarcia APK.
2. Skopiuj `app-debug.apk` na telefon (USB, Google Drive, itp.).
3. Otwórz plik na telefonie i potwierdź instalację.
4. Po pierwszym uruchomieniu zezwól na powiadomienia.

> ReelSaver **nie wejdzie do Google Play** — sklep zabrania apek do
> pobierania treści z portali stron trzecich. Instalujesz tylko jako APK.

## Struktura projektu

```
app/src/main/
├── AndroidManifest.xml          # rejestracja Share Intent + service
└── kotlin/com/reelsaver/app/
    ├── MainActivity.kt          # ekran główny (Compose, instrukcja)
    ├── ShareReceiverActivity.kt # odbiorca ACTION_SEND
    ├── DownloadService.kt       # foreground service + powiadomienia
    ├── extractor/
    │   └── VideoExtractor.kt    # pobranie URL-a wideo z IG/TikToka
    ├── storage/
    │   └── MediaStoreSaver.kt   # zapis do galerii (Scoped Storage)
    └── ui/
        └── Theme.kt
```

## Co robi każdy element

- **`ShareReceiverActivity`** — niewidoczna aktywność (`Theme.NoDisplay`)
  zarejestrowana jako handler `ACTION_SEND` z mime `text/plain`. Wyciąga
  pierwszy URL z udostępnionego tekstu i deleguje pobieranie do serwisu.
- **`DownloadService`** — `LifecycleService` w foregroundzie z
  powiadomieniem o postępie. Wywołuje `VideoExtractor.extract`,
  potem `MediaStoreSaver.saveVideo`.
- **`VideoExtractor`** — dla Instagrama parsuje meta tag `og:video` ze
  strony Reela; dla TikToka parsuje JSON z `__UNIVERSAL_DATA_FOR_REHYDRATION__`.
- **`MediaStoreSaver`** — zapis przez `MediaStore.Video` z
  `RELATIVE_PATH = Movies/ReelSaver`, zgodnie ze Scoped Storage (Android 10+).

## Ograniczenia i utrzymanie

- **Instagram regularnie zmienia HTML** — ekstraktor będzie wymagać
  aktualizacji co kilka miesięcy. Jeśli przestanie działać, zacznij
  od sprawdzenia, czy `og:video` nadal istnieje w odpowiedzi.
- **Prywatne profile / treści za logowaniem** — apka nie ma sesji,
  więc nie pobierze ich. Tylko publiczne posty.
- **Zdjęcia, karuzele, wątki** — obecna wersja obsługuje wyłącznie
  pojedyncze filmy. Karuzele wymagałyby dodatkowej logiki.

## Aspekty prawne

Pobierając cudze treści, łamiesz regulamin Instagrama / TikToka
(nawet jeśli jest to technicznie możliwe). Używaj wyłącznie do:

- własnych filmów,
- treści za wyraźną zgodą autora,
- użytku osobistego (oglądanie offline) zgodnego z lokalnym prawem.

Autor apki nie odpowiada za sposób jej użycia.
