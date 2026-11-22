# Instalacja i aktualizacja

## Wybór środowiska

Windows 11 x64 oraz WSL2 z Ubuntu 24.04/26.04 korzystają z tego samego repozytorium i procesu pracy. Każdy system musi mieć osobny checkout i środowisko wirtualne. Natywna instalacja i praca w Windows przeszły testy właściciela; nie oznacza to sprawdzenia każdej konfiguracji Windows i GPU.

Lokalne ASR wymaga sterownika NVIDIA, GPU z CUDA i przypiętych modeli lokalnych. Testy wykonano na RTX 3090 z 24 GB VRAM. Inne GPU NVIDIA z co najmniej 8 GB VRAM powinny działać, ale nie ma takiej gwarancji. Zarezerwuj co najmniej 20 GB na środowisko i modele oraz dodatkowe miejsce na nagrania, tymczasowe audio i wyniki. Wielkość pobierania zależy od pamięci podręcznej i wybranych opcji.

ASR w chmurze korzysta z FFmpeg i środowiska programu, ale nie uruchamia lokalnych modeli WhisperX, wyrównania ani diarization. Również sprawdzanie istniejących wyników i eksport nie inicjują modeli ML. W konfiguracji celowo korzystającej tylko z chmury test lokalnych modeli może zgłaszać ich brak; odróżnij to od problemów narzędzi multimedialnych lub dostawcy. Zwykły instalator nadal przygotowuje środowisko zgodne z plikiem blokady.

## Nowa instalacja Windows

1. Zainstaluj Git, sterownik NVIDIA do lokalnego ASR oraz Microsoft Visual C++ x64 Redistributable. Zainstaluj uv i otwórz ponownie PowerShell:

```powershell
winget install --id astral-sh.uv --exact
```

2. Sklonuj repozytorium do zwykłego katalogu użytkownika i przejdź do niego:

```powershell
git clone https://github.com/Polikles/ewp-transcripts.git
cd ewp-transcripts
powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Install
```

3. Do lokalnego ASR jawnie pobierz przypięte modele:

```powershell
uv run --locked --no-sync python scripts/setup-models.py
```

4. Sprawdź biblioteki przetwarzania mowy i uruchom GUI:

```powershell
uv run --locked transcriber doctor --test-speech-runtime
uv run --locked transcriber gui
```

Skrypt używa Python 3.12, przypiętych bibliotek Torch/CUDA i prywatnego FFmpeg ze współdzielonymi DLL. Domyślnie nie instaluje sterownika ani nie pobiera modeli. Lokalizację bibliotek i naprawę opisuje [instrukcja Windows](windows-native.md).

## Nowa instalacja WSL

1. Zainstaluj WSL2 oraz Ubuntu 24.04 lub 26.04. Zainstaluj sterownik NVIDIA po stronie Windows z obsługą CUDA w WSL. Repozytorium i większe pliki robocze najlepiej umieścić w systemie plików Linuksa. Nie instaluj linuksowego sterownika ekranu wewnątrz WSL.
2. W Ubuntu zainstaluj Git i pobierz repozytorium:

```bash
sudo apt update
sudo apt install git
git clone https://github.com/Polikles/ewp-transcripts.git
cd ewp-transcripts
./scripts/install-fresh-ubuntu.sh --install
```

3. Jeśli uv nie jest dostępne w PATH, otwórz nową powłokę. Do lokalnego ASR jawnie przygotuj modele, sprawdź środowisko i uruchom program:

```bash
./scripts/setup-models.sh
uv run --locked transcriber doctor --test-speech-runtime
uv run --locked transcriber gui
```

Instalator pyta o zmiany systemowe, instaluje przypięte zależności i sprawdza biblioteki audio. W razie niezgodnego ABI bibliotek systemowych może przygotować prywatne biblioteki FFmpeg 7. Pobranie modeli jest osobnym, jawnym krokiem.

## Dostęp do modeli i praca offline

Przed pobraniem `pyannote/speaker-diarization-community-1` zaakceptuj warunki tego modelu w Hugging Face. Podaj token tylko do odczytu w prywatnym monicie; nie umieszczaj go w poleceniu ani wspólnym dokumencie. Opcja `--public-only` pobiera publiczne modele ASR, wyrównania i dane językowe, pomijając chroniony diarizer. Nie przygotowuje pełnej lokalnej obsługi zmiksowanych mówców.

Oba skrypty modeli obsługują `--help`, `--yes` i `--public-only`. Domyślna konfiguracja przypina rewizje ASR large-v2, wyrównania PL/EN i pyannote. Modele są zwykle w `~/.cache/huggingface`, a w Windows w `%USERPROFILE%\.cache\huggingface`. Zwykła lokalna transkrypcja nie pobiera po cichu brakującego modelu. Brak `HF_TOKEN` nie przeszkadza, gdy wszystkie potrzebne snapshoty są już dostępne. Opcjonalne API dostawców nadal wymagają internetu.

## Uruchamianie, zatrzymywanie i aktualizacja

Polecenia wykonuj z repozytorium transkrybera, a nie z osobnego repozytorium waveform:

```text
uv run --locked transcriber gui
```

Otwórz wypisany adres `http://127.0.0.1:8765/`. Użyj `gui --no-open-browser`, aby otworzyć przeglądarkę samodzielnie, albo `gui --port 8766`, jeśli domyślny port jest zajęty. Zamknięcie karty przeglądarki nie zatrzymuje transkrypcji. Zapisz stan pracy i poczekaj na zakończenie lub bezpieczne anulowanie zadań przed zatrzymaniem serwera przez Ctrl+C.

Zwykła aktualizacja nie wymaga nowej instalacji:

```text
git pull
uv sync --locked
uv run --locked transcriber gui
```

Zatrzymaj serwer przed aktualizacją; wcześniej zapisz stan pracy i kopię zapasową. Nie pobieraj ponownie modeli i nie instaluj składników Windows po każdej aktualizacji. Doctor jest przydatny po instalacji, zmianie systemu lub bibliotek i przy odpowiednim błędzie. Naprawiaj lub reinstaluj zależności, gdy uzasadnia to diagnostyka. [Rozwiązywanie problemów](troubleshooting.md) obejmuje uruchamianie i aktualizacje Ubuntu.

## Usuwanie i przyszły instalator

Pełny deinstalator z jawnym wyborem usuwania modeli, samodzielny instalator graficzny Windows, skrót na pulpicie i wpis Dodaj/usuń programy są zaplanowane. Obecny skrypt instalacji z repozytorium ich nie udostępnia. Przed ręcznym usunięciem repozytorium lub pamięci podręcznej zachowaj wyniki, katalogi zapisów pracy i prywatne słowniki. Sprawdź, czy inne programy nie używają tych samych snapshotów Hugging Face. Klucz w magazynie systemowym jest osobnym zapisem; w razie potrzeby usuń go jawnie z programu. Nie podajemy automatycznej komendy usuwania, która musiałaby zgadywać przeznaczenie współdzielonych modeli i danych użytkownika.
