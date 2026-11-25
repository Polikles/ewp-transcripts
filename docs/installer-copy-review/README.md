# Teksty instalatora EwP — korekta EN/PL

Tabela przedstawia obecne teksty instalatora **0.24.2**. Jest materiałem do korekty;
jej przygotowanie nie zmienia tekstów programu. Zatwierdzony wcześniej arkusz
interfejsu aplikacji pozostaje bez zmian.

Otwórz **EwP-instalator-EN-PL-do-korekty-2026-11-25.xlsx**, zacznij od arkusza `Start`.
Alternatywa: **EwP-instalator-EN-PL-do-korekty.csv**, UTF-8 z BOM, separator średnik.
Podgląd `podglad.html` w paczce służy do czytania; korekty wpisuj w XLSX albo CSV.

## Jak poprawiać

- Edytuj kolumny **EN** i **PL**. Możesz poprawiać oba języki.
- W kolumnie **Decyzja** wybierz `ZMIANA`, `BEZ ZMIAN`, `USUNĄĆ` lub `PYTANIE`.
  Komentarze i propozycje reorganizacji wpisz w **Uwagi do korekty**.
- Zachowaj **ID**, nazwy parametrów w `{nawiasach}`, kody, nazwy własne i istotne
  spacje we fragmentach. Możesz filtrować i sortować wiersze.
- Przy zmianie pełnego zdania nie musisz poprawiać osobno jego wszystkich fragmentów.
  Pełny komunikat ma kontekst, dzięki któremu rozstrzygniemy powiązania przy integracji.
- Zachowaj plik bazowy i odeślij kopię z korektami. Ukryte kolumny oryginału oraz
  arkusz `_oryginal` pomagają porównać wersje; nie trzeba ich edytować.

## Zawartość

| Arkusz | Wpisy | Zakres |
| --- | ---: | --- |
| Interfejs | 179 | Etykiety, opisy operacji, przyciski, komunikaty, okna kluczy, instrukcje, podpowiedzi |
| Pelne_komunikaty | 57 | Pełne zdania składane z fragmentów, nagłówki, dysk, modele, postęp, raport |
| Raport_i_terminal | 237 | Własne teksty diagnostyki, logów, błędów i skryptów instalacji/usuwania |
| Notices_projektu | 61 | Informacje projektu, autorstwo i warunki assetów; uwagi o komentarzach wewnętrznych |
| Oryginalne_licencje | 569 | Akapity oryginalnych licencji do wglądu; uwagi wpisuj obok |
| Linki | 15 | Adresy instrukcji, modeli i usług, z rozróżnieniem endpointów technicznych |
| Dane_i_formaty | 14 | Jednostki, formaty dat, wzorce błędów i identyfikatory modeli |
| Archiwum_ID | 16 | Dawne wpisy pomocniczego CSV, które nie są aktualnymi tekstami ekranu |

Łącznie **1148 wpisów**. Główną korektę zacznij od `Interfejs` i `Pelne_komunikaty`.
W `Notices_projektu` oznaczono m.in. instrukcje dla twórców, odwołania do prywatnych
materiałów i niezweryfikowany adres autora. To punkty do oceny, nie zatwierdzone zmiany
prawne. Pełne, niezmienione bajtowo 12 plików notices/licencji z dostarczonego pakietu
są w katalogu `oryginalne-notices` paczki.

Identyczne EN i PL w raporcie lub notices oznacza, że aktualnie ten tekst także
w polskiej wersji występuje po angielsku. Nie jest to proponowane tłumaczenie.
Wiersze oryginalnych licencji i danych technicznych mają inne tło.

## Kompletność i ograniczenia

Inwentaryzacja obejmuje wszystkie operacje instalatora Windows, modalne instrukcje HF/OR,
start, błędy, postęp, zapis raportu oraz wspólne własne komunikaty instalacji, diagnostyki
i usuwania w Pythonie/PowerShellu/skryptach. Zachowuje wszystkie 179 wcześniejszych ID
(163 aktywne i 16 archiwalnych). Pełne szablony pokazują również wartości dynamiczne.

Nie istnieje zamknięta lista zmiennych komunikatów zewnętrznych narzędzi, systemu Windows,
odpowiedzi serwerów i wyjątków bibliotek. Takie dane w raporcie nie są własną kopią UI.
Tabela nie zastępuje zatwierdzonego arkusza aplikacji ani osobnego przeglądu podręczników.

`coverage.json` zawiera źródła, skróty kontrolne, powiązania i klasyfikację 1075 literałów C#.
Kontrola obejmuje zgodność danych XLSX/CSV, unikalność ID, parametry EN/PL pełnych szablonów,
brak formuł i zgodność oryginalnych notices z pakietem. Nie używano Excela/LibreOffice;
sprawdzono zapis i ponowny odczyt komórek oraz układ danych, nie natywne renderowanie Excela.

## Odtworzenie przez programistę

Baza inwentaryzacji: `f36f1e87b5c871d760da1fc956e4c409513a3b3c`,
produkt 0.24.2 ze źródła `7178bc7478897016e9663905739adb48afe73c00`.
Skrypt używa dodatkowo ręcznie zinwentaryzowanych pełnych szablonów z `templates.json`.
Wymagany osobny tymczasowy Python z `openpyxl==3.1.5`; bez zmian zależności produktu.

```sh
python tools/build_installer_copy_review.py \
  --bundle /home/linuch/project-ewp/deliveries/ewp-0.24.2-installers/EwP-0.24.2-windows-x64.zip \
  --output /tmp/nowy-katalog-przegladu
```

Skrypt wymaga nowego katalogu, aby nie nadpisać tabeli przekazanej do korekty.
Po otrzymaniu zmian: porównać po ID z oryginałem, uzgodnić pytania i dopiero wtedy
wprowadzić zaakceptowane teksty oraz zaktualizować odpowiednie instrukcje offline.
