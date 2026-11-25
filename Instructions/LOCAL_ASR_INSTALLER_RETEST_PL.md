# Retest 0.24.0 — instalator i lokalne modele ASR

## Przygotowanie

Użyj EwP-Setup-0.24.0.exe z bieżącej paczki. Jeśli masz0.23.x, najpierw wybierz Aktualizuj.
Doinstaluj modele lokalne wymaga identycznej wersji instalatora i programu. Nie trzeba ponownie
pobierać podstawowych modeli. Zachowaj zapis pracy przed testem; wyniki warto zapisywać do osobnego
katalogu. Nie włączaj chmury ani płatnych testów, aby sprawdzić lokalne modele.

## Instalator

1. Nagłówek ma ciemny motyw graficzny znany z programu. Komunikaty HF/uv (np. Xet) widoczne są
   wyłącznie po rozwinięciu Szczegóły techniczne/dziennik; opis bieżącego elementu pokazuje nazwę
   pakietu lub repozytorium. Etapy, licznik pobrań i postęp bieżącego pliku pozostają osobne.
2. Przy nowej instalacji Whisper Large v3 i Large v3 Turbo są opcjonalne i niezaznaczone.
3. Po aktualizacji wybierz Doinstaluj modele lokalne. Zaznacz tylko Whisper Large v3 Turbo
   (dropbox-dash/faster-whisper-large-v3-turbo, około1,6 GB). Potrzebne miejsce powinno odpowiadać
   wyborowi. HF nie powinien być wymagany, jeśli nie zaznaczysz brakującego/ponownie pobieranego
   modelu pyannote. OR nie jest wymagany. Po pobraniu diagnostyka uruchamia się automatycznie.
4. Otwórz ponownie Doinstaluj modele lokalne. Zainstalowane modele powinny być rozpoznane,
   wyszarzone i niezaznaczone. Zainstaluj ponownie wybrane modele odblokowuje ich zaznaczenie;
   samo włączenie tej opcji nie powinno wybierać modeli. Nie musisz ponownie ich pobierać w teście.
5. Analogicznie doinstaluj Whisper Large v3 (Systran/faster-whisper-large-v3, około3,1 GB).
   Opcja Sprawdź modele w Napraw weryfikuje SHA/wersje; brak niezainstalowanego modelu opcjonalnego
   nie powinien wymuszać jego pobrania. Pełna weryfikacja SHA dużych plików może potrwać.

## Program

1. Na świeżym profilu przeglądarki język domyślny odpowiada językowi interfejsu użytkownika
   Windows: polski albo angielski. Wybór w instalatorze nie nadpisuje języka systemu. Ręcznie
   zapisany wybór w programie ma pierwszeństwo; istniejące angielskie ustawienie zostanie zachowane.
2. Jeśli zapisałeś klucz OR w instalatorze, wybierz chmurę i Sprawdź klucz i połączenie.
   Po poprawnym sprawdzeniu powinno pojawić się: Klucz i połączenie z OR działają. Wczytano zapisany
   klucz. Nie wysłano audio. Sprawdzenie nie uruchamia transkrypcji ani nie zaznacza zgody na wysyłanie.
   W sesji z już aktywnym kluczem komunikat nie informuje o ponownym wczytaniu.
3. Wybierz lokalnego dostawcę, a potem Large v3 Turbo. Dodaj krótkie znane nagranie PL, zaplanuj
   i dodaj do kolejki. Przed uruchomieniem kolejka powinna pokazywać ASR · large-v3-turbo.
4. Dodaj drugie nagranie z wybranym Large v3. Pierwsze zadanie musi zachować Turbo, drugie v3.
   Zamknij/otwórz przeglądarkę albo uruchom ponownie program: zapis pracy ma odtworzyć wybory,
   a zadania mają pozostać oczekujące, bez samoczynnej transkrypcji.
5. Uruchom lokalną kolejkę. Sprawdź, czy oba modele kończą transkrypcję i eksport, a zapisane
   *_results.json w processing.models/role=asr wskazują właściwą nazwę i przypiętą wersję modelu.
   Oceniaj działanie i znaną treść; te modele nie gwarantują identycznego tekstu jak dostawca API.
6. Dodanie/zapis nie powinny wymagać ręcznego wyboru katalogu wyników; domyślny outputs oraz
   autozapis mają pozostać aktywne. Nie usuwaj work-state ani źródeł w trakcie tego testu.

## Zakres i raport

W tej wersji lokalne odpowiedniki obejmują Whisper v3 i v3 Turbo. Nie ustalono publicznych wag
Scribe v2 i MAI do zwykłej instalacji na PC; pozostają opcjami chmurowymi. Istniejące podstawowe
modele, ich wersje i poprzednie wyniki pozostają bez zmian. Lokalny wybór nie przełącza na API.

Po testach wystarczy raport instalatora oraz informacja: doinstalowanie Turbo/v3, rozpoznanie
zainstalowanych modeli, prawidłowe nazwy w kolejce i działanie obu lokalnych modeli. Przy błędzie
podaj model, etap i kod błędu, bez tokenów ani prywatnej transkrypcji. Automatyczne testy nie
zastępują tego testu działania modeli na Twoim GPU. Deinstalacja podczas pracy aplikacji została
już potwierdzona przez właściciela; nie musi być powtarzana w tej rundzie.
