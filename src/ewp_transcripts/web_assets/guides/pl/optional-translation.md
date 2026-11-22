# Opcjonalne tłumaczenie

Używaj poniższych kroków razem z odpowiadającym im etapem GUI.

1. Wybierz nagranie źródłowe: Wybierz nagranie i zweryfikowaną rewizję. Pomiń tłumaczenie z LLM pod kolejką, aby tłumaczyć ręcznie.
2. Wybierz kierunek tłumaczenia: Język źródła ustawia kierunek. Potwierdź zmianę kierunku i wybierz pasujące nagranie źródłowe.
3. Wygeneruj propozycję tłumaczenia: Aby użyć API, wybierz dostawcę i model, sprawdź połączenie, wyraź zgodę i wygeneruj propozycję tłumaczenia. Szczegóły źródła i słownik są rozwijane.
4. Przejdź do przeglądu tłumaczenia: Sprawdź znaczenie i mówców w przeglądzie tłumaczenia przed zastosowaniem i eksportem.

## 1. Wybierz nagranie źródłowe

Wybierz nagranie, najlepiej z ręcznie zweryfikowaną rewizją źródłową. Można jawnie tłumaczyć także niesprawdzone ASR lub wstępną korektę, ale słabszy status źródła zostanie zapisany; nie staje się ono przez to ręcznie zweryfikowane. Aby tłumaczyć ręcznie, wybierz Pomiń tłumaczenie z LLM pod kolejką, a potem otwórz weryfikację tłumaczenia.

## 2. Wybierz kierunek tłumaczenia

Język źródła ustawia PL → EN albo EN → PL. Zmiana kierunku wymaga jawnego potwierdzenia i pasującego źródła. Język interfejsu nie określa kierunku. Sprawdź tożsamość źródła przed generowaniem; szkicu tłumaczenia nie należy łączyć z niezwiązanym canonical JSON.

## 3. Wygeneruj propozycję tłumaczenia

Do pomocy wybierz OpenRouter albo osobno uruchomiony LM Studio oraz dokładny model. Sprawdź gotowość, w razie potrzeby rozwiń słownik tłumaczenia i przeczytaj warunki przekazania danych. Wspólny klucz OpenRouter działa dla ASR, korekty i tłumaczeń, ale każda operacja ma osobny zakres danych i zgody.

Po jawnej zgodzie Wygeneruj propozycję tłumaczenia wysyła tekst źródłowy, nie audio. OpenRouter może naliczyć opłatę. Słownik projektu dostarcza zatwierdzone terminy i konwencje właściwego kierunku; nie gwarantuje sensu ani płynności. Brak zgody podświetla checkbox. Udane generowanie zapisuje propozycję w kolejce i blokuje przypadkowe powtórzenie generowania w tym stanie.

## 4. Przejdź do przeglądu tłumaczenia

Otwórz propozycję w [Weryfikacji tłumaczenia i eksporcie](translation-review.md). Porównaj każdą jednostkę źródła i celu, poprawiając sens, pominięcia, dodatki, nazwy i styl. Poprawna odpowiedź API nie oznacza zatwierdzenia znaczenia. Zapisz pracę, aby wrócić później. Jeśli tłumaczenie nie jest potrzebne, możesz skończyć po eksporcie źródła bez wywoływania API.
