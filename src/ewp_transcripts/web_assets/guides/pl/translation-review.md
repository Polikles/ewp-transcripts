# Weryfikacja tłumaczenia i eksport

Używaj poniższych kroków razem z odpowiadającym im etapem GUI.

1. Wybierz nagranie: Otwórz ręczne tłumaczenie nagrania lub zapisaną propozycję z kolejki. Sprawdź źródło i kierunek.
2. Sprawdź źródło i tłumaczenie: Porównaj każdą jednostkę źródła z tłumaczeniem i popraw znaczenie, nazwy, pominięcia i dodatki.
3. Zastosuj tłumaczenie: Zastosuj tłumaczenie zapisuje i sprawdza szkic. Usuń błędy i sprawdź ostrzeżenia; ta czynność nie zapisuje jeszcze wersji do eksportu.
4. Zapisz tłumaczenie: Potwierdź ręczną weryfikację znaczenia i kliknij Zapisz i przygotuj do eksportu, aby zapisać niezmienną wersję tłumaczenia.
5. Zatwierdź i eksportuj: Wybierz formaty i kliknij Zatwierdź i eksportuj. Przed eksportem sprawdzana jest zgodność ze źródłem. Przejdź do następnego wyniku wraca do kolejki.

## 1. Wybierz nagranie

Otwórz ręczne tłumaczenie lub propozycję wybranego nagrania. Sprawdź canonical JSON, opcjonalną rewizję źródła i kierunek. Każde nagranie przywraca własny przegląd; przejście między etapami nie powinno wymagać kolejnego płatnego generowania. Jeśli ścieżka lub hash nie pasują, przywróć poprawny oryginał zamiast edytować pochodzenie w JSON.

## 2. Sprawdź źródło i tłumaczenie

Czytaj niezmienne źródło obok każdej edytowalnej jednostki tłumaczenia. Sprawdź znaczenie, przeczenia, nazwy, liczby, cytaty, mówców, pominięcia, dodatki i styl. Zachowuj niepewność źródła. Zapisz szkic tłumaczenia utrwala niedokończoną pracę. Cofnij i Ponów dotyczą bieżącego szkicu. Przywróć zapisany szkic otwiera ostatni zapis, a wyczyszczenie bieżącej weryfikacji czyści widok po potwierdzeniu.

Puste tłumaczenia domyślnie powodują błąd. Jeśli pominięcie jest celowe, włącz dopuszczenie pustych jednostek przed sprawdzeniem i zapisem końcowym. Niezmienne tłumaczenie i audyt odnotują pominięcie. Eksport tekstu i napisów pominie taką jednostkę bez pustego napisu. Potwierdzenie nie przenosi się między niezwiązanymi weryfikacjami.

## 3. Zastosuj tłumaczenie

Zastosuj tłumaczenie zapisuje i sprawdza szkic. Przeczytaj ostrzeżenia i usuń błędy. Nie zapisuje to jeszcze zweryfikowanego tłumaczenia. Edycja po sprawdzeniu unieważnia jego wynik; zastosuj szkic ponownie. Przyciski odpowiadają układowi weryfikacji źródła: Zastosuj jest pierwsze, a czyszczenie znajduje się osobno niżej.

## 4. Zapisz tłumaczenie

Po sprawdzeniu wszystkich jednostek zaznacz ręczną weryfikację znaczenia i wybierz Zapisz i przygotuj do eksportu. Powstanie niezmienne tłumaczenie powiązane z dokładnym źródłem. Rewizja źródłowa się nie zmienia. Techniczne ID i hashe służą potwierdzeniu pochodzenia, a nie edycji treści.

## 5. Zatwierdź i eksportuj

Wybierz formaty i kliknij Zatwierdź i eksportuj. Program sprawdzi zgodność pochodzenia przed zapisaniem plików. Eksporty znajdują się w `translation-exports` pod katalogiem wynikowym tłumaczenia. Pobieranie zapisanych eksportów zwraca te konkretne pliki. Odświeżanie sprawdza istniejące wersje i nie uruchamia tłumaczenia ani ponownego generowania. Zachowaj niezmienne tłumaczenia, audyty i rewizje źródła razem z eksportami.

Przejdź do następnego wyniku wraca do kolejki. Stan zadania zmienia się po utworzeniu propozycji, końcowym zapisie i eksporcie. Sam eksport SRT albo samego VTT wystarcza do oznaczenia eksportu. Aby wrócić później, [zapisz pracę](saved-work.md), a po restarcie otwórz weryfikację tego samego nagrania.
