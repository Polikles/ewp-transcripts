# Dostęp Hugging Face do modeli lokalnych

Do pobrania przypiętego modelu `pyannote/speaker-diarization-community-1` instalator potrzebuje
**tokenu odczytu**, a nie hasła do konta. Token nie zastępuje zgody na dostęp do modelu.
Przy pracy przez OpenRouter lub weryfikacji bez modeli lokalnych pomiń ten krok.

1. [Załóż konto Hugging Face](https://huggingface.co/join), potwierdź adres e-mail i zaloguj się.
2. Otwórz [stronę modelu pyannote](https://huggingface.co/pyannote/speaker-diarization-community-1).
   Wypełnij formularz dostępu i zaakceptuj warunki. Jeśli strona wymaga zatwierdzenia, poczekaj na dostęp.
3. Na koncie otwórz **Settings → Access Tokens** lub [ustawienia tokenów](https://huggingface.co/settings/tokens).
4. Wybierz **Create new token**, dostęp **Read**, nadaj rozpoznawalną nazwę i utwórz token.
   Skopiuj go prywatnie. Uprawnienie zapisu nie jest potrzebne. Przy tokenie fine-grained trzeba
   osobno zezwolić na odczyt tego repozytorium z ograniczonym dostępem; zwykły Read jest prostszy.
5. W instalatorze wybierz **Podaj token Hugging Face**, wklej go do maskowanego pola i poczekaj
   na automatyczne sprawdzenie. **Sprawdź token** powtarza test, a **OK** przyjmuje tylko prawidłowy token.
6. Okno się zamknie, a główny ekran pokaże **Token prawidłowy**. Wtedy zaznacz **Zaakceptowałem
   warunki pyannote w Hugging Face**. To zaznaczenie nie wysyła formularza dostępu do Hugging Face.

Test odczytuje punkt kontroli dostępu do modelu; nie wysyła nagrań ani transkrypcji. Token pozostaje
wyłącznie w pamięci instalatora i jest przekazywany procesowi jawnego pobierania modeli. Nie trafia
do profilu, raportu JSON, argumentów polecenia ani tekstowej konfiguracji. Zamknięcie/anulowanie
czyści pola; instalator nie zapisuje trwałego logowania do konta Hugging Face.

- `HF_HTTP_401`: sprawdź, czy skopiowano sam token oraz czy nie wygasł lub nie został odwołany.
- `HF_HTTP_403`: zaloguj się na to samo konto, zaakceptuj warunki modelu i sprawdź dostęp do odczytu.
- `HF_CONNECTION_FAILED`: sprawdź sieć/proxy i ponów próbę; nie wyłączaj sprawdzania certyfikatów.

Nie wklejaj tokenów do zgłoszeń, zrzutów ani raportów. Po pobraniu modeli możesz odwołać token
w ustawieniach HF. Kompletne przypięte pliki są używane ponownie; kreator graficzny mimo to sprawdza
dostęp przed włączeniem potwierdzenia warunków. Utrzymanie z terminala może używać pełnego cache
bez nowego tokenu, zgodnie z [instrukcją instalacji](../docs/gui/pl/installation.md).

Źródła: [tokeny HF](https://huggingface.co/docs/hub/security-tokens),
[dostęp do modeli z warunkami](https://huggingface.co/docs/hub/models-gated).
