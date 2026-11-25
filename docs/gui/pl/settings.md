# Ustawienia i informacje

Używaj poniższych kroków razem z odpowiadającym im etapem GUI.

1. Preferencje i profil: Pozostaw ETA wyłączone lub włącz je po kalibracji. Zapisz, wczytaj lub przenieś jeden plik JSON profilu z preferencjami, obszarami pracy i słownikami.
2. Przetestuj lokalne zależności: Uruchom opcjonalny test środowiska, aby włączyć doctor i naprawę zależności.
3. Przeczytaj raport doctor: Uruchom doctor i sprawdź błędy oraz szczegóły techniczne. Brak HF_TOKEN nie przeszkadza przy kompletnych modelach offline.
4. Napraw w razie potrzeby: Ponowna instalacja zależności pokazuje kroki w terminalu. Zapisz pracę i zatrzymaj GUI przed zmianą środowiska.
5. Sprawdź informacje o programie: Sprawdź wersję, przetwarzanie lokalne, opcjonalnych dostawców, licencje i informacje o zasobach.

## 1. Preferencje i profil

Motyw i język interfejsu wybiera się niezależnie od języka nagrania i tłumaczenia. Przy pierwszym uruchomieniu interfejs odczytuje język użytkownika Windows (polski lub angielski; poza Windows — język przeglądarki). Ręcznie zapisany wybór ma pierwszeństwo. Procent i czas, który upłynął, są zwykłymi wskaźnikami kolejki. ETA jest domyślnie wyłączone. Staje się dostępne po trzech udanych porównywalnych lokalnych transkrypcjach na tym komputerze: zgodny język, modele, układ ścieżek i mówców oraz etapy. Szacuje przetwarzanie, nie ręczną korektę, i nie musi być dokładne. Kalibracja czasu nie jest przenoszona z profilem.

Zapisz profil przechowuje lokalny snapshot, a wczytanie go przywraca. Eksport profilu pobiera jeden `ewp-user-profile.json`; import przyjmuje ten pojedynczy JSON. Zawiera preferencje, własne palety, nazwane lokalizacje i ostatnie projekty, wpisy katalogów obszarów pracy oraz domyślnie dostępne wersje słowników. Wyłącz dołączanie słowników, jeśli chcesz mniejszy plik z odwołaniami; wtedy przenieś dokładne słowniki osobno.

Profil nie zawiera mediów, transkrypcji, aktywnych zadań, kluczy, zgód ani kalibracji czasu. Nie zastępuje zapisu szkiców i obszarów ani kopii ich plików. Import scala katalogi bez usuwania istniejących zapisów i słowników oraz bez uruchamiania kolejki. Dołączone słowniki zachowują treść i hash w prywatnym magazynie według treści. Obce lub brakujące ścieżki pozostają widocznie niedostępne. Limit profilu to 16 MiB.

## Wspólny klucz OpenRouter

Zarządzanie kluczem otwiera wspólne okno ASR, korekty i tłumaczeń. Wpisany klucz można ustawić tylko na sesję. Zapisz klucz jawnie umieszcza go w magazynie systemowym. Użyj zapisanego klucza od razu aktywuje go w obecnej sesji serwera. Przycisk ustawienia tylko na sesję jest nieaktywny przy pustym polu i nie trzeba go klikać po użyciu zapisanego klucza. Sprawdź klucz API sprawdza wpisany klucz bez aktywowania albo aktywny klucz przy pustym polu. Wynik pojawia się obok przycisku. Test nie wysyła audio ani transkrypcji.

Wyczyść klucz sesji usuwa wpis z pamięci serwera. Usuń zapisany klucz usuwa wpis systemowy i czyści sesję. Klucz `OPENROUTER_API_KEY` ze środowiska może nadal działać do usunięcia go z terminala uruchamiającego serwer. Zamknij okno, × lub Escape zamyka okno i czyści niewysłany tekst, zachowując jawnie aktywowane klucze. Czyszczenie danych przeglądarki i pracy nie usuwa klucza działającego serwera. Restart usuwa klucz trzymany wyłącznie w pamięci. Sprawdzenie połączenia wczytuje klucz z magazynu systemowego, jeśli nie podano klucza i nie ma go w sesji ani środowisku. Komunikat sukcesu potwierdza wczytanie klucza i brak wysłanego audio. Nie oznacza to zgody na wysyłanie nagrań i nie uruchamia transkrypcji.

Windows korzysta z Menedżera poświadczeń. Linux i WSL wymagają dostępnej usługi Secret Service; nie ma awaryjnego zapisu jawnym tekstem. Dostęp może wymagać odblokowania magazynu. Przeglądarki połączone z jednym lokalnym serwerem współdzielą aktywny klucz; to instalacja dla jednego użytkownika. Klucze nie trafiają do przenośnych profili, JSON obszarów, transkrypcji ani pamięci przeglądarki. Zgoda na przekazanie danych jest zawsze osobna.

## 2. Przetestuj lokalne zależności

Użyj testu po instalacji lub przy problemie lokalnych bibliotek, nie jako obowiązkowego kroku każdego zadania. Sprawdza Python i system, FFmpeg i ffprobe, GPU i CUDA, ładowanie bibliotek mowy i przypięte snapshoty w ograniczonych procesach. Nie pobiera modeli i nie transkrybuje. Ukończony test włącza doctor i naprawę. Działające polecenie FFmpeg nie dowodzi, że TorchCodec wczytuje biblioteki współdzielone.

## 3. Przeczytaj raport doctor

Przeczytaj nieudane sprawdzenia i rozwiń szczegóły techniczne w razie potrzeby. Akceptowane środowiska to natywny Windows 11 i WSL z Ubuntu 24.04/26.04. Brak HF_TOKEN jest nieszkodliwy przy kompletnych modelach offline. Raport terminala uruchamia `uv run --locked transcriber doctor --test-speech-runtime`. Zwykły doctor nie ładuje modeli. Pomyślne testy potwierdzają sprawdzone zależności, a nie jakość rozpoznania czy wszystkie kombinacje modeli i GPU.

## 4. Napraw w razie potrzeby

Zapisz pracę, zatrzymaj GUI i wykonaj instrukcję terminala dla swojego systemu. [Windows](windows-native.md) korzysta z `scripts/setup-windows.ps1 -Repair`, a [naprawa po aktualizacji Ubuntu](ubuntu-upgrade.md) z `bash scripts/repair-dependencies.sh`. Naprawa przywraca przypięte biblioteki Python i audio. Nie jest ponownym pobieraniem modeli ani usuwaniem wyników. Nie uruchamiaj instalatora tylko po to, aby sprawdzić zwykłą aktualizację, która już działa.

## Tymczasowe katalogi robocze

Odśwież spis, ustaw powód zachowania i minimalny wiek, zaznacz niechronione pozycje i przygotuj podgląd usuwania. Przeczytaj liczbę i rozmiar, a następnie potwierdź w ciągu pięciu minut. Zmiana wyboru lub odwołań wymaga nowego podglądu. Aktywne zadania, znane odwołania kolejki i zapisów, nieznane pliki i starsze katalogi bez określonego właściciela są chronione. Sprawdzany jest tylko skonfigurowany katalog tymczasowy. Inne katalogi zapisów sprawdź osobno. To inna funkcja niż porządkowanie źródeł; nie usuwa opublikowanych wyników ani modeli.

## 5. Sprawdź informacje o programie

Informacje pokazują wersję programu i API, zakres przetwarzania, licencje i autorstwo grafiki. Lokalne GPU po przygotowaniu działa lokalnie; opcjonalni dostawcy mają własne zasady i opłaty. Kody błędów i JSON są pomocą diagnostyczną, nie zwykłymi krokami pracy. Przed zgłoszeniem przeczytaj [Rozwiązywanie problemów](troubleshooting.md). Nie dołączaj kluczy ani prywatnej treści transkrypcji i audio.
