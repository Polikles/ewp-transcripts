# Instrukcja użytkownika

Instrukcja opisuje bieżący interfejs wersji 0.26.2. Język interfejsu wybiera się osobno od języka nagrania. Wszystkie rozdziały są dołączone do programu i otwierają się bez internetu. Numeracja instrukcji odpowiada krokom widocznym u góry poszczególnych etapów. Podczas czytania pozostaw otwartą kartę programu.

## Zacznij tutaj

1. Wykonaj [instalację i aktualizację](installation.md) dla Windows 11 x64 albo WSL2 z Ubuntu 24.04/26.04.
2. [Transkrypcja](transcribe.md): wybierz katalog wyników, dodaj audio lub wideo, zaplanuj wszystkie nagrania, potwierdź plan, dodaj zadania do kolejki i uruchom ją.
3. [Opcjonalna korekta](optional-correction.md): wygeneruj wstępną korektę albo pomiń pomoc LLM.
4. [Weryfikacja i eksport źródła](source-review.md): sprawdź mówców, kolory i tekst, zatwierdź szkic, potwierdź ręczną weryfikację, zapisz zweryfikowaną rewizję i wyeksportuj napisy.
5. [Opcjonalne tłumaczenie](optional-translation.md): pomiń pomoc LLM, aby tłumaczyć ręcznie, albo wygeneruj propozycję tłumaczenia.
6. [Weryfikacja tłumaczenia i eksport](translation-review.md): porównaj źródło z tłumaczeniem, zastosuj szkic, potwierdź znaczenie, zapisz tłumaczenie i wyeksportuj napisy.

Najkrótsza lokalna ścieżka to Transkrypcja → Weryfikacja i eksport źródła. Słowniki, pomoc LLM i tłumaczenie są opcjonalne. Import gotowego canonical JSON pozwala pominąć ASR. Ukończenie ASR nie oznacza, że materiał nadaje się już do publikacji.

## Zachowaj i przenieś pracę

- [Zapisana praca i porządkowanie](saved-work.md): punkty zapisu, ponowne uruchomienie, kopie zapasowe, ostatnie lokalizacje i zarządzane kopie źródeł.
- [Słowniki](dictionaries.md): tworzenie, porównanie, edycja nowej wersji oraz niezależny import i eksport.
- [Ustawienia i informacje](settings.md): przenośne profile użytkownika, wspólny klucz OpenRouter, diagnostyka, opcjonalne ETA i usuwanie plików tymczasowych.
- [Pliki i eksporty](outputs.md): surowe wyniki, edytowalne szkice, zweryfikowane wersje i lokalizacje pobieranych plików.
- [Rozwiązywanie problemów](troubleshooting.md), [instalacja Windows](windows-native.md) i [naprawa po aktualizacji Ubuntu](ubuntu-upgrade.md).
- [Obsługa z terminala](cli.md): konfiguracja, grupy poleceń i przykłady bezpiecznego użycia.

## Zalecany sprzęt

Do w pełni lokalnej transkrypcji zalecamy zgodną **kartę NVIDIA z co najmniej 12 GB VRAM**, **32 GB RAM**
i dysk SSD. Sprawdzone odniesienie: **RTX 3090/24 GB**.12 GB to wymaganie orientacyjne. Na mniejszych
konfiguracjach program może działać, ale nie były one testowane i nie gwarantujemy działania;
**poniżej 12 GB VRAM zalecamy ASR w chmurze**.
Przypięte biblioteki CUDA 12.8 Update 1 wymagają obsługiwanej architektury z Compute Capability 7.0+
(Volta; typowe GeForce: Turing/RTX20xx/GTX 16xx lub nowsze). Przyjęta wersja sterownika to co najmniej
Windows/WSL 572.61 albo natywny Linux 570.124.06. Maxwell/Pascal, w tym GTX 1070, nie obsługuje tego lokalnego
silnika. Osobny CUDA Toolkit nie jest wymagany. Test komputera wyjaśnia brak zgodności karty lub
sterownika, a przy zgodnej karcie z mniej niż 12 GB ostrzega o prawdopodobnym braku działania,
nieprzetestowaniu i braku gwarancji. Wybór lokalny przy małej pamięci pozostaje dobrowolny.
Instalacja chmurowa lub aktualizacja samego programu nadal jest dostępna. Przeznacz 25 GB oraz
miejsce na dodatkowe modele/nagrania/wyniki. AMD jest eksperymentalne, z wyrównaniem i mówcami na CPU.
[Szczegółowa zgodność](https://github.com/Polikles/ewp-transcripts/blob/main/docs/HARDWARE.md).

## Prywatność i zakres obsługi

Lokalna transkrypcja GPU korzysta z modeli pobranych jawnie podczas przygotowania. Opcjonalne ASR OpenRouter wysyła audio, a korekta i tłumaczenie przez API wysyłają tekst. Sprawdzanie połączenia i odświeżanie cen nie wysyłają nagrań. Każda propozycja wymaga ręcznego sprawdzenia. Zapisy pracy i profile nie zawierają kluczy ani zgód na wysłanie danych i ręczne zatwierdzenie.

To lokalne narzędzie dla jednego użytkownika do podkastów i podobnych nagrań. Serwer nasłuchuje wyłącznie lokalnie; nie jest publiczną usługą dla wielu użytkowników. Testy odniesienia wykonano na RTX 3090 z 24 GB VRAM. Mniejsze zgodne konfiguracje mogą działać, ale nie były testowane i nie gwarantujemy działania; poniżej12 GB VRAM zalecamy ASR w chmurze. Można wybrać EN, ale do ostatnich testów chmurowych nie dostarczono reprezentatywnego nagrania EN. Program nie gwarantuje dokładności rozpoznania dla żadnego języka ani modelu.

Instrukcja tekstowa obejmuje obecny proces pracy. Zrzuty ekranu i końcowe ikony powstaną osobno; nie są wymagane do korzystania z tych instrukcji.
