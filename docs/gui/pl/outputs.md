# Pliki i eksporty

## Surowe pliki ASR

1. `episode_results.json` to canonical JSON, czyli główne wersjonowane źródło danych: hashe źródeł, modele, słowa z czasami, mówcy i pochodzenie. Zachowaj go bez zmian.
2. `episode_segments.json` to pochodny eksport segmentów do dalszego przetwarzania, domyślnie włączony.
3. `episode_transcript.txt` to czytelny surowy tekst, domyślnie włączony. Ani on, ani segmenty nie oznaczają ręcznego zatwierdzenia.

Domyślne trzy pliki pojawiają się w wybranym katalogu wyników transkrypcji. Konfiguracja może wyłączyć pochodne pliki albo dodać surowe SRT/VTT. Ponowny eksport canonical JSON nie uruchamia ASR i nie tworzy ręcznie zweryfikowanej rewizji. Ukończony wynik z pasującą sygnaturą źródeł jest pomijany, chyba że jawnie wymusisz nową wersję. Wymuszenie nie nadpisuje poprzednich wyników i nie omija sprawdzeń źródeł.

`*_results.partial.json`, `*_results.running.json` i `*_results.failed.json` opisują stan przetwarzania lub błąd, a nie gotową transkrypcję. USER_CANCELLED oznacza anulowanie. Zachowaj szczegóły awarii do diagnostyki; usunięcie tych plików nie naprawia dostawcy ani bibliotek. Jawne ponowienie zaczyna przerwane przetwarzanie od początku.

## Katalogi weryfikacji i publikacji

Przy zwykłych ścieżkach GUI weryfikacja źródła tworzy `reviews`, `revisions` i `exports` pod katalogiem projektu. Tłumaczenie ma własne ścieżki propozycji, weryfikacji, tłumaczeń i audytów. Końcowe pliki trafiają do `translation-exports`. Opcje zaawansowane mogą zmienić lokalizacje. Czytaj wyświetlaną ścieżkę, zamiast zakładać, że wszystko zapisano obok nagrania.

Edytowalny szkic jest punktem zapisu. Zatwierdź lub Zastosuj w GUI zapisuje i sprawdza go. Zapisz i przygotuj do eksportu tworzy niezmienną rewizję lub tłumaczenie po ręcznej weryfikacji. Dopiero osobna czynność eksportu generuje pliki końcowe. Istniejące publikacje pozostają niezmienne; kolejne wersje otrzymują odrębne ID i nazwy.

## Formaty

TXT zawiera czytelny tekst. SRT i VTT to napisy z czasami; wybierz format wymagany przez miejsce publikacji. YTT to YouTube srv3 z kolorami mówców z wybranej palety. HTML udostępnia dostępny zsynchronizowany eksport transkrypcji; prezentacja na platformie i opcjonalne podłączenie mediów są osobne od rozpoznania. Wybieraj formaty oferowane dla obecnego źródła, rewizji lub tłumaczenia. Nie każdy format ma zastosowanie do każdego polecenia.

Podział sekcji i bloków edytora służy ręcznej korekcie. Generator napisów korzysta z czasów słów i reguł układu, a nie z zasady jeden blok edytora = jeden napis. Eksport nie wymyśli czasów dla odpowiedzi chmurowej bez znaczników słów. Przed publikacją sprawdź rzeczywiste wyświetlanie, zwłaszcza palety, na docelowej platformie.

## Pobieranie, odświeżanie i kopia zapasowa

Pobieranie zapisanych eksportów zwraca dokładny zapisany plik ze sprawdzeniem tożsamości i hashy. Eksporty pozostają też w wybranym katalogu docelowym. Odświeżanie sprawdza, czy już istnieją. Nie generuje ich ponownie i nie wywołuje ASR ani LLM. Tłumaczenia znajdują się w `translation-exports`. Eksport zmienionej palety tworzy nowy YTT i nie zmienia wcześniej pobranego pliku.

W kopii zapasowej zachowaj canonical JSON, zweryfikowane rewizje i tłumaczenia, audyty, słowniki oraz eksporty, razem z ukrytymi trwałymi źródłami i manifestem pracy zapisanym osobno. Sam profil lub obszar pracy nie jest pełną kopią projektu.
