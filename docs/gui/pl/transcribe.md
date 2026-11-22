# Transkrypcja

Używaj poniższych kroków razem z odpowiadającym im etapem GUI.

1. Wybierz katalog wyników i nagrania: Najpierw wybierz wspólny katalog wyników, a potem pliki audio, wideo lub zapisane wyniki canonical JSON. Pasujące ścieżki mówców jednego odcinka wybierz razem.
2. Zaplanuj i dodaj do kolejki: Ustaw język i liczbę mówców osobno dla nagrania. Planowanie sprawdza wszystkie pliki spoza kolejki. Sprawdź cały plan, zaznacz potwierdzenie i dodaj zadania do kolejki.
3. Uruchom kolejkę: Uruchom kolejkę przetwarza przygotowane odcinki po kolei. Po zakończeniu przejdź do opcjonalnej korekty lub weryfikacji źródła.

## 1. Wybierz katalog wyników i nagrania

Najpierw wybierz jeden trwały wspólny katalog wyników. Główny przycisk wyboru plików i Dodaj pliki w lewej kolumnie przyjmują obsługiwane audio, wideo oraz canonical `*_results.json`. Zsynchronizowane ścieżki mówców jednego odcinka dodaj razem. Program wyodrębnia audio z wideo; nie zmienia oryginalnego filmu. Canonical JSON jest importowany do sprawdzenia bez ponownego ASR. JSON błędu, plik częściowy i dowolny inny JSON nie są gotowym wynikiem.

Domyślnie obsługiwane są WAV, MP3, FLAC, M4A, OGG, OPUS oraz MP4, MKV, MOV, WEBM, AVI, M4V. Faktyczne odczytanie zależy od FFmpeg i kodeka źródła. Zamiast wyboru pliku można wpisać ścieżkę widoczną dla serwera. Obsługiwane są ścieżki użytkownika Windows i WSL; katalogi systemowe, dowiązania symboliczne i cele junction są blokowane.

Nazwy `s0e01-Szymon.wav` i `s0e01-Damian.wav` tworzą jeden odcinek `s0e01` z osobnymi ścieżkami mówców. Inne nazwy odcinków pozostają osobno. Ścieżki mają wspólny początek czasu: nie są sklejane jedna za drugą ani automatycznie synchronizowane. Muszą mieć jednakową częstotliwość próbkowania. Różnica długości powyżej 100 ms daje ostrzeżenie, a powyżej 500 ms blokuje przetwarzanie bez jawnego obsługiwanego wyjątku. Przy wielu strumieniach audio w jednym pliku przeczytaj ostrzeżenie i wybierz właściwy układ przed planowaniem.

Język i liczba mówców dotyczą konkretnego nagrania, a nie całej kolejki. Wybierz PL, EN lub automatyczne rozpoznanie języka oraz automatyczne wykrywanie lub znaną liczbę mówców. Gdy brak metadanych, wybrane wartości są opisane gwiazdkami `*`/`**`; to ustawienia użytkownika, nie wykryte fakty. Wybranie EN dla polskiej mowy czasem dawało sensowny tekst angielski, ale poprawność nie jest gwarantowana. Do sprawdzonego tłumaczenia użyj osobnego etapu tłumaczenia.

## 2. Zaplanuj i dodaj do kolejki

Zaplanuj przetwarzanie sprawdza i planuje wszystkie wybrane nagrania, które nie są już w kolejce. Nie ma osobnego przycisku sprawdzania pliku w GUI. Dla każdego wiersza przejrzyj grupowanie źródeł, język, liczbę mówców, działanie i ostrzeżenia. Usuń błędy, potwierdź konkretny plan i jednym kliknięciem Dodaj do kolejki dodaj całą partię. Zmiana źródła, katalogu lub opcji wymaga ponownego planowania i potwierdzenia. Samo planowanie nie uruchamia ASR. Usuń z listy usuwa tylko pozycję z wyboru wejściowego.

Domyślnym dostawcą jest lokalne GPU. ASR w chmurze jest opcjonalne; rozwiń ustawienia silnika, wybierz OpenRouter i model. Kolejka może łączyć zadania lokalne i chmurowe. Wszystkie aktywne zadania przygotowane lub przetwarzane muszą korzystać z jednego katalogu wyników. Przed zmianą katalogu zakończ lub usuń aktywne wiersze. Sama historia zakończonych zadań nie blokuje poprzedniego katalogu.

## Modele chmurowe i koszty

Dostępne ustawienia modeli to `openai/whisper-large-v3`, `openai/whisper-large-v3-turbo`, `elevenlabs/scribe-v2` i `microsoft/mai-transcribe-2`. Dostępność i ceny mogą się zmieniać. Odśwież i oszacuj koszt sprawdza bieżące dane dostawcy i długość wybranych źródeł. Sprawdzanie klucza i odświeżanie cen nie wysyłają audio i nie naliczają kosztu transkrypcji. Ostateczny rachunek może się różnić. Wewnętrzne zabezpieczenie nie stanowi limitu rozliczeń dostawcy.

Whisper wymaga jednego mówcy na ścieżce; zmiksowane audio wielu mówców lepiej obsługują Scribe i MAI. Punkt końcowy musi zwracać czasy słów, nie tylko tekst. Długie nagrania są automatycznie dzielone na żądania poniżej 24 MB, z uwzględnieniem narzutu kodowania. Nakładający się kontekst jest łączony na oryginalnej osi czasu. Niepewna ciągłość oznaczeń mówców wymaga sprawdzenia. Program nie wymyśla czasów słów i nie wykonuje po błędzie ukrytej kolejnej płatnej próby.

Użyj [wspólnego klucza OpenRouter](settings.md). Zgoda na wysłanie audio dotyczy obecnie przygotowanych zadań i nie jest zapisywana. Wczytanie pracy, ponowienie albo zmiana zadań wymaga nowej zgody. Program sprawdza zgodę i aktywny klucz przed uruchomieniem jakiegokolwiek zadania w kolejce mieszanej. Wczytanie zapisu pracy nie daje zgody na wysłanie.

## 3. Uruchom kolejkę i przejdź dalej

Uruchom kolejkę przetwarza przygotowane zadania po kolei, pomijając ukończone ASR. Procent i etapy są orientacyjnymi wskaźnikami aktywności; czas, który upłynął, jest widoczny bez ETA. Obracająca się zębatka oznacza pracę w toku. Po zakończeniu ASR przejdź do korekty lub weryfikacji źródła. Nie oznacza to jeszcze zakończenia całego procesu pracy.

Anuluj zadanie od razu anuluje oczekujące przetwarzanie, a dla rozpoczętego czeka na bezpieczny punkt. Poczekaj na stan końcowy. Ponów zastępuje wybrany nieudany lub anulowany wiersz nowym zadaniem przygotowanym do startu. Przetwarzanie zacznie się od początku po jawnym uruchomieniu kolejki; ukończone zadania nie ruszą ponownie. Usuń ukończone zadania z kolejki zachowuje pozostałe. Usunięcie wiersza nie kasuje opublikowanych plików.

Udane ASR domyślnie zapisuje `*_results.json`, `*_segments.json` i `*_transcript.txt`. To surowe wyniki, a nie ręcznie zatwierdzone napisy. Zobacz [Pliki i eksporty](outputs.md). Przejdź do [Opcjonalnej korekty](optional-correction.md) albo od razu do [Weryfikacji i eksportu źródła](source-review.md). Przed zatrzymaniem zapisz stan; wznowienie opisuje [Zapisana praca](saved-work.md).
