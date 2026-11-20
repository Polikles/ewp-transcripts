"use strict";
// UI copy only. Never translate transcript/provider payloads, paths, model IDs or form values.
let guiLocale = "en";
const guiPolish = new Map([
  ["Transcribe", "Transkrypcja"], ["Optional correction", "Opcjonalna korekta"],
  ["Source review & export", "Weryfikacja i eksport źródła"], ["Optional translation", "Opcjonalne tłumaczenie"],
  ["Translation review & export", "Weryfikacja i eksport tłumaczenia"], ["Dictionaries", "Słowniki"],
  ["Saved work & cleanup", "Zapisana praca i porządkowanie"], ["Settings & About", "Ustawienia i informacje"],
  ["Interface language", "Język interfejsu"], ["Appearance", "Wygląd"],
  ["System", "Systemowy"], ["Light", "Jasny"], ["Dark", "Ciemny"], ["English", "Angielski"], ["Polish", "Polski"],
  ["Inspect and plan", "Inspekcja i plan"], ["How to use this page", "Jak korzystać z tej strony"],
  ["Server-side input path", "Ścieżka wejściowa na serwerze"], ["Shared output directory", "Wspólny katalog wyników"],
  ["Inspect", "Sprawdź plik"], ["Dry-run", "Plan bez przetwarzania"], ["Clear", "Wyczyść"],
  ["Add to queue", "Dodaj do kolejki"], ["Start queue", "Uruchom kolejkę"],
  ["Transcription queue", "Kolejka transkrypcji"], ["Language", "Język przetwarzania"],
  ["Number of speakers", "Liczba mówców"], ["Auto-detect", "Wykryj automatycznie"],
  ["Detect speaker count automatically", "Automatycznie wykryj liczbę mówców"],
  ["Choose audio files…", "Wybierz pliki audio…"], ["Choose output folder…", "Wybierz katalog wyników…"],
  ["Test local dependencies", "Test lokalnych zależności"],
  ["Dependency technical details (JSON)", "Szczegóły techniczne zależności (JSON)"],
  ["Failure technical details (JSON)", "Szczegóły techniczne błędu (JSON)"],
  ["Selected for inspection", "Wybrano do sprawdzenia"], ["Select episode", "Wybierz odcinek"],
  ["Transcription failed. Use Test local dependencies, then retry after fixing failed checks.", "Transkrypcja nie powiodła się. Uruchom test lokalnych zależności, usuń wykryte problemy i spróbuj ponownie."],
  ["Testing local dependencies… This can take a minute. No models are downloaded.", "Testowanie lokalnych zależności… Może to potrwać minutę. Modele nie są pobierane."],
  ["Local dependency checks found a problem. Fix failed checks before retrying transcription.", "Test lokalnych zależności wykrył problem. Usuń przyczyny błędów przed ponowną transkrypcją."],
  ["Local dependency checks passed. This checks library loading, CUDA visibility and local model paths; it does not run transcription.", "Test lokalnych zależności zakończony pomyślnie. Sprawdzono ładowanie bibliotek, dostępność CUDA i ścieżki modeli; transkrypcja nie została uruchomiona."],
  ["Use for inspect / plan", "Wybierz do inspekcji i planu"], ["Remove from list", "Usuń z listy"],
  ["Local dependencies", "Lokalne zależności"], ["Run doctor", "Uruchom doctor"],
  ["Quick steps", "Krótkie instrukcje"], ["Full instructions (English)", "Pełne instrukcje (angielski)"],
  ["Stage instructions", "Instrukcje etapu"], ["Add speaker", "Dodaj mówcę"],
  ["Recording queue", "Kolejka nagrań"], ["Add audio files…", "Dodaj pliki audio…"],
  ["Tools and settings", "Narzędzia i ustawienia"], ["Task context", "Kontekst zadania"],
  ["Recording details", "Szczegóły nagrania"], ["Recording language", "Język nagrania"],
  ["Translation target", "Język docelowy tłumaczenia"], ["Audio processing", "Przetwarzanie audio"],
  ["Local · WhisperX", "Lokalnie · WhisperX"],
  ["Speaker names and colors", "Nazwy i kolory mówców"],
  ["The selected profile previews the colors used for the next YTT export. Switching profiles preserves custom colors. Existing exports stay unchanged.", "Wybrany profil pokazuje kolory następnego eksportu YTT. Zmiana profilu zachowuje własne kolory. Istniejące eksporty pozostają bez zmian."],
  ["Ubuntu upgrade and dependency repair instructions", "Instrukcje aktualizacji Ubuntu i naprawy zależności"],
  ["Open Ubuntu upgrade instructions", "Otwórz instrukcje aktualizacji Ubuntu"],
  ["Place the cursor between complete words, then split. Select text to use Separate selected text instead.", "Ustaw kursor między całymi słowami i podziel tekst. Dla zaznaczenia użyj wydzielania zaznaczonego tekstu."],
  ["Transcription failed. Open Settings & About and use Test local dependencies, then retry after fixing failed checks.", "Transkrypcja nie powiodła się. Otwórz Ustawienia i informacje i użyj testu lokalnych zależności, a po usunięciu przyczyn błędów spróbuj ponownie."],
  ["Reinstall dependencies…", "Zainstaluj ponownie zależności…"],
  ["Test the environment to enable Doctor and dependency repair. These tools are optional maintenance actions.", "Przetestuj środowisko, aby włączyć doctor i naprawę zależności. Są to opcjonalne narzędzia konserwacji."],
  ["Repair dependencies in the terminal", "Napraw zależności w terminalu"],
  ["Save your work and stop the GUI with Ctrl+C. In the transcription checkout, run:", "Zapisz pracę i zatrzymaj GUI klawiszami Ctrl+C. W katalogu projektu transkrypcji uruchom:"],
  ["This restores locked TorchCodec and pyannote packages. If compatible FFmpeg libraries are missing, it downloads and builds private FFmpeg 7 audio libraries. Internet access and build tools are needed; missing tools are listed with their install command. System FFmpeg and model caches are preserved.", "Przywraca to przypięte wersje TorchCodec i pyannote. Jeśli brakuje zgodnych bibliotek FFmpeg, pobiera i kompiluje prywatne biblioteki audio FFmpeg 7. Wymaga internetu i narzędzi kompilacji; brakujące narzędzia są wskazywane z poleceniem instalacji. Zachowuje systemowy FFmpeg i pamięć podręczną modeli."],
  ["Restart the GUI and rerun Test local dependencies before retrying the queue.", "Uruchom ponownie GUI i test lokalnych zależności przed ponownym uruchomieniem kolejki."],
  ["Running doctor…", "Uruchamianie doctor…"], ["Doctor report (JSON)", "Raport doctor (JSON)"],
  ["Doctor finished. Native speech loading is reported separately by Test local dependencies.", "Doctor zakończył pracę. Ładowanie natywnych bibliotek mowy sprawdza osobno test lokalnych zależności."],
  ["I reviewed the plan and want to add jobs to the queue.", "Sprawdziłem plan i chcę dodać zadania do kolejki."],
  ["Audio copied locally. Inspect and dry-run each file, confirm staging, then start the queue. Copies become durable only when staged.", "Audio skopiowano lokalnie. Sprawdź i zaplanuj każdy plik, potwierdź dodanie, potem uruchom kolejkę. Kopie są trwałe dopiero po dodaniu do kolejki."],
  ["Remove", "Usuń"], ["Status", "Stan"], ["Job and settings", "Zadanie i ustawienia"], ["Input", "Wejście"],
  ["Planned/actual result", "Planowany / zapisany wynik"], ["Action", "Działanie"],
  ["Remove selected queue items", "Usuń wybrane pozycje kolejki"], ["Completion:", "Ukończenie:"],
  ["Legend:", "Legenda:"], ["not started", "nierozpoczęte"], ["completed", "ukończone"], ["error", "błąd"], ["skipped", "pominięte"],
  ["COMPLETED", "UKOŃCZONE"], ["STAGED", "PRZYGOTOWANE"], ["RUNNING", "W TOKU"], ["FAILED", "BŁĄD"], ["QUEUED", "W KOLEJCE"],
  ["Correction", "Korekta"], ["Review", "Weryfikacja"], ["Original export", "Eksport źródła"],
  ["LLM translation", "Tłumaczenie LLM"], ["Translation", "Tłumaczenie"], ["Translated export", "Eksport tłumaczenia"],
  ["Correction queue", "Kolejka korekty"], ["Review and verified export queue", "Kolejka weryfikacji i eksportu źródła"],
  ["Translation queue", "Kolejka tłumaczenia"], ["Semantic review and translated export queue", "Kolejka weryfikacji i eksportu tłumaczenia"],
  ["Add saved results…", "Dodaj zapisane wyniki…"], ["Select all actionable items", "Wybierz wszystkie dostępne pozycje"],
  ["Clear selected actionable items", "Odznacz dostępne pozycje"], ["Reopen correction", "Otwórz korektę"],
  ["Reopen review / export", "Otwórz weryfikację / eksport"], ["Reopen translation", "Otwórz tłumaczenie"],
  ["Reopen semantic review", "Otwórz weryfikację tłumaczenia"],
  ["Skip LLM-assisted correction", "Pomiń korektę LLM"], ["Skip LLM-assisted translation", "Pomiń tłumaczenie LLM"],
  ["LLM-assisted transcript correction", "Korekta transkrypcji z pomocą LLM"], ["LLM-assisted translation", "Tłumaczenie z pomocą LLM"],
  ["Review and export", "Weryfikacja i eksport"], ["Semantic translation review", "Weryfikacja znaczenia tłumaczenia"],
  ["Canonical result JSON", "Kanoniczny wynik JSON"], ["Correction output root", "Katalog roboczy korekty"],
  ["Source transcript revision (optional)", "Wersja źródłowej transkrypcji (opcjonalna)"],
  ["Review output root", "Katalog roboczy weryfikacji"], ["Translation output root", "Katalog roboczy tłumaczenia"],
  ["Target language", "Język docelowy"], ["Provider settings", "Ustawienia dostawcy"], ["Provider", "Dostawca"],
  ["Exact LM Studio model ID", "Dokładny identyfikator modelu LM Studio"], ["Exact model ID", "Dokładny identyfikator modelu"],
  ["LM Studio API endpoint", "Adres API LM Studio"], ["Provider response mode", "Tryb odpowiedzi dostawcy"],
  ["Plain text (Bielik-compatible)", "Zwykły tekst (zgodny z Bielikiem)"], ["JSON schema", "Schemat JSON"],
  ["JSON text compatibility", "Zgodność tekstowa JSON"], ["Enter ID manually", "Wpisz identyfikator ręcznie"],
  ["Allow a non-loopback LM Studio endpoint.", "Zezwól na adres LM Studio poza interfejsem lokalnym."],
  ["Set an OpenRouter API key", "Ustaw klucz API OpenRouter"], ["Check connection", "Sprawdź połączenie"],
  ["Check models and pricing", "Sprawdź modele i ceny"], ["Not checked", "Nie sprawdzono"], ["API OK", "API działa"],
  ["Project correction dictionary (optional)", "Projektowy słownik korekty (opcjonalny)"],
  ["Project translation dictionary (optional)", "Projektowy słownik tłumaczenia (opcjonalny)"],
  ["Dictionary catalog directory", "Katalog słowników"], ["Refresh dictionary list", "Odśwież listę słowników"],
  ["None / use direct path below", "Brak / użyj ścieżki poniżej"], ["Available correction dictionaries", "Dostępne słowniki korekty"],
  ["Available translation dictionaries", "Dostępne słowniki tłumaczenia"],
  ["Generate correction candidate", "Utwórz propozycję korekty"], ["Generate translation candidate", "Utwórz propozycję tłumaczenia"],
  ["Open candidate in manual review", "Otwórz propozycję do weryfikacji"], ["Open candidate in semantic review", "Otwórz propozycję do weryfikacji znaczenia"],
  ["Correction status", "Stan korekty"], ["Translation status", "Stan tłumaczenia"], ["Review status", "Stan weryfikacji"],
  ["Semantic review status", "Stan weryfikacji tłumaczenia"], ["Technical details (JSON)", "Szczegóły techniczne (JSON)"],
  ["Prepare review", "Przygotuj weryfikację"], ["Restore saved review", "Przywróć zapisaną weryfikację"],
  ["Save draft", "Zapisz szkic"], ["Preview", "Sprawdź zmiany"], ["Clear current review", "Wyczyść bieżącą weryfikację"],
  ["Prepare and validate", "Przygotowanie i sprawdzenie"], ["Draft and history", "Szkic i historia"],
  ["Undo", "Cofnij"], ["Redo", "Ponów"], ["Review identity:", "ID weryfikacji:"],
  ["Speaker names for this revision", "Nazwy mówców w tej wersji"], ["Add revision-only speaker", "Dodaj mówcę w tej wersji"],
  ["Speaker", "Mówca"], ["Transcript text", "Tekst transkrypcji"], ["Display", "Widok"],
  ["One section at a time", "Jedna sekcja"], ["All sections", "Wszystkie sekcje"],
  ["Previous section", "Poprzednia sekcja"], ["Next section", "Następna sekcja"],
  ["Separate selected text", "Wydziel zaznaczony tekst"], ["Split at cursor", "Podziel w miejscu kursora"],
  ["Merge entire block with previous", "Połącz cały blok z poprzednim"],
  ["I manually verified wording, speakers, punctuation, quotations, and sentence boundaries.", "Ręcznie sprawdziłem treść, mówców, interpunkcję, cytaty i granice zdań."],
  ["Apply verified revision", "Zatwierdź zweryfikowaną wersję"], ["Verified export formats", "Formaty eksportu źródła"],
  ["Export verified revision", "Eksportuj zweryfikowaną wersję"], ["Proceed to translation", "Przejdź do tłumaczenia"],
  ["Source", "Źródło"], ["Target translation", "Tekst tłumaczenia"],
  ["Save translation draft", "Zapisz szkic tłumaczenia"], ["Restore saved draft", "Przywróć zapisany szkic"],
  ["Preview translation", "Sprawdź tłumaczenie"], ["Clear current translation review", "Wyczyść bieżącą weryfikację tłumaczenia"],
  ["Apply verified translation", "Zatwierdź zweryfikowane tłumaczenie"], ["Translated export formats", "Formaty eksportu tłumaczenia"],
  ["Audit and export verified translation", "Sprawdź pochodzenie i eksportuj tłumaczenie"], ["Proceed with next output", "Przejdź do kolejnego wyniku"],
  ["Allow empty translation units (intentional omissions will be recorded and excluded from exports).", "Zezwól na puste jednostki tłumaczenia (celowe pominięcia zostaną zapisane i wyłączone z eksportu)."],
  ["I manually verified meaning, omissions, additions, uncertainty, names, project conventions, register, and style.", "Ręcznie sprawdziłem znaczenie, pominięcia, dodatki, niepewność, nazwy, konwencje projektu, rejestr i styl."],
  ["Project correction dictionary", "Projektowy słownik korekty"], ["Canonical results directory", "Katalog wyników kanonicznych"],
  ["Manual revisions directory", "Katalog wersji zweryfikowanych"], ["Dictionary work output root", "Katalog roboczy słownika"],
  ["Project ID", "Identyfikator projektu"], ["Minimum occurrences", "Minimalna liczba wystąpień"],
  ["Previous project dictionary (optional)", "Poprzedni słownik projektu (opcjonalny)"], ["Generate proposal", "Utwórz propozycję"],
  ["Save decisions", "Zapisz decyzje"], ["New dictionary ID", "Nowy identyfikator słownika"], ["Publish project dictionary", "Opublikuj słownik projektu"],
  ["I reviewed every candidate and want to publish this versioned project dictionary.", "Sprawdziłem wszystkie propozycje i chcę opublikować tę wersję słownika projektu."],
  ["pending", "oczekujące"], ["approved", "zaakceptowane"], ["rejected", "odrzucone"],
  ["Saved work state", "Zapisany stan pracy"], ["Workspace name", "Nazwa obszaru pracy"], ["Saved workspaces", "Zapisane obszary pracy"],
  ["Workspace storage directory (optional)", "Katalog zapisów pracy (opcjonalny)"], ["Save as a new workspace", "Zapisz jako nowy obszar pracy"],
  ["Save current work state", "Zapisz bieżący stan pracy"], ["Load selected work state", "Wczytaj wybrany stan pracy"],
  ["Refresh list", "Odśwież listę"], ["Remove selected work state", "Usuń wybrany zapis pracy"], ["Import work state file…", "Importuj plik zapisu pracy…"],
  ["Clear current work state", "Wyczyść bieżący stan pracy"], ["Managed source inventory", "Inwentarz zarządzanych źródeł"],
  ["Refresh inventory", "Odśwież inwentarz"], ["Delete selected unreferenced copies", "Usuń wybrane nieużywane kopie"],
  ["About", "Informacje"], ["License and warranty", "Licencja i gwarancja"], ["Source code", "Kod źródłowy"], ["Report an issue", "Zgłoś problem"],
  ["Clear EWP browser state", "Wyczyść stan EwP w przeglądarce"], ["Open the complete local GUI instructions", "Otwórz pełną lokalną instrukcję GUI"],
  ["YTT color profile", "Profil kolorów YTT"], ["Configured production palette", "Skonfigurowana paleta produkcyjna"],
  ["Brand preview palette", "Nowa paleta marki (podgląd)"], ["Adopt brand palette for this recording", "Zastosuj paletę marki dla tego nagrania"],
  ["Use configured production palette", "Użyj skonfigurowanej palety produkcyjnej"],
  ["Existing custom colors are retained. Brand colors require a new YouTube check; existing exports are never recolored.", "Zachowujemy własne kolory. Nowa paleta wymaga testu w YouTube; istniejące eksporty nigdy nie są przemalowywane."],
  ["No active recording", "Brak aktywnego nagrania"], ["No recordings yet. Import audio or saved results.", "Brak nagrań. Dodaj audio lub zapisane wyniki."],
  ["Working…", "Praca w toku…"], ["Done!", "Gotowe!"], ["Error", "Błąd"],
  ["Status: local service ready", "Stan: usługa lokalna gotowa"], ["Status: connecting", "Stan: łączenie"],
  ["No jobs in this server session.", "Brak zadań w tej sesji serwera."], ["No review is open.", "Nie otwarto weryfikacji."],
  ["No translation review is open.", "Nie otwarto weryfikacji tłumaczenia."], ["No correction is running.", "Korekta nie jest uruchomiona."],
  ["No translation is running.", "Tłumaczenie nie jest uruchomione."], ["No workspace state loaded.", "Nie wczytano stanu pracy."],
  ["Preview passed; no revision was written", "Sprawdzenie zakończone; nie zapisano wersji"],
  ["Verified immutable revision applied", "Zapisano zweryfikowaną niezmienną wersję"], ["Verified exports completed", "Eksport zweryfikowanych plików zakończony"],
  ["Draft saved; preview is required again", "Szkic zapisany; sprawdź zmiany ponownie"],
  ["Source export never requires translation or dictionaries.", "Eksport źródła nie wymaga tłumaczenia ani słowników."],
  ["Local-first audio transcription. LLM correction and translation are optional. Source export never requires translation or dictionaries.", "Transkrypcja audio działa lokalnie. Korekta i tłumaczenie LLM są opcjonalne. Eksport źródła nie wymaga tłumaczenia ani słowników."],
  ["Provider readiness and disclosure consent remain in each optional stage. Local API endpoints are separately operated; the application cannot guarantee third-party logging, retention, forwarding or storage location.", "Gotowość dostawcy i zgoda na przekazanie danych są sprawdzane w każdym opcjonalnym etapie. Lokalne API działają niezależnie; aplikacja nie gwarantuje zasad logowania, przechowywania, przekazywania ani lokalizacji danych usług zewnętrznych."],
  ["Audio is processed locally. Correction and translation send transcript text only after explicit scoped consent. Keys stay in server memory and are never saved in workspaces.", "Audio jest przetwarzane lokalnie. Korekta i tłumaczenie wysyłają tekst dopiero po wyraźnej zgodzie na wskazany zakres. Klucze pozostają w pamięci serwera i nie są zapisywane w obszarach pracy."],
  ["Asset credits and notices", "Autorzy zasobów i informacje prawne"], ["Identity asset terms", "Warunki używania identyfikacji wizualnej"],
]);
for (const [en, pl] of [
  [
    "Local-first podcast workflow",
    "Lokalny proces pracy z podcastem"
  ],
  [
    "Draft changes saved or no draft open",
    "Zmiany zapisane lub brak otwartego szkicu"
  ],
  [
    "Unsaved draft — navigation keeps it open",
    "Niezapisany szkic — nawigacja zachowuje jego treść"
  ],
  [
    "Choose a recording in a stage queue.",
    "Wybierz nagranie w kolejce etapu."
  ],
  [
    "Source and output paths",
    "Ścieżki źródła i wyników"
  ],
  [
    "Save or restore non-secret workflow fields and durable queue sources across browsers and program restarts. Saving current work state first saves dirty review drafts in the chosen output folder; the workspace JSON does not embed transcript text, API keys, or confirmations.",
    "Zapisz lub przywróć niesekretne ustawienia i trwałe źródła kolejki po zmianie przeglądarki lub ponownym uruchomieniu programu. Zapis najpierw utrwala zmienione szkice w wybranym katalogu. JSON obszaru pracy nie zawiera tekstu transkrypcji, kluczy API ani potwierdzeń."
  ],
  [
    "Enter a user-space directory to keep workspace JSON files with your backups. Leave blank for the private default location.",
    "Wpisz katalog użytkownika dla plików JSON obszaru pracy i kopii zapasowych. Puste pole oznacza domyślny prywatny katalog."
  ],
  [
    "Automatically replace the active saved workspace every 60 seconds when its non-secret fields or queue change.",
    "Automatycznie zastępuj aktywny zapis pracy co 60 sekund, gdy zmienią się niesekretne pola lub kolejka."
  ],
  [
    "Auto-save is off by default and becomes available after an explicit workspace save or load. Enabling it updates the saved recovery point when queue items are added or removed.",
    "Autozapis jest domyślnie wyłączony i dostępny po zapisaniu lub wczytaniu pracy. Po włączeniu dodanie lub usunięcie pozycji kolejki aktualizuje zapisany punkt odzyskiwania."
  ],
  [
    "Open saved work state file…",
    "Otwórz plik zapisanego stanu pracy…"
  ],
  [
    "Managed source copies",
    "Zarządzane kopie źródeł"
  ],
  [
    "Inventory durable browser-selected copies under the shared output directory. Cleanup audits the current queue, the default workspace catalog, the selected custom workspace catalog, and workflow lineage in this output directory. Workspace catalogs stored elsewhere are unknown and must be checked separately.",
    "Sprawdź trwałe kopie wybrane w przeglądarce we wspólnym katalogu wyników. Porządkowanie uwzględnia bieżącą kolejkę, domyślny i wybrany katalog obszarów pracy oraz pochodzenie plików. Katalogi obszarów pracy w innych miejscach należy sprawdzić oddzielnie."
  ],
  [
    "Refresh source inventory",
    "Odśwież inwentarz źródeł"
  ],
  [
    "Inventory has not been loaded.",
    "Inwentarz nie został wczytany."
  ],
  [
    "Enter one user-space input file and a shared output directory.",
    "Wybierz jeden plik użytkownika i wspólny katalog wyników."
  ],
  [
    "Inspect it, then run and review dry-run.",
    "Sprawdź plik, następnie uruchom i przejrzyj plan bez przetwarzania."
  ],
  [
    "Confirm the exact plan and add the file to the staged queue.",
    "Potwierdź konkretny plan i dodaj plik do kolejki oczekującej."
  ],
  [
    "Repeat with files from any accessible user location, keeping the same output directory.",
    "Powtórz dla plików z dostępnych lokalizacji użytkownika, zachowując ten sam katalog wyników."
  ],
  [
    "Review the table, remove mistakes, then start the queue.",
    "Sprawdź tabelę, usuń błędne pozycje, następnie uruchom kolejkę."
  ],
  [
    "Read media metadata and plan outputs without loading transcription models or writing artifacts.",
    "Sprawdź metadane i zaplanuj wyniki bez ładowania modeli i zapisywania artefaktów."
  ],
  [
    "Windows drive and WSL paths are accepted from accessible user space. Symlinks and operating-system directories are blocked.",
    "Obsługiwane są dostępne ścieżki użytkownika w Windows i WSL. Dowiązania symboliczne i katalogi systemowe są blokowane."
  ],
  [
    "Browse output folder…",
    "Wybierz katalog wyników…"
  ],
  [
    "Choose 1–6 speakers when known. Speaker attribution usually becomes less accurate as the number of speakers increases.",
    "Wybierz 1–6 mówców, jeśli znasz ich liczbę. Większa liczba mówców zwykle utrudnia poprawne przypisanie. Podczas weryfikacji można dodać kolejnych mówców."
  ],
  [
    "On narrow windows, scroll the queue horizontally to reach all columns and actions. Keyboard: focus the queue, then use the arrow keys.",
    "W wąskim oknie przewijaj kolejkę poziomo, aby dotrzeć do wszystkich kolumn i działań. Klawiatura: ustaw fokus na kolejce i użyj strzałek."
  ],
  [
    "This optional operation sends transcript text to the selected API and writes a non-final correction candidate. Audio is never sent. Manual review remains required.",
    "Ta opcjonalna operacja wysyła tekst transkrypcji do wybranego API i zapisuje wstępną korektę. Audio nie jest wysyłane. Weryfikacja przez człowieka pozostaje konieczna."
  ],
  [
    "Choose one canonical result to reopen its optional correction stage. Selection lasts only for this page and does not start provider work.",
    "Wybierz wynik kanoniczny, aby otworzyć opcjonalną korektę. Zaznaczenie obowiązuje na tej stronie i nie uruchamia dostawcy."
  ],
  [
    "Candidates and private resumable state are kept in separate directories below this root.",
    "Propozycje i prywatny stan wznowienia są przechowywane w oddzielnych podkatalogach."
  ],
  [
    "OpenRouter (cloud)",
    "OpenRouter (chmura)"
  ],
  [
    "Model",
    "Model"
  ],
  [
    "Exact OpenRouter model ID",
    "Dokładny identyfikator modelu OpenRouter"
  ],
  [
    "OpenRouter API endpoint",
    "Adres API OpenRouter"
  ],
  [
    "LM Studio (local)",
    "LM Studio (lokalny)"
  ],
  [
    "No API key is configured for this active GUI server process.",
    "W aktywnym procesie serwera GUI nie ustawiono klucza API."
  ],
  [
    "Dictionary list not loaded.",
    "Nie wczytano listy słowników."
  ],
  [
    "Project ID, version, and hash are read from the dictionary and recorded automatically.",
    "Identyfikator projektu, wersja i skrót słownika są odczytywane i zapisywane automatycznie."
  ],
  [
    "I understand that using this API is not a local operation: transcript text leaves this application, and EWP Transcriber cannot control how the provider logs, retains, uses, or forwards it. The result is still a non-final candidate requiring manual review.",
    "Rozumiem, że użycie tego API nie jest operacją lokalną: tekst opuszcza aplikację, która nie kontroluje jego logowania, przechowywania, wykorzystania ani przekazywania przez dostawcę. Wynik pozostaje propozycją wymagającą ręcznej weryfikacji."
  ],
  [
    "Canonical ASR text is unverified. Prepare an editable draft, save and preview it, then explicitly apply one immutable verified revision before exporting publication files.",
    "Kanoniczny tekst ASR jest niezweryfikowany. Przygotuj szkic, zapisz go i sprawdź zmiany, następnie jawnie zatwierdź niezmienną wersję przed eksportem do publikacji."
  ],
  [
    "Open one recording's saved review or prepare its own editable review. This never changes another recording's draft.",
    "Otwórz zapisaną weryfikację nagrania lub przygotuj jego szkic. Nie zmienia to szkicu innego nagrania."
  ],
  [
    "By default, reviews, revisions, and exports are kept in separate directories below this root. A persistent root can restore its last GUI review in another browser or later program run.",
    "Szkice, zatwierdzone wersje i eksporty są domyślnie w oddzielnych podkatalogach. Trwały katalog umożliwia przywrócenie weryfikacji w innej przeglądarce lub sesji programu."
  ],
  [
    "Set review, revision, and export directories manually.",
    "Ustaw katalogi szkiców, wersji i eksportów ręcznie."
  ],
  [
    "Editable review directory",
    "Katalog edytowalnych szkiców"
  ],
  [
    "Verified revision directory",
    "Katalog zatwierdzonych wersji"
  ],
  [
    "Export directory",
    "Katalog eksportu"
  ],
  [
    "These labels are stored in the review and immutable revision only. Canonical speaker IDs and the original ASR result remain unchanged.",
    "Nazwy zapisujemy tylko w szkicu i jego niezmiennej wersji. Kanoniczne identyfikatory mówców i oryginalny wynik ASR pozostają bez zmian."
  ],
  [
    "Generate a non-final LM Studio translation candidate from an explicitly identified raw, automated, or manually verified transcript source.",
    "Utwórz nieostateczną propozycję tłumaczenia z jawnie wskazanego źródła: surowego, automatycznego lub ręcznie zweryfikowanego."
  ],
  [
    "Choose one verified source to reopen its optional translation stage. Selection lasts only for this page and does not start provider work.",
    "Wybierz źródło, aby otworzyć opcjonalne tłumaczenie. Zaznaczenie obowiązuje na tej stronie i nie uruchamia dostawcy."
  ],
  [
    "Open manual translation",
    "Otwórz tłumaczenie ręczne"
  ],
  [
    "Choose a recording first.",
    "Najpierw wybierz nagranie."
  ],
  [
    "Choose a recording whose source language matches this direction.",
    "Wybierz nagranie, którego język źródłowy odpowiada temu kierunkowi."
  ],
  [
    "Leaving this blank translates raw ASR and records that unverified source with a warning.",
    "Puste pole oznacza tłumaczenie surowego ASR; niezweryfikowane źródło zostanie oznaczone ostrzeżeniem."
  ],
  [
    "OpenRouter is a cloud API. Use the session-only key control; the key is never written to a project, workspace, browser storage, or translation artifact.",
    "OpenRouter jest API w chmurze. Klucz ustawiony na czas sesji nigdy nie jest zapisywany w projekcie, obszarze pracy, pamięci przeglądarki ani pliku tłumaczenia."
  ],
  [
    "Project identity and hash are read from the dictionary automatically.",
    "Tożsamość i skrót słownika są odczytywane automatycznie."
  ],
  [
    "I understand that OpenRouter is a separately operated cloud API: transcript text leaves this application, and EWP Transcriber cannot control how the provider logs, retains, uses, or forwards it. The translation remains non-final and requires semantic manual review.",
    "Rozumiem, że OpenRouter to niezależne API w chmurze: tekst opuszcza aplikację, która nie kontroluje jego logowania, przechowywania, wykorzystania ani przekazywania przez dostawcę. Tłumaczenie pozostaje propozycją wymagającą ręcznej weryfikacji znaczenia."
  ],
  [
    "Five units at a time",
    "Pięć jednostek naraz"
  ],
  [
    "All units",
    "Wszystkie jednostki"
  ],
  [
    "Previous units",
    "Poprzednie jednostki"
  ],
  [
    "Next units",
    "Następne jednostki"
  ],
  [
    "Compare every immutable source unit with its editable target. Save, preview, and explicitly verify meaning before applying a final manual child.",
    "Porównaj każdą niezmienną jednostkę źródła z edytowalnym tłumaczeniem. Zapisz, sprawdź i jawnie potwierdź znaczenie przed zatwierdzeniem wersji ręcznej."
  ],
  [
    "Reopen a non-final translation candidate in its own semantic review. Final publication still requires preview and manual verification.",
    "Otwórz propozycję tłumaczenia w jej własnej weryfikacji znaczenia. Publikacja nadal wymaga sprawdzenia i ręcznej akceptacji."
  ],
  [
    "Compare canonical results with exact manual revisions, review contextual proposal evidence, retain rejected decisions, and publish one immutable project dictionary.",
    "Porównaj wyniki kanoniczne z ich ręcznymi wersjami, sprawdź kontekst propozycji, zachowaj odrzucenia i opublikuj niezmienny słownik projektu."
  ],
  [
    "Candidate filter",
    "Filtr propozycji"
  ],
  [
    "Show all",
    "Pokaż wszystkie"
  ],
  [
    "Only pending",
    "Tylko oczekujące"
  ],
  [
    "Only rejected",
    "Tylko odrzucone"
  ],
  [
    "Hide approved",
    "Ukryj zaakceptowane"
  ],
  [
    "Occurrence display",
    "Widok wystąpień"
  ],
  [
    "List",
    "Lista"
  ],
  [
    "Previous / next",
    "Poprzednie / następne"
  ],
  [
    "Dictionary status",
    "Stan słownika"
  ],
  [
    "No dictionary proposal is open.",
    "Nie otwarto propozycji słownika."
  ],
  [
    "Artwork: Cyryl. Creator URL is an unverified placeholder (blogcyryla.pl); TODO replace when supplied.",
    "Grafika: Cyryl. Adres twórcy jest niezweryfikowanym adresem zastępczym (blogcyryla.pl); TODO: zastąpić po otrzymaniu właściwego adresu."
  ],
  [
    "not started",
    "nie rozpoczęto"
  ],
  [
    "completed",
    "ukończone"
  ],
  [
    "skipped",
    "pominięto"
  ],
  [
    "error",
    "błąd"
  ],
  [
    "Correction",
    "Korekta"
  ],
  [
    "Review",
    "Weryfikacja"
  ],
  [
    "Original export",
    "Eksport źródła"
  ],
  [
    "LLM translation",
    "Tłumaczenie LLM"
  ],
  [
    "Translation",
    "Tłumaczenie"
  ],
  [
    "Translated export",
    "Eksport tłumaczenia"
  ],
  [
    "COMPLETED",
    "UKOŃCZONE"
  ],
  [
    "STAGED",
    "OCZEKUJE NA START"
  ],
  [
    "RUNNING",
    "W TOKU"
  ],
  [
    "FAILED",
    "BŁĄD"
  ],
  [
    "QUEUED",
    "W KOLEJCE"
  ],
  [
    "Translation uses an older or raw source. A newer verified source exists. Existing outputs are retained; reopen translation to use the new revision.",
    "Tłumaczenie używa starszego lub surowego źródła. Istnieje nowsza zweryfikowana wersja. Dotychczasowe wyniki są zachowane; otwórz tłumaczenie ponownie, aby użyć nowego źródła."
  ]
]) guiPolish.set(en, pl);
for (const [en,pl] of [["Correction queue", "Kolejka korekty"], ["Review and verified export queue", "Kolejka weryfikacji i eksportu źródła"], ["Translation queue", "Kolejka tłumaczenia"], ["Semantic review and translated export queue", "Kolejka weryfikacji i eksportu tłumaczenia"], ["Select all actionable items", "Wybierz wszystkie dostępne pozycje"], ["Clear selected actionable items", "Wyczyść wybór dostępnych pozycji"], ["Add saved results…", "Dodaj zapisane wyniki…"], ["Reopen correction", "Otwórz korektę"], ["Reopen review / export", "Otwórz weryfikację / eksport"], ["Reopen translation", "Otwórz tłumaczenie"], ["Reopen semantic review", "Otwórz weryfikację tłumaczenia"], ["Skip LLM-assisted correction", "Pomiń korektę LLM"], ["Skip LLM-assisted translation", "Pomiń tłumaczenie LLM"], ["Editable review prepared", "Przygotowano edytowalny szkic"], ["Review check", "Sprawdzenie weryfikacji"], ["Result", "Wynik"], ["Publication", "Publikacja"], ["None — editable draft only", "Brak — tylko edytowalny szkic"], ["Review file", "Plik szkicu"], ["Files written", "Zapisane pliki"], ["Files skipped", "Pominięte pliki"], ["Revision", "Wersja"], ["Warnings", "Ostrzeżenia"], ["Validation", "Sprawdzenie"], ["Passed", "Poprawne"], ["Unpublished", "Nieopublikowane"], ["Save", "Zapisz"], ["Cancel", "Anuluj"], ["Set key for this server session", "Ustaw klucz na czas sesji serwera"], ["Discard", "Odrzuć"], ["Clear API key", "Usuń klucz API"], ["Local-first podcast workflow", "Lokalny proces pracy nad podcastem"]]) guiPolish.set(en,pl);
guiPolish.set('Workflow stages', 'Etapy pracy');
guiPolish.set('Recordings', 'Nagrania');
guiPolish.set('Editable review prepared', 'Przygotowano edytowalny szkic');
guiPolish.set('Review check', 'Sprawdzenie weryfikacji');
guiPolish.set('Result', 'Wynik');
guiPolish.set('Publication', 'Publikacja');
guiPolish.set('None — editable draft only', 'Brak — tylko edytowalny szkic');
guiPolish.set('None — preview only', 'Brak — tylko sprawdzenie');
guiPolish.set('Review file', 'Plik weryfikacji');
guiPolish.set('No completed canonical results are available in this GUI queue yet.', 'W tej kolejce nie ma jeszcze ukończonych wyników kanonicznych.');
guiPolish.set('API key is available to browsers connected to this active GUI server process. It is not saved in the project or workspace and is erased when the GUI stops.', 'Klucz API jest dostępny dla przeglądarek połączonych z tym procesem serwera GUI. Nie jest zapisywany w projekcie ani obszarze pracy i znika po zatrzymaniu GUI.');
const guiNodeSources = new WeakMap();
const guiAttributeSources = new WeakMap();
let guiTranslationObserver;
for (const [en, pl] of [
  [
    "Remove completed tasks from the queue",
    "Usuń ukończone zadania z kolejki"
  ],
  [
    "Added to queue",
    "Dodano do kolejki"
  ],
  [
    "Custom profile name",
    "Nazwa własnego profilu"
  ],
  [
    "Preview",
    "Podgląd"
  ],
  [
    "Apply",
    "Zastosuj"
  ],
  [
    "Save",
    "Zapisz"
  ],
  [
    "Preview a profile or edit speaker colors, then Apply for this recording. Save keeps a named profile for other recordings.",
    "Wyświetl profil lub edytuj kolory mówców, a następnie zastosuj je do nagrania. Zapisz profil, aby używać go w innych nagraniach."
  ],
  [
    "Preview only. Apply to use these colors for this recording's next export.",
    "Tylko podgląd. Zastosuj kolory, aby użyć ich przy kolejnym eksporcie tego nagrania."
  ],
  [
    "Colors applied to this recording's next export. Existing exports stay unchanged.",
    "Kolory zastosowano do kolejnego eksportu tego nagrania. Dotychczasowe eksporty pozostają bez zmian."
  ],
  [
    "Custom profile saved. Apply to use it for this recording's next export.",
    "Własny profil zapisany. Zastosuj go do kolejnego eksportu tego nagrania."
  ],
  [
    "Accept direction change",
    "Potwierdź zmianę kierunku"
  ],
  [
    "Changing direction requires a matching source-language recording. Existing translations stay unchanged. Accept this change to continue.",
    "Zmiana kierunku wymaga nagrania w pasującym języku źródłowym. Dotychczasowe tłumaczenia pozostają bez zmian. Potwierdź zmianę, aby kontynuować."
  ],
  [
    "This direction needs a recording in the other source language. Choose a matching recording before generating.",
    "Ten kierunek wymaga nagrania w drugim języku źródłowym. Wybierz pasujące nagranie przed generowaniem."
  ],
  [
    "Source and target details",
    "Szczegóły źródła i języka docelowego"
  ],
  [
    "Preview the saved draft, then confirm that you verified meaning and speaker attribution before applying an immutable translation.",
    "Wyświetl podgląd zapisanego szkicu, a następnie potwierdź sprawdzenie znaczenia i przypisania mówców przed zastosowaniem niezmiennego tłumaczenia."
  ],
  [
    "Apply the verified translation first. Audit checks its source lineage before generating the selected subtitle formats.",
    "Najpierw zastosuj zweryfikowane tłumaczenie. Audyt sprawdza zgodność ze źródłem przed wygenerowaniem wybranych formatów napisów."
  ],
  [
    "Build a proposal from reviewed recordings (optional)",
    "Utwórz propozycję ze zweryfikowanych nagrań (opcjonalnie)"
  ],
  [
    "New dictionary",
    "Nowy słownik"
  ],
  [
    "Add dictionary file…",
    "Dodaj plik słownika…"
  ],
  [
    "Show removed dictionaries",
    "Pokaż słowniki usunięte z listy"
  ],
  [
    "Dictionary",
    "Słownik"
  ],
  [
    "Compare with",
    "Porównaj z"
  ],
  [
    "Choose a dictionary",
    "Wybierz słownik"
  ],
  [
    "No comparison",
    "Bez porównania"
  ],
  [
    "View / edit",
    "Przeglądaj / edytuj"
  ],
  [
    "Compare versions",
    "Porównaj wersje"
  ],
  [
    "Dictionary kind",
    "Rodzaj słownika"
  ],
  [
    "Polish correction",
    "Korekta polska"
  ],
  [
    "Translation",
    "Tłumaczenie"
  ],
  [
    "Recording scope",
    "Zakres nagrań"
  ],
  [
    "Source language",
    "Język źródłowy"
  ],
  [
    "Target language",
    "Język docelowy"
  ],
  [
    "Add entry",
    "Dodaj wpis"
  ],
  [
    "Remove entry",
    "Usuń wpis"
  ],
  [
    "Use example",
    "Wczytaj przykład"
  ],
  [
    "Source term",
    "Termin źródłowy"
  ],
  [
    "Preferred term",
    "Preferowany termin"
  ],
  [
    "Entry decision",
    "Decyzja dla wpisu"
  ],
  [
    "Approved",
    "Zaakceptowano"
  ],
  [
    "Rejected",
    "Odrzucono"
  ],
  [
    "Full dictionary document (JSON)",
    "Pełny dokument słownika (JSON)"
  ],
  [
    "Load JSON into editor",
    "Wczytaj JSON do edytora"
  ],
  [
    "Use a new ID when editing an existing dictionary. Previous files remain available to earlier runs. Remove hides an entry from this library; it does not delete its file.",
    "Przy edycji użyj nowego ID. Pliki wcześniejszych wersji pozostają dostępne dla wcześniejszych zadań. Usunięcie z listy ukrywa wpis, zachowując jego plik."
  ],
  [
    "Choose a dictionary or create a new one.",
    "Wybierz słownik lub utwórz nowy."
  ],
  [
    "Restore to list",
    "Przywróć na listę"
  ],
  [
    "Term / field",
    "Termin / pole"
  ],
  [
    "Dictionary list updated. Published files are unchanged.",
    "Lista słowników zaktualizowana. Opublikowane pliki pozostają bez zmian."
  ],
  [
    "Dictionary loaded. Save with a new ID to create an edited version.",
    "Słownik wczytany. Zapisz z nowym ID, aby utworzyć zmienioną wersję."
  ],
  [
    "New dictionary. Enter project, version ID, scope and at least one entry.",
    "Nowy słownik. Podaj projekt, ID wersji, zakres i co najmniej jeden wpis."
  ],
  [
    "Example loaded. Replace the example project and terms before saving.",
    "Przykład wczytany. Przed zapisem zastąp przykładowy projekt i terminy."
  ],
  [
    "JSON loaded into editor. Review before saving a new version.",
    "JSON wczytany do edytora. Sprawdź go przed zapisem nowej wersji."
  ],
  [
    "Dictionary file loaded. Review its entries and Save new dictionary version to add it to this catalog.",
    "Plik słownika wczytany. Sprawdź wpisy i zapisz nową wersję, aby dodać ją do katalogu."
  ],
  [
    "New dictionary version saved. Previous versions and past runs are unchanged.",
    "Nowa wersja słownika zapisana. Wcześniejsze wersje i zadania pozostają bez zmian."
  ]
]) guiPolish.set(en, pl);
guiPolish.set("Saving new dictionary version…", "Zapisywanie nowej wersji słownika…");
guiPolish.set("Manage project dictionaries, compare editions, edit terms and save new versions. Dictionaries are optional; previous versions remain available.", "Zarządzaj słownikami projektu, porównuj wersje, edytuj terminy i zapisuj nowe wersje. Słowniki są opcjonalne, a wcześniejsze wersje pozostają dostępne.");
guiPolish.set("Use optional API assistance or skip it to translate manually. Every candidate requires semantic review before export.", "Skorzystaj z opcjonalnej pomocy API lub pomiń ją i tłumacz ręcznie. Każda propozycja wymaga weryfikacji znaczenia przed eksportem.");
guiPolish.set("Current direction: PL → EN.", "Aktualny kierunek: PL → EN.");
guiPolish.set("Current direction: EN → PL.", "Aktualny kierunek: EN → PL.");
guiPolish.set("Preset colors", "Kolory profilu");
guiPolish.set("Saving custom profile…", "Zapisywanie własnego profilu…");
function guiUiText(value) {
  if (guiLocale !== "pl") return value;
  const trimmed = value.trim();
  const coded = guiDiagnosticPattern.exec(trimmed);
  if (coded) {
    const description = guiPolishErrorDescriptions.get(coded[1]);
    const translatedBody = guiUiText(coded[2]);
    if (["GUI_PROFILE_INVALID", "GUI_DICTIONARY_REQUEST_INVALID", "GUI_QUEUE_ACTION_REJECTED", "GUI_WORKDIR_INVALID", "GUI_EXPORT_DOWNLOAD_INVALID"].includes(coded[1]) && translatedBody !== coded[2]) return `${coded[1]}: ${translatedBody}`;
    return `${coded[1]}: ${description || (translatedBody !== coded[2] ? translatedBody : guiPolishFallbackError(coded[1]))}`;
  }
  const exact = guiPolish.get(trimmed);
  if (exact !== undefined) return value.replace(trimmed, exact);
  const indicator = /^(ASR|Correction|Review|Original export|LLM translation|Translation|Translated export): (.*)$/.exec(trimmed);
  if (indicator) return `${guiUiText(indicator[1])}: ${guiUiText(indicator[2])}`;
  const dynamic = guiPolishDynamicText(trimmed);
  if (dynamic !== null) return value.replace(trimmed, dynamic);
  let translated = guiPolish.get(trimmed);
  if (!translated) {
    const composite = /^(completed|failed|staged|queued|running|cancelled|cancel_requested) · (.+)$/.exec(trimmed);
    if (composite) return `${guiPolish.get(composite[1]) || composite[1]} · ${guiUiText(composite[2])}`;
    translated = trimmed.replace(/^Workspace saved: (.*)$/, 'Zapisano obszar pracy: $1')
      .replace(/^Workspace loaded: (.*)\. Provider credentials and confirmations were not restored\.$/, 'Wczytano obszar pracy: $1. Dane dostępowe i potwierdzenia nie zostały przywrócone.')
      .replace(/^(\d+) selected; batch execution will remain per-item consent gated\.$/, 'Wybrano: $1; zgoda na przetwarzanie pozostaje wymagana dla każdej pozycji.')
      .replace(/^\((\d+) items?\)$/, '(pozycje: $1)')
      .replace(/^Selected: (.+)\. Inspect, then run dry-run to review this episode before adding it to the queue\.$/, 'Wybrano: $1. Sprawdź pliki i uruchom zaplanuj przetwarzanie przed dodaniem pliku do kolejki.')
      .replace(/^Batch selection: (\d+) correction · (\d+) translation$/, "Zaznaczenie zbiorcze: $1 korekta · $2 tłumaczenie")
      .replace(/^Units (\d+)–(\d+) of (\d+)$/, "Jednostki $1–$2 z $3")
      .replace(/^\((\d+) items?\)$/, "($1 pozycji)")
      .replace(/^Workspace saved: (.*)$/, 'Zapisano obszar pracy: $1')
      .replace(/^Workspace loaded: (.*)\. Provider credentials and confirmations were not restored\.$/, 'Wczytano obszar pracy: $1. Dane dostępowe i potwierdzenia nie zostały przywrócone.')
      .replace(/^(\d+) selected; batch execution will remain per-item consent gated\.$/, 'Wybrano: $1; zgoda na przetwarzanie pozostaje wymagana dla każdej pozycji.')
      .replace(/^\((\d+) items?\)$/, '(pozycje: $1)')
      .replace(/^Selected: (.+)\. Inspect, then run dry-run to review this episode before adding it to the queue\.$/, 'Wybrano: $1. Sprawdź pliki i uruchom zaplanuj przetwarzanie przed dodaniem pliku do kolejki.')
      .replace(/^Batch selection: (\d+) correction · (\d+) translation$/, 'Wybór zbiorczy: $1 korekta · $2 tłumaczenie')
      .replace(/^Units (\d+)–(\d+) of (\d+)$/, 'Jednostki $1–$2 z $3')
      .replace(/^Inspected (\d+) \/ (\d+) episodes\. ?$/, "Sprawdzono $1 z $2 odcinków.")
      .replace(/^(\d+) dictionaries in this view\.$/, "Słowniki w tym widoku: $1.")
      .replace(/^(\d+) differences\. Neither dictionary was changed\.$/, "Różnice: $1. Żaden słownik nie został zmieniony.")
      .replace(/^Transcript section (\d+)$/, "Sekcja transkrypcji $1")
      .replace(/^Translation unit (\d+)$/, "Jednostka tłumaczenia $1")
      .replace(/^Section (\d+) of (\d+)$/, "Sekcja $1 z $2")
      .replace(/^(speaker_\d+) display name$/, "Nazwa wyświetlana $1")
      .replace(/^Speaker color (speaker_\d+)$/, "Kolor mówcy $1")
      .replace(/^Remove (speaker_\d+)$/, "Usuń $1")
      .replace(/^Next step: correction$/, "Następny krok: korekta")
      .replace(/^Next step: manual review$/, "Następny krok: ręczna weryfikacja")
      .replace(/^Next step: translation$/, "Następny krok: tłumaczenie")
      .replace(/^Next step: export verified transcript$/, "Następny krok: eksport źródła")
      .replace(/^Next step: export verified translation$/, "Następny krok: eksport tłumaczenia");
  }
  return value.replace(trimmed, translated);
}
function translateGui() {
  guiTranslationObserver?.disconnect();
  clearStaleGuiErrorDiagnostics();
  document.documentElement.lang = guiLocale;
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    if (node.parentElement.closest("script, style, textarea, pre, [data-gui-content], #library-comparison td, #gui-export-palette option, .translation-source, .gui-context-speaker, .stage-queue-item h4, .dictionary-candidate legend, .review-block select, #gui-recordings strong, .stage-queue-item h4")) continue;
    const previous = guiNodeSources.get(node);
    const source = previous && previous.last === node.nodeValue ? previous.source : node.nodeValue;
    retainGuiErrorDiagnostic(node, source);
    const translated = node.parentElement.id === "preview-review" && source.trim() === "Apply"
      ? source.replace("Apply", guiLocale === "pl" ? "Zatwierdź" : "Apply") : guiUiText(source);
    if (node.nodeValue !== translated) node.nodeValue = translated;
    guiNodeSources.set(node, {source, last: translated});
  }
  for (const element of document.querySelectorAll("[title], [aria-label], [placeholder]")) {
    const originals = guiAttributeSources.get(element) || {};
    for (const name of ["title", "aria-label", "placeholder"]) {
      const value = element.getAttribute(name);
      if (value === null) continue;
      const previous = originals[name];
      const source = previous && previous.last === value ? previous.source : value;
      const translated = guiUiText(source);
      if (translated !== value) element.setAttribute(name, translated);
      originals[name] = {source, last: translated};
    }
    guiAttributeSources.set(element, originals);
  }
  syncGuiStatusMotion();
  guiTranslationObserver?.observe(document.body, {childList:true, subtree:true, characterData:true, attributes:true, attributeFilter:["title", "aria-label", "placeholder", "hidden"]});
}
function startGuiTranslation() {
  let pending = false;
  guiTranslationObserver = new MutationObserver(() => {
    if (pending) return;
    pending = true;
    queueMicrotask(() => { pending = false; translateGui(); });
  });
  const originalConfirm = window.confirm.bind(window);
  window.confirm = text => originalConfirm(guiUiText(text));
  translateGui();
}
