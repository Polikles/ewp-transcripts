# Opcjonalna korekta

Używaj poniższych kroków razem z odpowiadającym im etapem GUI.

1. Wybierz nagranie: Otwórz zakończone nagranie z kolejki. Pola wyboru służą osobno do operacji zbiorczych.
2. Wybierz dostawcę i słownik: Aby uzyskać pomoc, wybierz dostawcę, model i opcjonalny słownik. Sprawdź gotowość i warunki przekazania danych.
3. Wygeneruj wstępną korektę: Wyraź zgodę dla tego zakresu i wygeneruj wstępną korektę. Wymaga ona ręcznego sprawdzenia.
4. Przejdź do weryfikacji źródła: Otwórz propozycję w ręcznej weryfikacji lub pomiń korektę LLM, aby sprawdzić oryginalną transkrypcję.

## 1. Wybierz nagranie

Wybierz nagranie z ukończonym ASR. Pola wyboru służą do zbiorczych operacji na osobnych nagraniach; kliknięcie nagrania otwiera jego własny edytor. Pomoc LLM jest opcjonalna. Pomiń korektę LLM kieruje surowe ASR do ręcznego sprawdzenia. Bezpośrednie rozpoczęcie ręcznej weryfikacji również zapisuje pominięcie pomocy, aby następny krok nie pozostał na korekcie.

## 2. Wybierz dostawcę i słownik

Wybierz OpenRouter ze wspólnym kluczem albo osobno uruchomiony serwer LM Studio z dokładnym adresem i modelem. Instalator programu nie instaluje LM Studio ani jego modeli. Zgodna odpowiedź nie dowodzi dobrej jakości modelu. Dotychczas sprawdzone modele lokalne nadal wymagają dokładnej weryfikacji.

Przed generowaniem sprawdź gotowość. Test nie wysyła transkrypcji. Zdalny punkt końcowy wymaga osobnej świadomej decyzji o przekazaniu danych. Opcjonalny słownik korekty wybierz według konkretnej wersji; jego ustawienia rozwijaj w razie potrzeby. Słownik korekty dotyczy terminów języka źródłowego, a nie kierunku tłumaczenia.

## 3. Wygeneruj wstępną korektę

Przeczytaj i zaznacz zgodę dotyczącą obecnego źródła i dostawcy. Wygeneruj wstępną korektę wysyła tekst transkrypcji i zatwierdzony kontekst słownika. Wywołania OpenRouter mogą być płatne; w tym etapie dostawca otrzymuje tekst, a nie audio. Wspólnym kluczem ASR i LLM zarządzasz w [Ustawieniach](settings.md).

Wstępna korekta nie jest wynikiem końcowym. Sprawdź nazwy, cytaty, interpunkcję, powtórzenia i samopoprawki. Pomoc nie powinna zmieniać znaczenia wypowiedzi ani zamieniać mowy w wygładzoną prozę. Błąd generowania nie oznacza zgody na inną ani automatyczną płatną próbę. Szczegóły techniczne zachowują jednoznaczne kody błędów.

## 4. Przejdź do weryfikacji źródła

Otwórz propozycję w [Weryfikacji i eksporcie źródła](source-review.md) albo pomiń pomoc i sprawdź ASR. Nadal trzeba ręcznie przeczytać tekst, sprawdzić szkic, potwierdzić weryfikację i wykonać eksport. Canonical JSON z ASR nie zmienia się. Zapisz stan pracy, jeśli chcesz wrócić później.
