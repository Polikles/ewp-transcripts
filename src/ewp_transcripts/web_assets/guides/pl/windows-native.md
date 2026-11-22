# Natywny Windows: instalacja i naprawa

1. Wykonaj [Instalację i aktualizację](installation.md): Git, uv, sterownik NVIDIA Windows i Microsoft Visual C++ x64.
2. W osobnym repozytorium Windows uruchom `powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Install`.
3. Do lokalnego ASR po przyjęciu warunków modelu wykonaj `uv run --locked --no-sync python scripts/setup-models.py`.
4. Wykonaj `uv run --locked transcriber doctor --test-speech-runtime`, a potem `uv run --locked transcriber gui`.

Obejście polityki PowerShell działa tylko dla tego uruchomienia. Skrypt używa Python 3.12, przypiętych pakietów CUDA 12.8 i współdzielonych plików FFmpeg 7.1.1 sprawdzanych SHA-256. Nie zmienia globalnego PATH, nie instaluje sterownika i domyślnie nie pobiera modeli. `-SetupModels` uruchamia osobny etap modeli, a `-PublicOnly` pomija snapshot chroniony. Nie współdziel środowiska wirtualnego z WSL.

Prywatny FFmpeg zwykle znajduje się w `%LOCALAPPDATA%\ewp-transcripts\ffmpeg-7`. Program przygotowuje wyszukiwanie DLL audio i Torch dla własnego procesu. Jawne `EWP_FFMPEG_PREFIX` może wskazywać inny zgodny katalog współdzielonej wersji z podkatalogiem `bin`. Sam systemowy FFmpeg lub kompilacja statyczna nie zapewniają DLL potrzebnych TorchCodec 0.7.

## Naprawa

Zapisz pracę i zatrzymaj GUI, a następnie uruchom:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Repair
uv run --locked transcriber doctor --test-speech-runtime
```

Przywraca to przypięte TorchCodec i pyannote oraz prywatny FFmpeg. Przy błędach CUDA, cuDNN i Visual C++ zachowaj diagnostykę zamiast losowo wymieniać pakiety. Nie zastępuj przypiętych współdzielonych bibliotek wersją FFmpeg 8 lub nowszą. Zwykła aktualizacja to `git pull` i `uv sync --locked`. Działająca instalacja nie wymaga regularnej reinstalacji.

Modele zwykle są w `%USERPROFILE%\.cache\huggingface`. Ścieżki typu `C:\Users\name\Podcast files\Żółć.wav` pozostają natywne. Wybieraj zwykłe katalogi użytkownika; katalogi systemowe i cele dowiązań są blokowane. Profil nie kopiuje nagrań: przenoś katalogi mediów i wyników osobno i sprawdzaj brakujące ścieżki.

Przy błędzie starego przygotowania modeli `Blocked import of regex` zaktualizuj kod i powtórz to samo polecenie. Obecny etap danych językowych działa w izolowanym procesie poza repozytorium. Nie trzeba wyłączać zabezpieczeń NLTK. Właściciel przetestował instalację, pracę lokalną i chmurową oraz ponowne uruchomienie na Windows 11 x64 z RTX 3090. To nie jest kwalifikacja każdego komputera.
