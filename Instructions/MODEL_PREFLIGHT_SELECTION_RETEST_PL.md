# Retest 0.24.1 — brak modelu i aktywne nagranie

Zaktualizuj0.24.0 przez EwP-Setup-0.24.1.exe. Nie trzeba pobierać ponownie modeli ani powtarzać
zaakceptowanej transkrypcji kolejki mieszanej. Wersje i konfiguracje modeli pozostają bez zmian.

1. Jeśli masz model oznaczony jako niezainstalowany, wybierz go i kliknij Zaplanuj przetwarzanie.
   Ma pojawić się komunikat: Wybrany model nie został zainstalowany. Doinstaluj model, zrestartuj
   program i spróbuj ponownie. Planowanie ma się zatrzymać przed dodaniem zadania do kolejki.
   Nie usuwaj działającego modelu wyłącznie na potrzeby tego testu; ten scenariusz sprawdzono
   automatycznie na małych, syntetycznych plikach.
2. W tabeli kolejki nazwa ASR powinna mieć osobny wiersz i odstęp od nazwy odcinka i ustawień.
3. Otwórz istniejące wyniki kilku odcinków. W Weryfikacja i eksport źródła wybieraj kolejno różne
   nagrania. Otwarta transkrypcja ma wskazywać to samo nagranie obwódką w kolejce po lewej i na
   liście1. Wybierz nagranie. Poprzedni odcinek traci zaznaczenie. Sprawdź jasny i ciemny motyw.
   Oznaczenie ma pozostać po odświeżeniu kolejki. Nie trzeba transkrybować ponownie ani używać API.

Kontrola modeli jest lokalna i lekka: obecność/rozmiary plików, bez ładowania bibliotek ML,
hashowania dużych plików czy pobierania. Napraw → Sprawdź modele nadal służy do weryfikacji SHA.
Przy starcie kolejki model jest sprawdzany ponownie; jeśli zniknął po zapisaniu planu lub po
odtworzeniu starej kolejki, zadania pozostają oczekujące zamiast rozpoczynać przygotowanie.
