# Instalacja i aktualizacja

## Wybierz sposób instalacji

1. W Windows uruchom kreator `EwP-Setup-0.22.0.exe` i wykonaj opisane niżej kroki.
2. Do instalacji terminalowej pobierz ZIP Windows albo tar.gz/ZIP Ubuntu i użyj krótkich poleceń poniżej. Nie trzeba ręcznie klonować repozytorium ani wcześniej instalować Python i uv.
3. Jeśli pracujesz z repozytorium jako programista lub dotychczasowy użytkownik, zachowaj ten sposób i korzystaj z sekcji aktualizacji checkoutu. To nie jest instalacja zarządzana.

Instalator zarządzany jest nowy w 0.22.0. Paczki testowe są dostępne w przekazanej paczce oraz w zadaniu Actions „Installer build and Windows startup” repozytorium. Publiczne skrypty pobierania zaczną działać po publikacji pasującego wydania. Nie zgaduj adresu pobierania. Obecny EXE jest niepodpisany; nie dostarczono certyfikatu podpisywania kodu.

Obecne cele to Windows 11 x64 oraz Ubuntu 24.04/26.04, w tym WSL2. Wcześniejsze testy programu w Windows/WSL pozostają zaakceptowane. Nowy cykl instalacji zarządzanej ma rzeczywiste testy na VM Ubuntu; pełny test instalacji i usuwania na Windows 11 jest osobny od kompilacji lub uruchomienia okien na runnerze CI. Testowe GPU to RTX 3090 24 GB. Oczekiwanie działania na innych NVIDIA z co najmniej 8 GB VRAM nadal nie jest gwarancją.

## Kreator Windows

Uruchom EXE ze zwykłego konta użytkownika. Zawiera środowisko własnego GUI i sprawdzoną paczkę programu, a nie wielogigabajtowe modele mowy. Test hosta może przygotować małe tymczasowe środowisko Python instalatora i wymaga internetu. Sprawdź system i architekturę, dysk, sterownik NVIDIA przy lokalnym ASR oraz Visual C++ x64. Przycisk otwiera instalator wymaganego składnika Microsoft. Brakujący sterownik NVIDIA zainstaluj osobno po stronie hosta.

Wybierz pusty katalog aplikacji, zwykle `%LOCALAPPDATA%\EwPTranscripts`, osobny od nagrań. Istniejąca zarejestrowana instalacja jest proponowana automatycznie. Do aktualizacji i naprawy zachowaj tę lokalizację. Niepusty katalog bez znaczników instalatora jest odrzucany, więc stary checkout Git nie zostanie nadpisany.

Zaznacz modele lokalnego GPU, aby przygotować przypięte ASR, wyrównanie PL/EN, diarization i dane podziału zdań. Zaakceptuj warunki pyannote na swoim koncie HF, potwierdź pobranie i podaj prywatnie token tylko do odczytu. Kompletne snapshoty są używane ponownie; token może pozostać pusty, jeśli wszystko już jest dostępne. Nieudany test HF wskazuje problem tokenu, warunków lub połączenia przed pobraniem modeli. Token jest używany tylko tymczasowo i instalator go nie zapisuje.

Bez modeli lokalnych można sprawdzać i eksportować gotowe wyniki albo wybrać OpenRouter jako silnik ASR nagrania. Lokalne GPU pozostaje zwykłym domyślnym wyborem programu. Instalacja bez modeli nie wyraża zgody na wysłanie audio ani nie zmienia automatycznie silnika każdego nagrania.

Pole OpenRouter jest opcjonalne. Sprawdzenie wysyła tylko żądanie uwierzytelnienia i połączenia, bez audio. Instalacja z wypełnionym polem jawnie zapisuje klucz w tym samym magazynie systemowym, którego używa program. Nie ma zapisu awaryjnego jawnym tekstem. W aplikacji wybierz użycie zapisanego klucza, gdy chcesz go aktywować; zgoda na wysłanie i płatne wywołania pozostaje osobna. Praca lokalna nie wymaga OR. Zobacz [Ustawienia](settings.md).

Wybierz instalację, aktualizację, naprawę, przywrócenie poprzedniej wersji albo odinstalowanie. Kontynuuj pokazuje etapy i własną zębatkę, a diagnostykę w szczegółach technicznych. Testy hosta mają osobne podsumowanie. Zapisz raport zachowuje diagnostykę bez kluczy. Nie zamykaj kreatora w trakcie operacji. Po sukcesie uruchom program lub użyj skrótu na pulpicie. „Dodaj/usuń programy” udostępnia pasujący deinstalator.

## Instalacja terminalowa z pobranej paczki

PowerShell w Windows, w katalogu pobranego ZIP:

```powershell
Expand-Archive .\EwP-0.22.0-windows-x64.zip -DestinationPath .\EwPSetup
powershell -ExecutionPolicy Bypass -File .\EwPSetup\control\Install-EwP.ps1 -Bundle .\EwP-0.22.0-windows-x64.zip
```

Po zaakceptowaniu warunków modelu dodaj `-Local -AcceptModelTerms`, aby przygotować modele lokalne. Monit tokenu jest ukryty; pusta odpowiedź pozwala użyć kompletnych modeli. `-SaveOpenRouterKey` włącza osobny ukryty monit i jawny zapis OR w systemie. `-Root 'D:\Apps\EwP'` wybiera własny pusty katalog. Obejście polityki PowerShell dotyczy tylko tego uruchomienia. Ścieżki ze spacjami obejmuj cudzysłowami.

Ubuntu 24.04/26.04, w katalogu pobranego tar.gz:

```bash
mkdir -p EwPSetup
tar -xzf EwP-0.22.0-ubuntu-x64.tar.gz -C EwPSetup
bash EwPSetup/control/Install-EwP.sh install --bundle "$PWD/EwPSetup/bundle.zip"
```

Dodaj `--local --accept-model-terms` dla modeli, `--save-openrouter-key` dla ukrytego monitu OR lub `--root "$HOME/Apps/EwP"` dla innej lokalizacji. Brakujące pakiety Ubuntu można zainstalować po jawnym monicie sudo. Nie instaluj sterownika ekranu Linuksa wewnątrz WSL; CUDA udostępnia sterownik Windows. Zgodność z fizycznym Ubuntu trzeba potwierdzić wykonaniem, a nie wnioskować tylko z WSL.

Plik SHA256SUMS służy do sprawdzenia pobranych plików. Skrypty online `Install-EwP-0.22.0.ps1` i `.sh` są generowane z dokładnymi hashami paczek pasującego wydania; nie pobiorą nieopublikowanego wydania. Skrypty i GUI używają wspólnego mechanizmu, blokady zależności i zasad modeli.

## Aktualizacja zarządzana i poprzednia wersja

Zapisz pracę i kopię, zakończ zadania lub bezpiecznie je anuluj i zatrzymaj serwer. Samo zamknięcie karty nie wystarcza. Zarządzany launcher trzyma blokadę aktywności; aktualizacja i usuwanie odmawiają działania, gdy ta aplikacja pracuje. Zweryfikowaną blokadę martwego procesu można odzyskać po przerwaniu; żywy lub nieznany właściciel pozostaje chroniony.

Pobierz paczkę nowej wersji. Wskaż ją w kreatorze albo uruchom nowy instalator z tym samym katalogiem. Przykłady domyślnej lokalizacji:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\EwPTranscripts\Install-EwP.ps1" -Action update -Bundle 'C:\Downloads\NEW_WINDOWS_BUNDLE.zip'
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\EwPTranscripts\Install-EwP.ps1" -Action rollback
```

```bash
bash "$HOME/.local/share/ewp-transcripts/installation/Install-EwP.sh" update --bundle '/path/NEW_UBUNTU_BUNDLE.zip'
bash "$HOME/.local/share/ewp-transcripts/installation/Install-EwP.sh" rollback
```

Zastąp nazwę dużymi literami rzeczywistym pobranym plikiem. Aktualizacja i naprawa CLI zachowują poprzedni wybór modeli, chyba że podasz `--cloud-only`/`-CloudOnly` albo jawnie wybierzesz lokalne modele. Kompletne niezmienione modele nie wymagają ponownego pobrania. Nowe lub brakujące modele chronione nadal wymagają zgody i tokenu. Program sprawdza prywatny FFmpeg, przypięte zależności i numer aplikacji przed atomowym przełączeniem aktywnej wersji.

Nieudane przygotowanie zachowuje poprzednią aplikację. Rollback wybiera zachowaną sprawdzoną wersję i nie przepisuje danych użytkownika. To wydanie nie migruje obszarów ani profili. Nie zakładaj, że dowolna przyszła zmiana schematu pozwoli bezpiecznie wrócić do starszej wersji. Zachowywane są aktywne i bezpośrednio poprzednie środowisko. Starsze pliki programu są porządkowane po udanym przełączeniu, z zachowaniem dodanych plików projektu. Wyniki, modele, profile, słowniki i klucze nie są resetowane.

## Deinstalacja zarządzana

Użyj kreatora, „Dodaj/usuń programy” albo przygotuj podgląd w terminalu:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\EwPTranscripts\Install-EwP.ps1" -Action uninstall
```

```bash
bash "$HOME/.local/share/ewp-transcripts/installation/Install-EwP.sh" uninstall
```

Przeczytaj plan. Ponów z `-Yes`/`--yes`, aby potwierdzić. Opcjonalne `-RemoveModels`/`--remove-models` usuwa dokładne zarejestrowane snapshoty, a `-RemoveKey`/`--remove-key` wspólny zapis OR. To niezależne wybory; domyślnie pozostają zachowane. Niestandardowe lub nieweryfikowalne lokalizacje modeli są chronione. Bloby HF używane przez inne snapshoty pozostają; cały cache HF nie jest kasowany. Modele mogą być używane przez inne programy, więc sprawdź tę decyzję.

Oryginalne nagrania, publikacje i stan użytkownika nie należą do usuwania środowiska. Nieznane pliki dodane wewnątrz katalogu wersji także pozostają; dlatego katalog może nie być pusty po deinstalacji. Windows kończy usuwanie blokowanych plików po wyjściu kreatora i interpretera. Wpisy pulpitu i rejestru należące do innej instalacji nie są usuwane. Tymczasowe środowiska bootstrapu są sprzątane po zakończeniu skryptu. Uruchomienie, rollback i deinstalacja zainstalowanego programu w Ubuntu używają istniejącego prywatnego Pythona bez ponownego pobierania środowiska.

Starszy checkout Git nie jest instalacją zarządzaną i nie jest usuwany na podstawie zgadywanych ścieżek. Zachowaj kopię przed ręcznym porządkowaniem. Nowy instalator może działać obok niego i używać tych samych dokładnych modeli. Profile i obszary przenoś świadomie, sprawdzając ścieżki oryginalnych mediów.

## Instalacja i aktualizacja z repozytorium

Windows i WSL muszą mieć osobne repozytoria i środowiska. Do nowej instalacji źródłowej Windows przygotuj Git, uv, sterownik NVIDIA do lokalnego ASR i Visual C++ x64, a potem:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Install
uv run --locked --no-sync python scripts/setup-models.py
uv run --locked transcriber doctor --test-speech-runtime
uv run --locked transcriber gui
```

Dla świeżego checkoutu Ubuntu:

```bash
./scripts/install-fresh-ubuntu.sh --install
./scripts/setup-models.sh
uv run --locked transcriber doctor --test-speech-runtime
uv run --locked transcriber gui
```

Modele pobiera się jawnie. `--public-only` pomija chroniony diarizer i nie przygotowuje całego lokalnego procesu z wieloma mówcami. Brak HF_TOKEN nie przeszkadza przy kompletnych modelach offline. Zwykła transkrypcja nie pobiera brakujących modeli po cichu. API chmurowe nadal wymaga internetu i własnych zgód.

Zwykła aktualizacja repozytorium po zapisie pracy i zatrzymaniu serwera:

```text
git pull --ff-only
uv sync --locked
uv run --locked transcriber gui
```

Nie instaluj wszystkiego i nie pobieraj modeli po każdej aktualizacji. [Naprawy Windows](windows-native.md) lub [naprawy po aktualizacji Ubuntu](ubuntu-upgrade.md) używaj po odpowiednim błędzie diagnostyki. GUI podaje lokalny adres, zwykle `http://127.0.0.1:8765/`. Dostępne są `gui --no-open-browser` i `gui --port 8766`. Zamknięcie przeglądarki nie zatrzymuje przetwarzania. Przed przenoszeniem lub usuwaniem projektu przeczytaj [zapis pracy](saved-work.md), [pliki i eksporty](outputs.md) oraz [rozwiązywanie problemów](troubleshooting.md).
