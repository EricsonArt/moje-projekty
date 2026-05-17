Tu wrzucasz pliki cookies wyeksportowane z przegladarki.

Potrzebne pliki (jezeli uzywasz tych platform):
  tiktok.txt       - dla TikTok kanalow
  instagram.txt    - dla Instagram kanalow
  youtube.txt      - OPCJONALNE, tylko jak YT bedzie blokowal

JAK WYEKSPORTOWAC COOKIES:

1. Zainstaluj w przegladarce rozszerzenie "Get cookies.txt LOCALLY"
   (Chrome / Edge / Firefox - szukaj w sklepie)
   - autor: Rahul Shaw / open source
   - WAZNE: NIE wersja "Get cookies.txt" bez "LOCALLY" (tamta wysyla cookies do internetu!)

2. Zaloguj sie normalnie na TikTok / Instagram w przegladarce.

3. Na zalogowanej stronie kliknij ikonke rozszerzenia (gora po prawej).
   Klik "Export As" -> "Netscape format" -> zapisuje plik cookies.txt.

4. Zmien nazwe pliku na:
   - tiktok.txt    (jezeli cookies sa z tiktok.com)
   - instagram.txt (jezeli z instagram.com)

5. Wrzuc plik do tego folderu: data/cookies/

UWAGA - BEZPIECZENSTWO:
  - Ten folder jest w .gitignore - cookies NIGDY nie ida na GitHuba.
  - Cookies = sesja zalogowania. Kto je ma, ma dostep do Twojego konta.
  - Nie wysylaj nikomu plikow cookies.txt
  - Wymieniaj co 1-2 tygodnie (TT i IG czasem wygasaja sesje)

JEZELI PIPELINE MOWI "Cookies expired" / "Login required":
  Zaloguj sie ponownie w przegladarce -> wyeksportuj cookies od nowa -> nadpisz plik.
