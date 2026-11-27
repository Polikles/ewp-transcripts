# Obsługa z terminala

1. Wykonuj polecenia z repozytorium transkrybera. Ścieżki ze spacjami obejmuj cudzysłowami.
2. Użyj `uv run --locked transcriber --help`, a potem `--help` wybranego polecenia przed użyciem opcji.
3. Zachowuj canonical JSON bez zmian. Podgląd CLI i przycisk GUI o zatwierdzonej nazwie mogą mieć różne znaczenie zapisu końcowego; czytaj pomoc konkretnego polecenia.

## Zwykłe polecenia

```text
uv run --locked transcriber --version
uv run --locked transcriber gui --help
uv run --locked transcriber doctor --help
uv run --locked transcriber inspect --help
uv run --locked transcriber dry-run --help
uv run --locked transcriber transcribe --help
uv run --locked transcriber export --help
uv run --locked transcriber clean --help
```

`gui` uruchamia lokalny interfejs. `doctor` sprawdza środowisko; opcja `--test-speech-runtime` dodatkowo testuje biblioteki mowy. `inspect` pozostaje osobną diagnostyką CLI, mimo że GUI łączy sprawdzanie z planowaniem. `dry-run` przygotowuje plan bez zapisywania wyników i katalogów roboczych oraz bez ładowania modeli. `transcribe` uruchamia lokalną transkrypcję; do ASR w chmurze i jawnej zgody kolejki użyj GUI. `export` odtwarza surowe eksporty z canonical JSON bez audio i ASR. `clean` przygotowuje podgląd katalogów tymczasowych ze znacznikami programu. Nie zastępuje czyszczenia źródeł w GUI ani deinstalatora.

## Konfiguracja

Kolejność nadpisywania ustawień to: wbudowane domyślne → preset → konfiguracja użytkownika → opcjonalny `transcriber.toml` bieżącego katalogu → jawny plik `--config` → opcje polecenia. Nie każde polecenie ma wszystkie opcje; sprawdź jego pomoc. Domyślny plik użytkownika to `~/.config/ewp-transcripts/config.toml`. Wbudowane ustawienia są w `src/ewp_transcripts/resources/default-config.toml`. W głównym katalogu nie musi istnieć śledzony `transcriber.toml`. Utwórz go tylko dla świadomych zmian i bez kluczy. Indywidualne opcje nagrań GUI są zapisywane osobno w planach i obszarach.

W Windows używaj natywnych ścieżek użytkownika. W WSL ścieżka musi być widoczna dla serwera; obsługiwane są też ścieżki dysków Windows. Obejmuj całą ścieżkę cudzysłowami. Grupowanie wielu plików, kontrola długości i próbkowania, niezmienne wersje oraz lokalne modele offline obowiązują również w CLI.

## Weryfikacja, tłumaczenia i słowniki

```text
uv run --locked transcriber revise --help
uv run --locked transcriber translate --help
uv run --locked transcriber dictionary --help
uv run --locked transcriber benchmark --help
```

`revise` przygotowuje edytowalny przegląd źródła, sprawdza go i zapisuje niezmienne rewizje. Podpolecenie `correct` uruchamia pomoc dostawcy i może kosztować również przy podglądzie. `translate` przygotowuje ręczne tłumaczenie, sprawdza, zapisuje, audytuje i eksportuje; `automate` tworzy propozycję do sprawdzenia. `dictionary` proponuje mapowania z dokładnych par wyniku i rewizji oraz publikuje zatwierdzone decyzje. `benchmark` jest zaawansowaną funkcją prywatnej oceny i nie jest wymagany w normalnej pracy nad podkastem.

Dla zewnętrznego edytora zachowaj pola techniczne i zmieniaj wyłącznie dozwoloną treść. Najpierw przygotuj dokument, popraw tekst, sprawdź go poleceniem preview, a dopiero potem użyj apply i eksportu. W razie niezgodności źródła przywróć właściwy plik zamiast zmieniać hashe. Dokładne opcje podaje `--help` wybranego podpolecenia.

Komplet zaawansowanych przykładów flag pozostaje w angielskim [runbooku CLI](https://github.com/Polikles/ewp-transcripts/blob/main/Instructions/README.md). Ten rozdział opisuje zwykłą obsługę terminala po polsku. Nazwy wykonywalnych poleceń, flag, pól JSON i kody diagnostyczne pozostają oryginalne. Zapisy pracy i profile obsługuj w GUI; nie istnieją domyślane polecenia o nazwach przycisków.

## Przykład lokalnej pracy w CLI

Podstaw własne ścieżki i dokładne wygenerowane nazwy. Po revise prepare popraw wygenerowany dokument przed preview i apply. W tłumaczeniu między prepare a preview uzupełnij każdą linię docelową. Nie zmieniaj technicznych nagłówków ani linii źródłowych. Te polecenia po uruchomieniu wykonują rzeczywistą transkrypcję i zapis końcowy; wcześniej przeczytaj ich pomoc.

```text
uv run --locked transcriber dry-run "recordings" --output-dir "output"
uv run --locked transcriber transcribe "recordings" --language pl --output-dir "output" --non-interactive
uv run --locked transcriber export "output/episode_results.json" --format srt --format vtt --output-dir "raw-exports"
uv run --locked transcriber revise prepare "output/episode_results.json" --output-dir "reviews"
uv run --locked transcriber revise preview "reviews" --results-dir "output"
uv run --locked transcriber revise apply "reviews" --results-dir "output" --output-dir "revisions" --audit
uv run --locked transcriber export "output/episode_results.json" --revision "revisions/episode_revision_001.json" --format srt --output-dir "exports"
uv run --locked transcriber translate prepare "output/episode_results.json" --revision "revisions/episode_revision_001.json" --target-language en --output-dir "translation-reviews"
uv run --locked transcriber translate preview "translation-reviews" --results "output" --revisions-dir "revisions"
uv run --locked transcriber translate apply "translation-reviews" --results "output" --revisions-dir "revisions" --output-dir "translations"
uv run --locked transcriber translate export "translations" --format srt --format vtt --output-dir "translation-exports"
```

Pomoc dostawcy uruchamia `revise correct` lub `translate automate`. Przed płatnym wywołaniem przeczytaj ich `--help`, warunki przekazania danych i jawne opcje chmurowe. GUI prowadzi przez wspólny klucz i zgody zadań. Powyższy przykład lokalny nie wymaga klucza API.
