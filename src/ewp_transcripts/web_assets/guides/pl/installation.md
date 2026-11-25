# Instalacja i aktualizacja

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

## Wybierz sposób instalacji

1. W Windows uruchom kreator `EwP-Setup-0.24.1.exe` i wykonaj opisane niżej kroki.
2. Do instalacji terminalowej pobierz ZIP Windows albo tar.gz/ZIP Ubuntu i użyj krótkich poleceń poniżej. Nie trzeba ręcznie klonować repozytorium ani wcześniej instalować Python i uv.
3. Jeśli pracujesz z repozytorium jako programista lub dotychczasowy użytkownik, zachowaj ten sposób i korzystaj z sekcji aktualizacji checkoutu. To nie jest instalacja zarządzana.

Instalacja zarządzana pojawiła się w0.22.0;0.24.1 poprawia kreator graficzny. Paczki testowe są dostępne w przekazanej paczce oraz w zadaniu Actions „Installer build and Windows startup” repozytorium. Publiczne skrypty pobierania zaczną działać po publikacji pasującego wydania. Nie zgaduj adresu pobierania. Obecny EXE jest niepodpisany; nie dostarczono certyfikatu podpisywania kodu.

Obecne cele to Windows 11 x64 oraz Ubuntu 24.04/26.04, w tym WSL2. Wcześniejsze testy programu w Windows/WSL pozostają zaakceptowane. Nowy cykl instalacji zarządzanej ma rzeczywiste testy na VM Ubuntu; pełny test instalacji i usuwania na Windows 11 jest osobny od kompilacji lub uruchomienia okien na runnerze CI. Testowe GPU to RTX 3090 24 GB. Oczekiwanie działania na innych NVIDIA z co najmniej 8 GB VRAM nadal nie jest gwarancją.

## Kreator Windows

Uruchom `EwP-Setup-0.24.1.exe` na zwykłym koncie użytkownika. Paczka zawiera program,
środowisko graficzne i wyśrodkowane logo EwP w ramce; nie zawiera wielogigabajtowych modeli.

1. **Działanie i język.** Wybierz English/Polski oraz jedno działanie: Zainstaluj, Aktualizuj,
   Napraw, Doinstaluj modele lokalne, Przywróć poprzednią wersję albo Odinstaluj. Następny ekran
   zależy od tego wyboru.
2. **Lokalizacja i test.** Przy instalacji wybierz **Folder instalacji programu**, osobny od
   nagrań i starego repozytorium. Ilość miejsca na tym dysku jest sprawdzana automatycznie;
   Dalej nie działa poniżej **25 GB** (20 GB instalacji plus5 GB wolnego marginesu). Uruchom
   **Sprawdź komputer**: zobaczysz model CPU, system, miejsce, GPU ze sterownikiem i Visual C++.
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
Expand-Archive .\EwP-0.24.1-windows-x64.zip -DestinationPath .\EwPSetup
powershell -ExecutionPolicy Bypass -File .\EwPSetup\control\Install-EwP.ps1 -Bundle .\EwP-0.24.1-windows-x64.zip
```

Po zaakceptowaniu warunków modelu dodaj `-Local -AcceptModelTerms`, aby przygotować modele lokalne. Monit tokenu jest ukryty; pusta odpowiedź pozwala użyć kompletnych modeli. `-SaveOpenRouterKey` włącza osobny ukryty monit i jawny zapis OR w systemie. `-Root 'D:\Apps\EwP'` wybiera własny pusty katalog. Obejście polityki PowerShell dotyczy tylko tego uruchomienia. Ścieżki ze spacjami obejmuj cudzysłowami.

Ubuntu 24.04/26.04, w katalogu pobranego tar.gz:

```bash
mkdir -p EwPSetup
tar -xzf EwP-0.24.1-ubuntu-x64.tar.gz -C EwPSetup
bash EwPSetup/control/Install-EwP.sh install --bundle "$PWD/EwPSetup/bundle.zip"
```

Dodaj `--local --accept-model-terms` dla modeli, `--save-openrouter-key` dla ukrytego monitu OR lub `--root "$HOME/Apps/EwP"` dla innej lokalizacji. Brakujące pakiety Ubuntu można zainstalować po jawnym monicie sudo. Nie instaluj sterownika ekranu Linuksa wewnątrz WSL; CUDA udostępnia sterownik Windows. Zgodność z fizycznym Ubuntu trzeba potwierdzić wykonaniem, a nie wnioskować tylko z WSL.

Plik SHA256SUMS służy do sprawdzenia pobranych plików. Skrypty online `Install-EwP-0.24.1.ps1` i `.sh` są generowane z dokładnymi hashami paczek pasującego wydania; nie pobiorą nieopublikowanego wydania. Skrypty i GUI używają wspólnego mechanizmu, blokady zależności i zasad modeli.

## Aktualizacja zarządzana i poprzednia wersja

Zapisz pracę i kopię, zakończ zadania lub bezpiecznie je anuluj i zatrzymaj serwer. Samo zamknięcie karty nie wystarcza. Zarządzany launcher trzyma blokadę aktywności; aktualizacja i usuwanie odmawiają działania, gdy ta aplikacja pracuje. Zweryfikowaną blokadę martwego procesu można odzyskać po przerwaniu; żywy lub nieznany właściciel pozostaje chroniony.

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
