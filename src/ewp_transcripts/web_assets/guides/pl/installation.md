# Instalacja i aktualizacja

Od0.25.0 instalacja zarządzana otwiera własne okno Windows bez PowerShell/przeglądarki.
Skrót ponownie przywołuje to samo okno. Zamknięcie zapisuje pracę; aktywne zadania można dokończyć
lub zatrzymać. Szczegóły: [Uruchamianie i zamykanie](windows-native.md).
Wymagany jest Microsoft WebView2 Evergreen Runtime; brak składnika pokazuje komunikat z linkiem
Microsoft. Runtime .NET jest dołączony do programu.

Instalator ma zatwierdzone opisy EN/PL oraz jasny motyw graficzny w tle części głównej.
Komunikaty „Pobierz nowszą wersję instalatora” zawierają link do [katalogu releases](https://github.com/Polikles/ewp-transcripts/tree/main/releases).
Pierwszy publiczny instalator pojawi się tam po ukończeniu natywnego interfejsu Windows.
Komentarz o $2 pod instrukcją OpenRouter opisuje wcześniejsze testy, nie gwarantuje kosztu;
wyświetla się osobno mniejszą czcionką. Informacje projektu są dostępne po polsku, a oryginalna
AGPL i licencje dostawców pozostają w niezmienionej wersji angielskiej. Dziennik i raport
techniczny również pozostają po angielsku.

Nowa instalacja wykrywa istniejącą instalację w kroku 2, przed diagnostyką i pobieraniem,
również po wybraniu innego pustego folderu. Dla starszej wersji wybierz Aktualizuj, dla tej samej
Napraw, a dla nowszej Przywróć poprzednią wersję lub pobierz nowszy instalator. Kreator pokazuje
wykryty folder i wersję. Oba opisy miejsca przy nowej instalacji wymagają 25 GB. Sprawdzenie jest
ponawiane przed przygotowaniem programu. Kompletne modele w cache nadal nie wymagają tokenu HF.

## Bieżące zachowanie instalatora

Aktualizacja zachowuje niezmienione wersje modeli i nie wymaga tokenu HF ani klucza OR.
Naprawa domyślnie obejmuje sam program, a diagnostyka uruchamia się automatycznie.
Sprawdź modele weryfikuje lokalizacje, wersje i sumy kontrolne plików bez pobierania.
Pobierz ponownie modele pozwala następnie wybrać konkretne modele. Publiczne modele nie
wymagają HF; przycisk tokenu pojawia się dla wybranego brakującego lub ponownie pobieranego
modelu wymagającego dostępu. Doinstalowanie modeli także uruchamia diagnostykę automatycznie
bez pytania o OR. Test dysku rozróżnia pełny budżet20 GB programu i podstawowych modeli
od dodatkowego wolnego miejsca potrzebnego do operacji.

Większy trybik po lewej, aktualny etap, czynność i czas pokazują przebieg instalacji.
Pobieranie plików modeli i FFmpeg pokazuje mierzone bajty, prędkość i przybliżony pozostały czas.
Etapy bez mierzalnej całości używają paska aktywności. Raporty mają datę i czas w treści
oraz proponowanej unikalnej nazwie.

Skrót pulpitu i wpis programu mają ikonę EwP. Lista programów pokazuje zmierzony rozmiar
programu, cache i modeli. Dodaj/usuń programy oferuje Napraw, Przywróć poprzednią wersję
oraz Odinstaluj. Plik `uninstall.exe` w folderze programu oferuje Napraw i Odinstaluj.
`Remove-EwP.ps1` działa bez wewnętrznego argumentu Plan. Pliki programu i skróty są usuwane
przed komunikatem sukcesu; po zamknięciu okna usuwa się tylko sam deinstalator. Pliki tylko do
odczytu są obsługiwane, a praca użytkownika, w tym `work-state` i `outputs`, pozostaje.
Wpis programu znika dopiero po pomyślnym usunięciu. Przy błędzie zachowany zostaje datowany
raport w katalogu podanym w dzienniku instalatora.

Tylko pierwsza instalacja ma pięć kroków; pozostałe operacje mogą mieć ich mniej.
Ogólny pasek etapów i licznik pobrań obejmują całą operację; drugi pasek dotyczy bieżącego pliku.
Pola postępu zachowują położenie, a raz otwarty dziennik pozostaje rozwinięty.

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

## Wybierz sposób instalacji

1. W Windows uruchom kreator `EwP-Setup-0.26.2.exe` i wykonaj opisane niżej kroki.
2. Do instalacji terminalowej pobierz ZIP Windows albo tar.gz/ZIP Ubuntu i użyj krótkich poleceń poniżej. Nie trzeba ręcznie klonować repozytorium ani wcześniej instalować Python i uv.
3. Jeśli pracujesz z repozytorium jako programista lub dotychczasowy użytkownik, zachowaj ten sposób i korzystaj z sekcji aktualizacji checkoutu. To nie jest instalacja zarządzana.

Instalacja zarządzana pojawiła się w0.22.0;0.25.0 dodaje własne okno aplikacji Windows. Paczki testowe są dostępne w przekazanej paczce oraz w zadaniu Actions „Installer build and Windows startup” repozytorium. Publiczne skrypty pobierania zaczną działać po publikacji pasującego wydania. Nie zgaduj adresu pobierania. Obecny EXE jest niepodpisany; nie dostarczono certyfikatu podpisywania kodu.

Obecne cele to Windows 11 x64 oraz Ubuntu 24.04/26.04, w tym WSL2. Wcześniejsze testy programu w Windows/WSL pozostają zaakceptowane. Nowy cykl instalacji zarządzanej ma rzeczywiste testy na VM Ubuntu; pełny test instalacji i usuwania na Windows 11 jest osobny od kompilacji lub uruchomienia okien na runnerze CI. Testowe GPU to RTX 3090 24 GB. 12 GB+ to orientacyjne zalecenie lokalne; mniejsze zgodne karty nie były testowane i powinny używać ASR w chmurze.

## AMD w Windows (experimental)

Od0.26.0 komputer Windows z samą kartą AMD może używać ROCm/HIP do ASR. Wyrównanie słów
oraz rozpoznawanie mówców działa na CPU. Transkrypcja i wydajność na fizycznej karcie AMD nie
zostały przetestowane. Wykrycie karty AMD przy instalacji lub aktualizacji otwiera okienko
**obsługa kart AMD jest eksperymentalna i nie została przetestowana** z przyciskiem
**Rozumiem, kontynuuj**. Zamknięcie okienka pozostawia „Dalej” zablokowane. Ostrzeżenie pojawia się
również przy kartach obu producentów; nowa instalacja domyślnie zachowuje wtedy NVIDIA.
Sam procesor AMD nie uruchamia tego profilu. Odpowiedni sterownik GPU instaluje się osobno.

Zweryfikowane biblioteki wymagają dodatkowo około1,33GB pobierania i3,71GB po rozpakowaniu,
bez zmiany modeli. Automatyczna diagnostyka sprawdza dostępność HIP i float16; niezgodny sprzęt
lub sterownik kończy się błędem diagnostyki. W terminalu potwierdzenie ma postać
`-AcceptExperimentalAmd`. [Opis implementacji i ograniczeń](https://github.com/Polikles/ewp-transcripts/blob/main/docs/AMD_EXPERIMENTAL.md)
oraz [uruchamianie i naprawa Windows](windows-native.md). Ten adapter nie włącza AMD w Ubuntu/WSL.

## Kreator Windows

Uruchom `EwP-Setup-0.26.2.exe` na zwykłym koncie użytkownika. Paczka zawiera program,
środowisko graficzne i wyśrodkowane logo EwP w ramce; nie zawiera wielogigabajtowych modeli.

1. **Działanie i język.** Wybierz English/Polski oraz jedno działanie: Zainstaluj, Aktualizuj,
   Napraw, Doinstaluj modele lokalne, Przywróć poprzednią wersję albo Odinstaluj. Następny ekran
   zależy od tego wyboru.
2. **Lokalizacja i test.** Przy instalacji wybierz **Folder instalacji programu**, osobny od
   nagrań i starego repozytorium. Ilość miejsca na tym dysku jest sprawdzana automatycznie;
   Dalej nie działa poniżej **25 GB** (20 GB instalacji plus5 GB wolnego marginesu). Uruchom
   Wymagany test uruchamia się automatycznie po wejściu na ten ekran z prawidłową lokalizacją,
   przy instalacji, aktualizacji, naprawie i doinstalowaniu modeli. Po zmianie folderu ponownie
   sprawdzane jest miejsce na dysku; wyniki CPU, systemu, GPU i środowiska pozostają zachowane.
   **Sprawdź komputer** pozwala powtórzyć pełną diagnostykę.
   Wyniki pokazują OK i zmieniają język wraz z wyborem języka. System ma nazwę wydania, np.26H2;
   starsze lub nierozpoznane wydanie dostaje ostrzeżenie o zgodności. Link bibliotek Visual C++
   pojawia się dopiero po wyniku brakującym lub niejednoznacznym i otwiera instrukcję Microsoft
   zamiast od razu pobierać EXE. Brakujący sterownik NVIDIA zainstaluj
   osobno. Test może przygotować małe prywatne środowisko Python.
3. **Lokalne modele i token HF.** Zaznacz **Użyj lokalnych modeli na moim GPU…**, aby zobaczyć
   listę podstawowych modeli i potrzebne miejsce (około8,4 GB przed użyciem cache, plus dane językowe).
   Opcjonalne Whisper Large v3 (około3,1 GB) i Large v3 Turbo (około1,6 GB) są domyślnie niezaznaczone.
   Istniejące dokładne pliki są wykorzystywane ponownie; dysk cache jest sprawdzany osobno.
   **Podaj token Hugging Face** otwiera maskowane okno: wklejenie uruchamia test, **Sprawdź token**
   go powtarza, a **OK** przyjmuje poprawny wynik. Na ekranie głównym pojawia się Token prawidłowy
   i dopiero wtedy można potwierdzić zaakceptowanie warunków pyannote. Ikona informacji otwiera okno z krokami
   założenia konta, dostępu do modelu i tokenu Read oraz [pełną instrukcję HF](https://github.com/Polikles/ewp-transcripts/blob/main/Instructions/HUGGINGFACE_ACCESS_PL.md).
   Token pozostaje w pamięci tylko podczas instalacji. Przy próbie przejścia dalej brakujące
   wymagane potwierdzenie zostaje podświetlone.
4. **Klucz OpenRouter (opcjonalnie).** Załóż konto, doładuj je, wybierz obszar Default,
   a następnie utwórz klucz API z niskim limitem wydatków. Linki w krokach otwierają właściwe strony.
   Podaj klucz OpenRouter otwiera maskowane okno testu. Możesz też przejść dalej bez klucza i dodać
   go później w programie. Zatwierdzony klucz trafia do magazynu systemowego dopiero podczas
   instalacji; nie oznacza to zgody na wysyłanie audio. Traktuj tokeny jak hasła.
5. **Instalacja i wynik.** Dalej rozpoczyna wybraną operację. Zębatka i opisy etapów pokazują
   postęp. Nawigacja to Wstecz/Dalej/Anuluj. Anulowanie przygotowania zatrzymuje procesy i zachowuje
   poprzednią aktywną wersję oraz pobrane cache. Krótkie końcowe zatwierdzanie/usuwanie musi się
   zakończyć przed zamknięciem. Po sukcesie uruchom program z kreatora lub skrótu na pulpicie.
   Licencje i autorstwo są linkiem w lewym dolnym rogu każdego ekranu. Zapisz raport znajduje się
   pod Szczegółami technicznymi/dziennikiem, a Zamknij w prawym dolnym rogu.

Aktualizacja, naprawa, doinstalowanie modeli, przywracanie i deinstalacja automatycznie wykrywają
zarządzaną instalację i pokazują jej lokalizację. Pytanie o folder pojawia się tylko, gdy jej nie
znaleziono; link Wybierz inną instalację pozwala wskazać alternatywną. Repozytorium Git nie jest
przejmowane jako instalacja zarządzana. Zmiana działania resetuje dalsze ekrany, ścieżki, wyniki
i klucze do wartości domyślnych nowej operacji. Aktualizacja używa wersji
wbudowanej w instalator; Napraw i Doinstaluj modele wymagają zgodnej wersji, aby nie aktualizować
starszego programu bez wyboru Aktualizuj. Doinstalowanie korzysta z tych samych modeli i kontroli
dostępu. Rollback pomija formularze modeli i kluczy. Deinstalacja pokazuje plan usunięcia oraz
opcje zachowania modeli/klucza przed jawnym potwierdzeniem. Dodaj/usuń programy otwiera ten kreator.

Osobny pusty folder, np. `D:\Transcripts-test-01`, jest dozwolony, podobnie jak osobny folder
wewnątrz Program Files. Wybranie w oknie katalogów całego dysku albo samego Program Files dodaje
podkatalog `EwPTranscripts`; kontener nie staje się katalogiem programu. Test komputera nie wymaga
uprawnień administratora. Windows może poprosić o nie dopiero przy właściwej instalacji,
aktualizacji lub usuwaniu. Zatwierdź na tym samym koncie Windows, aby zachować właściciela modeli
i magazynu kluczy. Zwykłe uruchamianie programu nie wymaga administratora tylko dlatego, że program
jest w Program Files: blokada aktywności jest zapisana w profilu użytkownika.
Przy podwyższonych uprawnieniach brakujące modele pobierane są tylko do katalogu bez dowiązań
wewnątrz profilu tego użytkownika. Niestandardowy cache poza profilem przygotuj wcześniej jako
zwykły użytkownik; kompletne istniejące modele nadal można wykorzystać ponownie.

Bez modeli lokalnych można używać ASR OpenRouter lub weryfikować/eksportować istniejące wyniki;
domyślnym silnikiem nagrań pozostaje lokalne GPU. OR jest opcjonalny i niepotrzebny do pracy lokalnej.
Tokeny/klucze nie trafiają do profili, raportów ani tekstowego zapisu awaryjnego. Patrz [Ustawienia](settings.md).

## Instalacja terminalowa z pobranej paczki

PowerShell w Windows, w katalogu pobranego ZIP:

```powershell
Expand-Archive .\EwP-0.26.2-windows-x64.zip -DestinationPath .\EwPSetup
powershell -ExecutionPolicy Bypass -File .\EwPSetup\control\Install-EwP.ps1 -Bundle .\EwP-0.26.2-windows-x64.zip
```

Po zaakceptowaniu warunków modelu dodaj `-Local -AcceptModelTerms`, aby przygotować modele lokalne. Monit tokenu jest ukryty; pusta odpowiedź pozwala użyć kompletnych modeli. `-SaveOpenRouterKey` włącza osobny ukryty monit i jawny zapis OR w systemie. `-Root 'D:\Apps\EwP'` wybiera własny pusty katalog. Obejście polityki PowerShell dotyczy tylko tego uruchomienia. Ścieżki ze spacjami obejmuj cudzysłowami.

Ubuntu 24.04/26.04, w katalogu pobranego tar.gz:

```bash
mkdir -p EwPSetup
tar -xzf EwP-0.26.2-ubuntu-x64.tar.gz -C EwPSetup
bash EwPSetup/control/Install-EwP.sh install --bundle "$PWD/EwPSetup/bundle.zip"
```

Dodaj `--local --accept-model-terms` dla modeli, `--save-openrouter-key` dla ukrytego monitu OR lub `--root "$HOME/Apps/EwP"` dla innej lokalizacji. Brakujące pakiety Ubuntu można zainstalować po jawnym monicie sudo. Nie instaluj sterownika ekranu Linuksa wewnątrz WSL; CUDA udostępnia sterownik Windows. Zgodność z fizycznym Ubuntu trzeba potwierdzić wykonaniem, a nie wnioskować tylko z WSL.

Plik SHA256SUMS służy do sprawdzenia pobranych plików. Skrypty online `Install-EwP-0.26.2.ps1` i `.sh` są generowane z dokładnymi hashami paczek pasującego wydania; nie pobiorą nieopublikowanego wydania. Skrypty i GUI używają wspólnego mechanizmu, blokady zależności i zasad modeli.

## Aktualizacja zarządzana i poprzednia wersja

Zapisz pracę i kopię oraz zakończ lub bezpiecznie anuluj zadania. Aktualizacja/usuwanie w natywnym
Windows prosi okno programu o zapis i zamknięcie; odmowa zapisu blokuje wymianę/usuwanie plików.
W jawnym trybie przeglądarkowym zamknięcie karty nie zatrzymuje serwera: po zapisie zatrzymaj go
przez Ctrl+C. Blokada systemowa i zweryfikowana tożsamość procesu chronią aktywnego/nieznanego
właściciela; porzucone metadane martwego procesu są odzyskiwane.

Pobierz i uruchom nowy instalator dla istniejącego katalogu zarządzanej instalacji albo użyj paczki terminalowej. Kreator używa własnej wbudowanej wersji i nie ma wyboru ZIP-a. Przykłady domyślnej lokalizacji:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\EwPTranscripts\Install-EwP.ps1" -Action update -Bundle 'C:\Downloads\NEW_WINDOWS_BUNDLE.zip'
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\EwPTranscripts\Install-EwP.ps1" -Action rollback
```

```bash
bash "$HOME/.local/share/ewp-transcripts/installation/Install-EwP.sh" update --bundle '/path/NEW_UBUNTU_BUNDLE.zip'
bash "$HOME/.local/share/ewp-transcripts/installation/Install-EwP.sh" rollback
```

Zastąp nazwę dużymi literami rzeczywistym pobranym plikiem. Aktualizacja i naprawa CLI zachowują poprzedni wybór modeli, chyba że podasz `--cloud-only`/`-CloudOnly` albo jawnie wybierzesz lokalne modele. Kompletne niezmienione modele nie wymagają ponownego pobrania. Nowe lub brakujące modele chronione nadal wymagają zgody i tokenu. Program sprawdza prywatny FFmpeg, przypięte zależności i numer aplikacji przed atomowym przełączeniem aktywnej wersji.

Nieudane przygotowanie zachowuje poprzednią aplikację. Rollback wybiera zachowaną sprawdzoną wersję i nie przepisuje danych użytkownika. To wydanie nie migruje obszarów ani profili. Nie zakładaj, że dowolna przyszła zmiana schematu pozwoli bezpiecznie wrócić do starszej wersji. Zachowywane są aktywne i bezpośrednio poprzednie środowisko. Starsze pliki programu są porządkowane po udanym przełączeniu, z zachowaniem dodanych plików projektu. Wyniki, modele, profile, słowniki i klucze nie są resetowane.

## Deinstalacja zarządzana

Użyj kreatora, „Dodaj/usuń programy” albo przygotuj podgląd w terminalu:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:LOCALAPPDATA\EwPTranscripts\Install-EwP.ps1" -Action uninstall
```

```bash
bash "$HOME/.local/share/ewp-transcripts/installation/Install-EwP.sh" uninstall
```

Przeczytaj plan. Ponów z `-Yes`/`--yes`, aby potwierdzić. Opcjonalne `-RemoveModels`/`--remove-models` usuwa dokładne zarejestrowane snapshoty, a `-RemoveKey`/`--remove-key` wspólny zapis OR. To niezależne wybory; domyślnie pozostają zachowane. Niestandardowe lub nieweryfikowalne lokalizacje modeli są chronione. Bloby HF używane przez inne snapshoty pozostają; cały cache HF nie jest kasowany. Modele mogą być używane przez inne programy, więc sprawdź tę decyzję.

Oryginalne nagrania, publikacje i stan użytkownika nie należą do usuwania środowiska. Nieznane pliki dodane wewnątrz katalogu wersji także pozostają; dlatego katalog może nie być pusty po deinstalacji. Windows kończy usuwanie blokowanych plików po wyjściu kreatora i interpretera. Wpisy pulpitu i rejestru należące do innej instalacji nie są usuwane. Tymczasowe środowiska bootstrapu są sprzątane po zakończeniu skryptu. Uruchomienie, rollback i deinstalacja zainstalowanego programu w Ubuntu używają istniejącego prywatnego Pythona bez ponownego pobierania środowiska.

Starszy checkout Git nie jest instalacją zarządzaną i nie jest usuwany na podstawie zgadywanych ścieżek. Zachowaj kopię przed ręcznym porządkowaniem. Nowy instalator może działać obok niego i używać tych samych dokładnych modeli. Profile i obszary przenoś świadomie, sprawdzając ścieżki oryginalnych mediów.

## Instalacja i aktualizacja z repozytorium

Windows i WSL muszą mieć osobne repozytoria i środowiska. Do nowej instalacji źródłowej Windows przygotuj Git, uv, sterownik NVIDIA do lokalnego ASR i Visual C++ x64, a potem:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Install
uv run --locked --no-sync python scripts/setup-models.py
uv run --locked transcriber doctor --test-speech-runtime
uv run --locked transcriber gui
```

Dla świeżego checkoutu Ubuntu:

```bash
./scripts/install-fresh-ubuntu.sh --install
./scripts/setup-models.sh
uv run --locked transcriber doctor --test-speech-runtime
uv run --locked transcriber gui
```

Modele pobiera się jawnie. `--public-only` pomija chroniony diarizer i nie przygotowuje całego lokalnego procesu z wieloma mówcami. Brak HF_TOKEN nie przeszkadza przy kompletnych modelach offline. Zwykła transkrypcja nie pobiera brakujących modeli po cichu. API chmurowe nadal wymaga internetu i własnych zgód.

Zwykła aktualizacja repozytorium po zapisie pracy i zatrzymaniu serwera:

```text
git pull --ff-only
uv sync --locked
uv run --locked transcriber gui
```

Nie instaluj wszystkiego i nie pobieraj modeli po każdej aktualizacji. [Naprawy Windows](windows-native.md) lub [naprawy po aktualizacji Ubuntu](ubuntu-upgrade.md) używaj po odpowiednim błędzie diagnostyki. GUI podaje lokalny adres, zwykle `http://127.0.0.1:8765/`. Dostępne są `gui --no-open-browser` i `gui --port 8766`. Zamknięcie przeglądarki nie zatrzymuje przetwarzania. Przed przenoszeniem lub usuwaniem projektu przeczytaj [zapis pracy](saved-work.md), [pliki i eksporty](outputs.md) oraz [rozwiązywanie problemów](troubleshooting.md).
