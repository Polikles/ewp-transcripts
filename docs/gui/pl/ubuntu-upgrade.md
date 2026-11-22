# Aktualizacja Ubuntu: naprawa bibliotek mowy

1. Zapisz pracę, zatrzymaj GUI i zachowaj szczegóły nieudanego testu speech_runtime.
2. W repozytorium transkrybera uruchom `bash scripts/repair-dependencies.sh`.
3. Wykonaj `uv run --locked transcriber doctor --test-speech-runtime`, uruchom GUI i powtórz test lokalnych zależności.
4. Po udanych testach jawnie ponów nieudane lub anulowane zadanie. Ta naprawa nie wymaga pobierania modeli.

## Jeśli problem zaczął się po Ubuntu 24 → 26

Ubuntu 24.04 i 26.04 w WSL2 są akceptowane. Aktualizacja systemu może zastąpić biblioteki FFmpeg, podczas gdy przypięte środowisko Python nadal korzysta z TorchCodec 0.7. Dostępność poleceń `ffmpeg` i `ffprobe` nie dowodzi zgodności bibliotek współdzielonych. Błędy braku `libavutil.so.56` do `.59` wskazują potrzebę sprawdzenia ABI.

Skrypt przywraca przypięte TorchCodec i pyannote. Jeśli dekodowanie nadal nie działa, pobiera zweryfikowane źródła FFmpeg 7.1.5 i buduje prywatne współdzielone biblioteki audio. Zachowuje systemowy FFmpeg. Prywatna kompilacja obsługuje wewnętrzne PCM, a nie zastępuje ogólnego dekodera wideo systemu. Potrzebne są internet i narzędzia kompilacji; przy brakach skrypt wypisuje konkretne polecenie ich instalacji. Nieudana kompilacja zachowuje własny log.

`--native-only` używaj tylko, gdy celowo zachowujesz poprawne środowisko Python zgodne z blokadą. Nie twórz dowiązań udających starsze ABI dla FFmpeg 8. Nie naprawiaj tego losową aktualizacją Torch, CUDA lub TorchCodec. Modele, canonical JSON, rewizje i eksporty pozostają nienaruszone.

Dla nowej instalacji WSL skorzystaj z [Instalacji i aktualizacji](installation.md). Windows ma osobną [procedurę naprawy](windows-native.md). Naprawiaj po właściwym nieudanym sprawdzeniu, nie po każdej zwykłej aktualizacji kodu.
