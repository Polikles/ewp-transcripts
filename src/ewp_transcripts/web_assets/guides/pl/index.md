# Instrukcja użytkownika

Instrukcja opisuje bieżący interfejs wersji 0.23.0. Język interfejsu wybiera się osobno od języka nagrania. Wszystkie rozdziały są dołączone do programu i otwierają się bez internetu. Numeracja instrukcji odpowiada krokom widocznym u góry poszczególnych etapów. Podczas czytania pozostaw otwartą kartę programu.

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

Do lokalnej transkrypcji zalecamy jako punkt wyjścia nowszą kartę **NVIDIA RTX z 12 GB VRAM lub więcej**,
**32 GB RAM**, wielordzeniowy procesor x64 i dysk SSD. Konfiguracja odniesienia sprawdzona w pracy
programu to **RTX 3090 z 24 GB VRAM**. Rekomendacja nie oznacza przetestowania każdej takiej karty;
**8 GB VRAM nie jest jeszcze potwierdzonym minimum**. Znaczenie ma również architektura: obecne
pakiety PyTorch 2.8/CUDA 12.8 nie obsługują Pascal, w tym GTX 1070. Przyszłe testy GTX 1070/32 GB/i5-10400F
zaczną się od zgodności środowiska, potem zmierzą zapas VRAM i wydajność. Na instalację przeznacz 25 GB,
a na dodatkowe modele, nagrania i wyniki osobne miejsce. ASR w chmurze i praca z gotowymi wynikami
nie wymagają lokalnej karty NVIDIA. AMD Windows pozostaje eksperymentalne; wyrównanie i rozpoznawanie
mówców działa na CPU. [Szczegóły sprzętowe](https://github.com/Polikles/ewp-transcripts/blob/main/docs/HARDWARE.md).

## Prywatność i zakres obsługi

Lokalna transkrypcja GPU korzysta z modeli pobranych jawnie podczas przygotowania. Opcjonalne ASR OpenRouter wysyła audio, a korekta i tłumaczenie przez API wysyłają tekst. Sprawdzanie połączenia i odświeżanie cen nie wysyłają nagrań. Każda propozycja wymaga ręcznego sprawdzenia. Zapisy pracy i profile nie zawierają kluczy ani zgód na wysłanie danych i ręczne zatwierdzenie.

To lokalne narzędzie dla jednego użytkownika do podkastów i podobnych nagrań. Serwer nasłuchuje wyłącznie lokalnie; nie jest publiczną usługą dla wielu użytkowników. Testy odniesienia wykonano na RTX 3090 z 24 GB VRAM. Cel 8 GB VRAM wymaga zgodnej architektury i bibliotek; nie jest potwierdzonym minimum. Można wybrać EN, ale do ostatnich testów chmurowych nie dostarczono reprezentatywnego nagrania EN. Program nie gwarantuje dokładności rozpoznania dla żadnego języka ani modelu.

Instrukcja tekstowa obejmuje obecny proces pracy. Zrzuty ekranu i końcowe ikony powstaną osobno; nie są wymagane do korzystania z tych instrukcji.
