# Weryfikacja i eksport źródła

Używaj poniższych kroków razem z odpowiadającym im etapem GUI.

1. Wybierz nagranie: Wybierz zakończone nagranie z kolejki, aby przygotować lub ponownie otworzyć jego szkic.
2. Imiona i kolory mówców: Sprawdź nazwy, przypisania mówców i profil kolorów YTT. "Dodaj mówcę" tworzy kolejnego mówcę do edycji.
3. Sprawdź transkrypcję: Popraw tekst i przypisania mówców. Dla podziału ustaw kursor między całymi słowami; dla zaznaczenia użyj wydzielania zaznaczonego tekstu.
4. Sprawdź i zapisz rewizję: Kliknij Zatwierdź, aby zapisać i sprawdzić szkic. Potwierdź ręczne sprawdzenie, a następnie Zapisz i przygotuj do eksportu.
5. Eksportuj napisy: Wybierz formaty i wyeksportuj zatwierdzoną rewizję. Opcjonalne tłumaczenie może nastąpić później.

## 1. Wybierz nagranie

Otwórz weryfikację i eksport wybranego nagrania z jego kolejki. Program przygotuje nowy szkic albo przywróci zapisany szkic tego nagrania. Można też zaimportować gotowy canonical JSON zamiast ponownie transkrybować. Wynik źródłowy i katalog pracy określają tożsamość weryfikacji; nie łącz ścieżek niezwiązanych wyników i rewizji. Ręczne ścieżki pozostają opcją zaawansowaną.

## 2. Imiona i kolory mówców

Ustaw wyświetlane imiona i sprawdź przypisanie mówcy w każdym bloku. Dodaj mówcę tworzy edytowalną tożsamość w tej rewizji; nie rozpoznaje automatycznie głosu i nie uruchamia ASR. Przed usunięciem używanego mówcy przypisz jego bloki do innych osób.

Wybierz profil kolorów YTT. Example default jest początkowym wyborem, a EwP Brand® to profil identyfikacji podkastu właściciela. Podgląd pokazuje kolory profilu, Zastosuj używa ich dla nagrania, a Zapisz zachowuje własny profil do ponownego użycia. Indywidualne nadpisania kolorów mówców pozostają zachowane. Kolory dotyczą przyszłych eksportów YTT; wcześniej zapisane pliki się nie zmieniają. SRT nie zawiera palety YTT.

## 3. Sprawdź transkrypcję i odsłuchaj

Popraw we wszystkich sekcjach treść, interpunkcję, nazwy, cytaty i przypisania mówców. Informacja o pliku pod polem mówcy pochodzi z danych źródłowych słów; zmiana nazwy mówcy jej nie zmienia. Długie bloki i sekcje są dzielone w pobliżu końców zdań dla wygody korekty. Ten podział nie wyznacza granic napisów. Jeśli brak użytecznej interpunkcji, przy pierwszej sekcji pojawia się ostrzeżenie; poświęć wtedy szczególną uwagę podziałom i mówcom.

Odtwarzacz nagrania jest w lewej kolumnie. Zsynchronizowane ścieżki i kanały są miksowane na wspólnej osi czasu od zera, a nie odtwarzane jeden po drugim. Przejdź do tego fragmentu ustawia odtwarzanie na znanym czasie słowa. Nowy lub zmieniony tekst może używać najbliższego znanego czasu, o czym informuje odtwarzacz. Można zmieniać tempo odsłuchu. Gdy brak audio, przywróć niezmienione źródła i przeładuj nagranie; edycję gotowego wyniku można kontynuować bez odsłuchu. Zmiana etapu wstrzymuje odtwarzanie.

Umieść kursor między pełnymi słowami i użyj podziału w miejscu kursora albo zaznacz tekst i wydziel go jako osobny blok. Połącz z poprzednim blokiem łączy je ponownie. Przypisz powstałe bloki właściwym osobom. Pola tekstowe dopasowują wysokość. Cofnij i Ponów dotyczą historii bieżącego szkicu, a nie opublikowanych rewizji. Zmiany struktury zapisują zmieniony tekst; Zapisz szkic pozostaje osobnym punktem zapisu.

## 4. Sprawdź i zapisz rewizję

Zatwierdź zapisuje i sprawdza bieżący szkic. Przeczytaj błędy i ostrzeżenia. To jeszcze nie zapisuje końcowej rewizji. Po sprawdzeniu całego tekstu zaznacz ręczną weryfikację i wybierz Zapisz i przygotuj do eksportu. Powstanie niezmienna zweryfikowana rewizja i zostanie włączony jej eksport. Brak potwierdzenia podświetla checkbox; zaznacz go dopiero po rzeczywistym sprawdzeniu treści, mówców i granic zdań.

Zapisz szkic zachowuje także niedokończoną pracę. Przywróć zapisany szkic wczytuje poprzednio zapisany szkic. Wyczyść bieżący szkic czyści widok po potwierdzeniu, nie usuwając opublikowanych plików. Zmiana szkicu po sprawdzeniu wymaga ponownego Zatwierdź. Zmiany zweryfikowanego wyniku zapisz jako kolejną rewizję; nie edytuj canonical JSON ani niezmiennych rewizji w miejscu.

## 5. Eksportuj napisy

Wybierz formaty i wykonaj eksport zweryfikowanej rewizji. Domyślny katalog to `exports` pod katalogiem projektu weryfikacji; ścieżki niestandardowe są w opcjach zaawansowanych. Linki pobierania zapisanych eksportów zwracają rzeczywiste pliki. Odświeżanie sprawdza wcześniejsze eksporty w katalogu i nie generuje ich ponownie. Eksport z nową paletą tworzy nowy plik, zachowując wcześniejsze wersje. [Pliki i eksporty](outputs.md) wyjaśniają formaty i różnicę względem surowego ASR.

Przejdź do następnego nagrania albo [Opcjonalnego tłumaczenia](optional-translation.md). Tłumaczenie nie jest wymagane do ukończenia weryfikacji i eksportu źródła. Przed zakończeniem sesji zapisz pracę; eksporty i niezmienne rewizje pozostają na dysku po zamknięciu przeglądarki i serwera.
