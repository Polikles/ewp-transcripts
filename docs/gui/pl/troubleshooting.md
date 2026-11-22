# Rozwiązywanie problemów

1. Zapisz możliwą do zachowania pracę i zanotuj kod diagnostyczny, wersję programu, system oraz wykonywaną czynność.
2. Przeczytaj odpowiedni punkt niżej. Rozwijaj techniczny JSON, gdy jest potrzebny.
3. Po usunięciu przyczyny ponów czynność jawnie. W zwykłym zgłoszeniu nie ujawniaj klucza ani prywatnego audio i transkrypcji.

## Nie znaleziono transcriber

`Failed to spawn: transcriber` występuje przed otwarciem GUI. Sprawdź, czy jesteś w `ewp-transcripts`, a nie `ewp-waveform`, oraz czy `pyproject.toml` i `uv.lock` należą do tego programu. Wykonaj `uv sync --locked`, a potem `uv run --locked transcriber --help`. Nie współdziel `.venv` między Windows a WSL. Środowisko można odtworzyć; wyniki i modele są osobno.

## Serwer niedostępny, Informacje pokazują Loading, kolejka nie odświeża się

Sprawdź, czy serwer nadal działa w terminalu, i użyj wypisanego adresu i portu. Pobierz aktualny kod, zatrzymaj i uruchom serwer, a potem odśwież stronę, aby JS i serwer były zgodne. Błąd inicjalizacji przeglądarki może wystąpić przy dostępnym serwerze; zachowaj jego kod. Sam nieodświeżany widok nie dowodzi zawieszenia GPU. Zamknięcie przeglądarki nie zatrzymuje pracy. W razie potrzeby po przygotowaniu serwera wczytaj zapisany obszar.

## Niewłaściwy katalog wyników albo powtórzone pliki

Wszystkie aktywne zadania używają jednego katalogu wyników. Przed zmianą zakończ lub usuń przygotowane zadania. Sama historia końcowa nie blokuje katalogu. Planowanie obejmuje wszystkie wybrane pliki spoza kolejki; nie trzeba osobno sprawdzać ani wybierać jednego odcinka. Jednakowa nazwa i treść oznaczają jeden wybór. Różne pliki z tym samym ID nagrania wymagają celowo różnych tożsamości; nie usuwaj stanów JSON w celu obejścia kontroli.

## Lokalne ASR nie działa mimo działającego ffmpeg

Otwórz Ustawienia i informacje → test lokalnych zależności. Sprawdź nieudany test speech_runtime i doctor. Działające polecenie ffmpeg nie dowodzi zgodności ABI bibliotek FFmpeg z TorchCodec, Torch i CUDA. Jeśli błąd zaczął się po aktualizacji Ubuntu 24 → 26, wykonaj [naprawę po aktualizacji](ubuntu-upgrade.md). Windows ma [własny skrypt naprawy](windows-native.md). Zapisz pracę i zatrzymaj serwer przed zmianą bibliotek. Nie twórz pozornych dowiązań `libavutil` i nie aktualizuj losowo Torch i Codec.

## Brakuje modelu lub danych językowych

Po zaakceptowaniu wymaganych warunków uruchom jawne przygotowanie modeli dla swojego systemu. `HF_TOKEN` jest potrzebny do chronionego pobrania, nie do pracy z kompletnymi modelami lokalnymi. Jeśli Windows zgłasza `Blocked import of regex`, pobierz aktualny skrypt z izolowanym pobieraniem danych językowych i ponów `uv run --locked --no-sync python scripts/setup-models.py`. Nie wyłączaj zabezpieczenia NLTK. Błąd przygotowania modelu różni się od awarii dekodowania po udanym przygotowaniu.

## OpenRouter: brak klucza, zgody albo czasów słów

Przed uruchomieniem kolejki wpisz klucz lub użyj zapisanego. Sam test wpisanego klucza go nie aktywuje. Zaznacz nową zgodę dla obecnych zadań chmurowych. Klucz i zgoda nie są częścią zapisu pracy. Brak lub błędne uwierzytelnienie chmury blokuje całą kolejkę mieszaną przed przetwarzaniem.

Odpowiedź ASR bez czasów słów nie pozwala przygotować napisów. To problem odpowiedzi modelu, dostawcy lub punktu końcowego, a nie brak ścieżki wejściowej obszaru. Odśwież dostępność modeli i ceny, sprawdź środki i wybierz obsługiwaną ścieżkę lub model ze znacznikami słów przed jawnym ponowieniem. Program ogranicza Whisper do znanych tras obsługujących czasy i nadal sprawdza każdą odpowiedź. Zmiana modelu może kosztować; nie ma automatycznego płatnego przełączania. Zachowaj JSON błędu; jego usunięcie nie naprawi odpowiedzi dostawcy.

Przy korekcie i tłumaczeniu przez API sprawdź także gotowość modelu i endpointu oraz zgodę konkretnego etapu. Wynik pozostaje wstępny do ręcznej weryfikacji.

## Nie widać zapisu albo nie można zapisać obszaru

Otwórz zapisaną pracę; dostępne ostatnie katalogi są przywoływane automatycznie. W razie potrzeby wskaż właściwy katalog i odśwież albo otwórz manifest bezpośrednio. Wiersz pliku zapisu pokazuje lokalizację starszego zapisu. Nowe domyślnie trafiają do katalogu wyników, jeśli opcjonalne pole jest puste. Starszy zapis prywatny lub niestandardowy zachowuje swój katalog. Osobną kopię twórz przez Zapisz jako nowy i inną nazwę. Powtórzone nazwy są celowo odrzucane. ZIP samego katalogu wyników nie zawiera manifestu zapisanego gdzie indziej.

Przy przeniesionych plikach odtwórz media, wyniki i ukryte katalogi albo użyj poprawnie przeniesionego obszaru. Profil sam nie zawiera mediów. Wczytanie nie uruchamia ASR, a plany wymagają nowego potwierdzenia. Nieudany lub anulowany wiersz ponawiaj jawnie; nie usuwaj ręcznie plików błędu jako sposobu odzyskiwania.

## Nieaktywny zapis, eksport lub odtwarzacz

Dla źródła Zatwierdź sprawdza szkic. Potem ręczna weryfikacja i Zapisz i przygotuj do eksportu włączają eksport. Dla tłumaczenia Zastosuj tłumaczenie i sprawdzenie znaczenia są osobne od zapisu końcowego i eksportu. Nowa edycja wymaga ponownego sprawdzenia. Puste jednostki wymagają zgody na celowe pominięcia. Błędny hash lub pochodzenie wymaga dokładnego źródła i rewizji, a nie zmiany ID.

Odsłuch wymaga wszystkich niezmienionych ścieżek. Po ich przywróceniu przeładuj audio. Miks korzysta ze wspólnego czasu zero. Sekcje edytora nie wyznaczają podziału napisów. Odświeżanie eksportów wyszukuje zapisane pliki bez ASR i zmiany treści.

## Komunikaty terminala

Ostrzeżenie ONNX o wykrywaniu urządzeń `/sys/class/drm` może wystąpić w WSL przy działającym CUDA. Sprawdź doctor i rzeczywisty wynik zadania. Informacja Wav2Vec2 o `masked_spec_embed` jest ostrzeżeniem ładowania modelu i sama nie dowodzi awarii transkrypcji. Nie trenuj modelu tylko po to, aby ją uciszyć. Przy nieudanym zadaniu sprawdź właściwy kod błędu i biblioteki mowy. Przewijanie lub zamykanie odtwarzacza może przerwać strumień HTTP; zwykłe rozłączenia są obsługiwane bez traktowania ich jako awarii ASR. Nowy nieobsłużony traceback zgłoś wraz z czynnością i kodem, bez prywatnych danych.
