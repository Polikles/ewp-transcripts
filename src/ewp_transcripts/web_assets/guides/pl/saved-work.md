# Zapisana praca i porządkowanie

Używaj poniższych kroków razem z odpowiadającym im etapem GUI.

1. Wybierz katalog wyników i zapisu: Pozostaw opcjonalny katalog pusty, aby zapisywać nowe pliki stanu pracy w katalogu wyników, lub wybierz osobny katalog zapisów i kopii zapasowych.
2. Zapisz bieżący stan pracy: Zapisz bieżący stan pracy przed zatrzymaniem programu. Domyślna nazwa zadania zawiera datę i czas; własna nazwa jest opcjonalna. Zmienione szkice są najpierw zapisywane.
3. Wczytaj zapisaną pracę: Lista odświeża się przy otwarciu tej sekcji. Ostatni stan wczytuje się automatycznie; w razie potrzeby wybierz inny zapis i wczytaj go. Wprowadź lub jawnie wczytaj klucz dostawcy; zgoda na wysłanie pozostaje niezaznaczona.
4. Sprawdź porządkowanie przed usunięciem: Odśwież spis zarządzanych źródeł i przeczytaj przyczyny zachowania plików przed jawnym porządkowaniem.

## 1. Wybierz katalog wyników i zapisu

Wybierz katalog wyników przed pracą. Puste pole opcjonalnego katalogu zapisów umieszcza NOWE pliki stanu pracy w katalogu wyników. Możesz wybrać inny katalog zapisów i kopii zapasowych. Aktualizacja wybranego starszego zapisu zachowuje jego faktyczny katalog. Wiersz pliku zapisu pokazuje rzeczywistą ścieżkę manifestu. Serwer lokalnie pamięta dostępne ostatnie lokalizacje wyników i zapisów. Lista odświeża się przy otwarciu sekcji. Zapamiętanie katalogów nie uruchamia pracy i nie przywraca zgód.

Instalacja zarządzana domyślnie wypełnia katalog wyników folderem `outputs` obok programu. Przy chronionej instalacji używa zapisywalnego folderu użytkownika. Możesz pozostawić tę ścieżkę albo wskazać inną; poprzedni własny wybór ma pierwszeństwo. Dodanie plików uruchamia zapis od razu po wyborze, a inne zmiany zapisują się po krótkiej pauzie. Dodatkowa kontrola działa co15 sekund.

## 2. Zapisz bieżący stan pracy

Pozostaw proponowaną nazwę `zadanie + data i czas` albo wprowadź własną, unikalną nazwę i zapisz bieżący stan. Zmienione szkice źródła i tłumaczenia są najpierw zapisywane. Nowe nazwy plików zaczynają się nazwą i kończą `--<UUID>.workspace.json`. Znaki niedozwolone w nazwach Windows są zastępowane; polskie litery mogą pozostać. Nie trzeba rozpoznawać zapisu po samym UUID.

Własna nazwa wczytanego obszaru wypełnia się automatycznie i jest chroniona przed przypadkową zmianą. Nazwa domyślna jest wyszarzona i można ją zastąpić. Aktualizacja zapisuje ten sam obszar. Zapisz jako nowy obszar wymaga innej nazwy i zachowuje oryginał. Powtórzona nazwa w znanych katalogach jest odrzucana. Wielkość liter, spacje na brzegach i równoważne zapisy Unicode nie tworzą odrębnych nazw. Puste pole używa nazwy domyślnej; zajęta własna nazwa podświetla pole.

Autozapis jest aktywny od uruchomienia i zapisuje zmiany oraz szkice edycji w ciągu kilku sekund.
Ostatni aktywny stan pracy wczytuje się automatycznie, także w nowej sesji przeglądarki.
Przed wyborem katalogu wyników instalacja zarządzana zapisuje stan w `work-state` obok programu.
Przy instalacji w chronionym folderze, np. Program Files, używa prywatnego katalogu użytkownika.
Wybór katalogu wyników wiąże z nim początkowy zapis odzyskiwania. Wiersz pliku zapisu pokazuje
rzeczywistą ścieżkę. Nazwane zapisy nadal służą do świadomego tworzenia punktów powrotu.
Przed zatrzymaniem serwera poczekaj na zakończenie zapisu. Brakujące ścieżki nie powodują
zastąpienia ostatniego zapisu pustym stanem.

Wyniki kolejki są zapisywane również po zamknięciu przeglądarki. Niedokończone zadania wracają
do stanu oczekującego i wymagają jawnego uruchomienia. Zamknięcie karty nadal pozostawia serwer
włączony; po zakończeniu pracy zatrzymaj go przez Ctrl+C. Natywny interfejs Windows jest
zaplanowany po odbiorze instalatora.

## 3. Wczytaj zapisaną pracę

Wybierz obszar z listy i wczytaj stan albo otwórz jego plik manifestu. Okno postępu pokazuje liczbę wczytanych i wszystkich zadań podczas sprawdzania ścieżek, źródeł i edytorów. Poczekaj do końca. Przywracane są zadania ukończone, nieudane i anulowane oraz oczekujące z indywidualnymi opcjami. Przerwane przetwarzanie nigdy nie wznawia się samo. Ponowienie jest jawne i rozpoczyna pracę od początku.

Nowe zapisy przechowują również pliki wybrane przed planowaniem, w tym wiele ścieżek mówców jednego odcinka. Wczytanie przywraca pliki i ustawienia bez planowania. Kliknij jawnie Zaplanuj przetwarzanie, a potem sprawdź i potwierdź plan przed dodaniem. Ponowny wybór pliku o tej samej nazwie i treści nie tworzy duplikatu. Inna treść może wymagać odrębnego ID. Starsze zapisy bez trwałych danych wyboru mogą wymagać ponownego wskazania oryginałów.

Klucze i zgody na wysłanie lub ręczną weryfikację nie są zapisywane. Wprowadź albo jawnie wczytaj klucz OpenRouter, jeśli serwer już go nie ma, i zaznacz nową zgodę dla chmury. Klucz nadal obecny w tej samej sesji serwera jest niezależny od wczytania pracy. Brakujące ścieżki trzeba odtworzyć; sam manifest nie zawiera wszystkich plików.

## Kopia zapasowa i przenoszenie projektu

Kopiuj cały katalog wyników RAZEM z ukrytymi katalogami, np. `.ewp-gui-sources`, oraz osobno ustawione katalogi weryfikacji, rewizji, tłumaczeń, słowników i zapisów pracy. Zachowaj także nagrania, jeśli pozostają poza nimi. Nowe trwałe kopie wybranych mediów znajdują się pod katalogiem wyników; same tymczasowe kopie wyboru przeglądarki nie są kopią zapasową.

JSON obszaru zawiera odwołania, hashe, opcje i tożsamość etapów, a nie bajty nagrań, klucze ani zgody. Gotowy wynik można edytować i eksportować bez audio, ale odsłuch wymaga niezmienionych mediów. Przeniesienie na inny komputer wymaga skopiowania plików i sprawdzenia ścieżek. [Profil użytkownika](settings.md) przenosi preferencje, wpisy katalogów i opcjonalne słowniki, a nie nagrania i transkrypcje. Nie zmieniaj hashy, aby obejść zmienione źródło.

## 4. Sprawdź porządkowanie przed usunięciem

Usunięcie wybranego zapisu kasuje wyłącznie jego manifest. Wyczyść bieżący stan pracy zapomina nieaktywny stan interfejsu i pamięci po potwierdzeniu. Nie działa w czasie aktywnego przetwarzania. Żadna z tych czynności nie usuwa opublikowanych rewizji, eksportów ani wszystkich mediów.

Spis zarządzanych kopii źródeł pokazuje trwałe kopie programu i powód ich zachowania. Przygotuj podgląd usuwania tylko nieużywanych kopii, sprawdź plan i jawnie potwierdź. Bieżąca praca, znane katalogi zapisów i odwołania etapów chronią pliki. Inne katalogi poza znanymi tej operacji trzeba sprawdzić osobno. To osobna funkcja od czyszczenia tymczasowych katalogów w Ustawieniach. Nie kasuje zewnętrznych oryginałów ani modeli.

## Projekty i lokalizacje

Ostatnie projekty otwierają odwołania wyniku i katalogu. Nazwane lokalizacje wypełniają pola wejścia i wyjścia bez uruchamiania ASR. Zmiana wejścia zastępuje oczekujący wybór, nie zadania w kolejce. Wyszukiwanie zapisanych wyników sprawdza canonical JSON we wskazanym katalogu i pozwala dodać je bez ASR. Skan obejmuje do 500 wpisów, a pojedynczy import do 50 wyników. Niedostępna ścieżka wymaga odtworzenia pliku, a nie automatycznego generowania go od nowa.
