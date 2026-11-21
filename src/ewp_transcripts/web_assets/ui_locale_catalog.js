"use strict";
const guiDiagnosticPattern = /^([A-Z][A-Z0-9]*_[A-Z0-9_]+):\s*([\s\S]*)$/;
// Additional audited UI copy. Keys remain English; codes and user content are preserved.
for (const [en, pl] of [
  ["Save key in OS credential store", "Zapisz klucz w magazynie systemowym"],
  ["Use saved OpenRouter key", "Użyj zapisanego klucza OpenRouter"],
  ["Remove saved OpenRouter key", "Usuń zapisany klucz OpenRouter"],
  ["Clear session key", "Wyczyść klucz sesji"],
  ["Manage OpenRouter key", "Zarządzaj kluczem OpenRouter"],
  ["OpenRouter API key", "Klucz API OpenRouter"],
  ["Key saved in the OS credential store and active for this session.", "Klucz zapisano w magazynie systemowym i uaktywniono w tej sesji."],
  ["Saved OpenRouter key is active for this session.", "Zapisany klucz OpenRouter jest aktywny w tej sesji."],
  ["Stored/session key cleared. The server environment still supplies a key.", "Usunięto zapisany klucz lub klucz sesji. Środowisko serwera nadal dostarcza klucz."],
  ["OpenRouter key removed from the selected storage.", "Usunięto klucz OpenRouter z wybranego magazynu."],
  ["OS credential storage is unavailable; use a session-only key.", "Systemowy magazyn poświadczeń jest niedostępny; użyj klucza tylko na tę sesję."],
  ["No OpenRouter key is saved in the OS store.", "W magazynie systemowym nie ma zapisanego klucza OpenRouter."],
  ["Unknown credential action.", "Nieznane działanie dotyczące klucza API."],
  ["One key is shared by ASR, correction and translation. OS storage is optional. If no secure store is available, use a session-only key. After restarting, choose Use saved OpenRouter key.", "Jeden klucz służy do ASR, korekty i tłumaczeń. Zapis systemowy jest opcjonalny. Jeśli bezpieczny magazyn nie jest dostępny, użyj klucza tylko na sesję. Po restarcie wybierz Użyj zapisanego klucza OpenRouter."],
  ["The key is sent only to this loopback server. Session-only keys are erased when it stops. You can explicitly save a key in the OS credential store and use it after a restart. ASR, correction and translation share this key; profiles and browser storage never contain it.", "Klucz trafia wyłącznie do tego lokalnego serwera. Klucz sesji znika po jego zatrzymaniu. Możesz jawnie zapisać klucz w magazynie systemowym i użyć go po restarcie. ASR, korekta i tłumaczenia korzystają z tego samego klucza; profile i pamięć przeglądarki go nie zawierają."],
  ["One OpenRouter key is available for ASR, correction and translation on this server. Session memory is cleared on exit; an explicitly saved OS entry remains until removed.", "Na serwerze jest dostępny jeden klucz OpenRouter do ASR, korekty i tłumaczeń. Pamięć sesji jest czyszczona po zakończeniu; jawnie zapisany klucz systemowy pozostaje do usunięcia."],
  ["Native Windows environment detected.", "Wykryto natywne środowisko Windows."],
  ["Native Windows setup and repair instructions", "Instrukcje konfiguracji i naprawy natywnego Windows"],
  ["This restores locked Python dependencies and the pinned private FFmpeg 7 shared runtime. Internet access is required. Save work and stop the GUI first.", "Przywraca przypięte zależności Pythona i prywatne biblioteki współdzielone FFmpeg 7. Wymaga internetu. Najpierw zapisz pracę i zatrzymaj GUI."],
  [
    "Jobs",
    "Zadania"
  ],
  [
    "Output",
    "Wynik"
  ],
  [
    "Recording language",
    "Język nagrania"
  ],
  [
    "Speakers",
    "Liczba mówców"
  ],
  [
    "Source files",
    "Źródła"
  ],
  [
    "Decision",
    "Działanie"
  ],
  [
    "process",
    "do przetworzenia"
  ],
  [
    "skip",
    "pomiń"
  ],
  [
    "none",
    "brak"
  ],
  [
    "None",
    "Brak"
  ],
  [
    "Dry-run",
    "Zaplanuj przetwarzanie"
  ],
  [
    "Planning…",
    "Planowanie…"
  ],
  [
    "Planning...",
    "Planowanie…"
  ],
  [
    "Dry-run completed",
    "Plan gotowy"
  ],
  [
    "Adding…",
    "Dodawanie…"
  ],
  [
    "Adding...",
    "Dodawanie…"
  ],
  [
    "Added to staged queue",
    "Dodano do kolejki oczekującej na uruchomienie"
  ],
  [
    "Inspecting…",
    "Sprawdzanie…"
  ],
  [
    "Inspection completed",
    "Sprawdzanie zakończone"
  ],
  [
    "Queue finished",
    "Kolejka ukończona"
  ],
  [
    "Queue is already running",
    "Kolejka jest już uruchomiona"
  ],
  [
    "No staged jobs to start",
    "Brak zadań oczekujących na uruchomienie"
  ],
  [
    "Prepare text for review",
    "Przygotuj tekst do sprawdzenia"
  ],
  [
    "Save and prepare for export",
    "Zapisz i przygotuj do eksportu"
  ],
  [
    "Formats",
    "Formaty"
  ],
  [
    "Apply translation",
    "Zastosuj tłumaczenie"
  ],
  [
    "Save translation",
    "Zapisz tłumaczenie"
  ],
  [
    "Save and export",
    "Zatwierdź i eksportuj"
  ],
  [
    "Continue to translation review",
    "Przejdź do przeglądu tłumaczenia"
  ],
  [
    "Translation review & export",
    "Weryfikacja tłumaczenia i eksport"
  ],
  [
    "Generate correction candidate",
    "Wygeneruj wstępną korektę"
  ],
  [
    "Generate translation candidate",
    "Wygeneruj propozycję tłumaczenia"
  ],
  [
    "Manual model ID",
    "Wpisz ID modelu"
  ],
  [
    "Check for current models and pricing",
    "Sprawdź dostępne modele i ceny"
  ],
  [
    "API endpoint",
    "Adres API"
  ],
  [
    "Reasoning-token budget",
    "Limit tokenów rozumowania"
  ],
  [
    "API check",
    "Sprawdzenie API"
  ],
  [
    "API key",
    "Klucz API"
  ],
  [
    "Set key for this session",
    "Ustaw klucz na tę sesję"
  ],
  [
    "Segments JSON",
    "Segmenty JSON"
  ],
  [
    "This makes an external request to the selected provider to read current model availability and listed input/output prices. It does not send transcript text and never runs automatically.",
    "Ta czynność wysyła zapytanie do wybranego dostawcy o dostępne modele i ceny wejścia/wyjścia. Nie wysyła transkrypcji i nigdy nie uruchamia się automatycznie."
  ],
  [
    "Treat API keys as secrets. Use a dedicated key with a low spending limit; the project's 20-episode testing used substantially less than a USD $2 limit.",
    "Traktuj klucze API jak hasła. Używaj osobnego klucza z niskim limitem wydatków; testy projektu na 20 odcinkach wykorzystały znacznie mniej niż limit 2 USD."
  ],
  [
    "The key is sent only to this loopback server, kept only for the current server process, never written to project files or browser storage, and must be entered again after restarting the GUI.",
    "Klucz trafia wyłącznie do tego lokalnego serwera i pozostaje tylko w pamięci jego procesu. Nie jest zapisywany w plikach projektu ani pamięci przeglądarki. Po ponownym uruchomieniu GUI trzeba podać go ponownie."
  ],
  [
    "Use the server environment or set a key for the active GUI server process. The key is shared with browsers connected to that process, but is never written to project files, saved workspaces, or browser storage.",
    "Skorzystaj ze zmiennej środowiskowej serwera lub ustaw klucz dla bieżącego procesu GUI. Klucz jest dostępny dla przeglądarek połączonych z tym procesem, ale nie trafia do plików projektu, zapisów pracy ani pamięci przeglądarki."
  ],
  [
    " I understand that transcript text is sent to a separately operated LM Studio API whose logging, retention, or forwarding EWP Transcriber cannot control. The translation remains non-final and requires semantic manual review.",
    " Rozumiem, że tekst transkrypcji trafia do osobno obsługiwanego API LM Studio. EWP Transcriber nie kontroluje jego rejestrowania, przechowywania ani przekazywania danych. Tłumaczenie jest wstępne i wymaga ręcznej weryfikacji znaczenia."
  ],
  [
    "Add a speaker available only in this editable review and its descendant revision.",
    "Dodaj mówcę do tego edytowalnego tekstu i utworzonej z niego rewizji."
  ],
  [
    "Apply a verified immutable revision before exporting.",
    "Zapisz zweryfikowaną rewizję przed eksportem."
  ],
  [
    "Apply a verified immutable revision before proceeding to translation.",
    "Zapisz zweryfikowaną rewizję przed przejściem do tłumaczenia."
  ],
  [
    "Ask this deployment's operating system for a server-visible folder; no folder contents are uploaded.",
    "Wybierz katalog dostępny dla serwera w oknie systemowym. Zawartość katalogu nie jest przesyłana."
  ],
  [
    "Auto-save checked: no tracked workflow-field changes to save.",
    "Sprawdzono autozapis: brak zmian ustawień do zapisania."
  ],
  [
    "Auto-save completed. No credential, confirmation, or editor text was stored.",
    "Autozapis zakończony. Nie zapisano danych dostępowych, potwierdzeń ani treści edytora."
  ],
  [
    "Auto-save detected tracked changes; validating workspace paths…",
    "Autozapis wykrył zmiany; sprawdzanie ścieżek obszaru pracy…"
  ],
  [
    "Auto-save inactive: load an available workspace first.",
    "Autozapis nieaktywny: najpierw wczytaj dostępny obszar pracy."
  ],
  [
    "Auto-save inactive: save or load a workspace first.",
    "Autozapis nieaktywny: najpierw zapisz lub wczytaj obszar pracy."
  ],
  [
    "Changes pending for auto-save. They will be validated at the next 60-second check.",
    "Zmiany oczekują na autozapis. Zostaną sprawdzone podczas kolejnej kontroli za maksymalnie 60 sekund."
  ],
  [
    "Checking current external model data…",
    "Sprawdzanie aktualnych danych modeli u dostawcy…"
  ],
  [
    "Choose an existing user-space audio file with the browser's native picker.",
    "Wybierz dostępny plik audio w systemowym oknie przeglądarki."
  ],
  [
    "Choose completed canonical result JSON files with the browser's native file picker.",
    "Wybierz pliki JSON ukończonych wyników transkrypcji w systemowym oknie przeglądarki."
  ],
  [
    "Completed canonical transcription loaded; configure optional correction before generating a candidate.",
    "Wczytano ukończoną transkrypcję. Skonfiguruj opcjonalną korektę przed wygenerowaniem wstępnej korekty."
  ],
  [
    "Correction is running; do not close the server.",
    "Korekta trwa; nie zamykaj serwera."
  ],
  [
    "Empty-unit handling changed; preview the saved translation again.",
    "Zmieniono obsługę pustych jednostek; ponownie zastosuj zapisany szkic tłumaczenia."
  ],
  [
    "Existing non-final correction candidate found for this canonical result; manual review is still required.",
    "Znaleziono wstępną korektę tej transkrypcji. Nadal wymaga ręcznego sprawdzenia."
  ],
  [
    "Export publication files from the applied verified revision.",
    "Wyeksportuj pliki z zapisanej, zweryfikowanej rewizji."
  ],
  [
    "Fill translation source fields from this verified revision.",
    "Uzupełnij źródło tłumaczenia tą zweryfikowaną rewizją."
  ],
  [
    "Generating correction…",
    "Generowanie wstępnej korekty…"
  ],
  [
    "LLM-assisted correction skipped; this output is now open in manual review.",
    "Pominięto korektę z LLM. Tekst jest otwarty do ręcznego sprawdzenia."
  ],
  [
    "LLM-assisted translation skipped. An editable manual translation review is open below; save, preview, verify, apply, and optionally export it.",
    "Pominięto tłumaczenie z LLM. Otworzono edytowalne tłumaczenie: zapisz szkic, zastosuj tłumaczenie, sprawdź je, zapisz do eksportu i wyeksportuj."
  ],
  [
    "Next occurrence",
    "Następne wystąpienie"
  ],
  [
    "Previous occurrence",
    "Poprzednie wystąpienie"
  ],
  [
    "Non-final correction candidate generated; manual review is required.",
    "Wygenerowano wstępną korektę. Wymaga ręcznego sprawdzenia."
  ],
  [
    "Output folder selection cancelled.",
    "Anulowano wybór katalogu wyników."
  ],
  [
    "Preview passed: exact source lineage, complete target text, and immutable unit ownership validated. No translation was published.",
    "Sprawdzenie zakończone: potwierdzono pochodzenie źródła, kompletność tłumaczenia i przypisanie jednostek. Tłumaczenie nie zostało jeszcze zapisane do eksportu."
  ],
  [
    "Preview the current draft before applying.",
    "Zatwierdź bieżący szkic przed zapisaniem go do eksportu."
  ],
  [
    "Redo a current-editor change. This does not change saved files.",
    "Przywróć zmianę w bieżącym edytorze. Zapisane pliki pozostaną bez zmian."
  ],
  [
    "Remove this queue entry. Saved files remain on disk.",
    "Usuń tę pozycję z kolejki. Zapisane pliki pozostaną na dysku."
  ],
  [
    "Remove this unused revision-only speaker from the current draft.",
    "Usuń tego nieużywanego mówcę z bieżącego szkicu."
  ],
  [
    "Saved work state removed.",
    "Usunięto zapisany stan pracy."
  ],
  [
    "Saved workspace list refreshed.",
    "Odświeżono listę zapisów pracy."
  ],
  [
    "Select actionable queue items or reopen one correction before generating a candidate.",
    "Zaznacz dostępne pozycje kolejki lub otwórz jedną korektę przed wygenerowaniem wstępnej korekty."
  ],
  [
    "Select actionable queue items or reopen one translation before generating a candidate.",
    "Zaznacz dostępne pozycje kolejki lub otwórz jedno tłumaczenie przed wygenerowaniem propozycji."
  ],
  [
    "Select complete words or a sentence, then isolate that selected text for separate speaker assignment.",
    "Zaznacz całe słowa lub zdanie, a następnie wydziel zaznaczony tekst, aby przypisać mu innego mówcę."
  ],
  [
    "Selected queue output loaded; review provider settings and consent before generating a non-final translation candidate.",
    "Wczytano wybraną pozycję kolejki. Sprawdź ustawienia dostawcy i zgodę przed wygenerowaniem propozycji tłumaczenia."
  ],
  [
    "Speaker color",
    "Kolor mówcy"
  ],
  [
    "This saved review has already been applied.",
    "Ten zapisany tekst został już przygotowany do eksportu."
  ],
  [
    "Translation draft saved; preview is required again.",
    "Zapisano szkic tłumaczenia; ponownie zastosuj tłumaczenie."
  ],
  [
    "Translation is running; do not close the server.",
    "Tłumaczenie trwa; nie zamykaj serwera."
  ],
  [
    "Undo the last current-editor change. This does not change saved files.",
    "Cofnij ostatnią zmianę w bieżącym edytorze. Zapisane pliki pozostaną bez zmian."
  ],
  [
    "Verified manual translation applied.",
    "Zweryfikowane tłumaczenie zapisano i przygotowano do eksportu."
  ],
  [
    "Verified transcript source loaded from the completed review step.",
    "Wczytano zweryfikowane źródło z ukończonego sprawdzania tekstu."
  ],
  [
    "Verified transcript source loaded from this queue output.",
    "Wczytano zweryfikowane źródło z tej pozycji kolejki."
  ],
  [
    "Verified translation audited and exported.",
    "Tłumaczenie zatwierdzono i wyeksportowano."
  ],
  [
    "Versioned project dictionary published.",
    "Zapisano nową wersję słownika projektu."
  ],
  [
    "pending",
    "oczekuje"
  ],
  [
    "complete",
    "ukończone"
  ],
  [
    "failed",
    "błąd"
  ],
  [
    "skipped",
    "pominięte"
  ],
  [
    "running",
    "w toku"
  ],
  [
    "queued",
    "oczekuje na przetwarzanie"
  ],
  [
    "staged",
    "oczekuje na start"
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
    "Tłumaczenie z LLM"
  ],
  [
    "Translated export",
    "Eksport tłumaczenia"
  ],
  [
    "Correction",
    "Korekta"
  ],
  [
    "Translation",
    "Tłumaczenie"
  ],
  [
    "ASR",
    "ASR"
  ],
  [
    "raw-asr",
    "surowa transkrypcja ASR"
  ],
  [
    "manual",
    "ręczna"
  ],
  [
    "automated",
    "automatyczna"
  ],
  [
    "manual-verified",
    "ręcznie zweryfikowane"
  ],
  [
    "unverified",
    "niezweryfikowane"
  ],
  [
    "manual-verified-revision",
    "ręcznie zweryfikowana rewizja"
  ],
  [
    "raw",
    "surowe"
  ],
  [
    "approved",
    "zatwierdzone"
  ],
  [
    "rejected",
    "odrzucone"
  ],
  [
    "Non-final candidate",
    "Wstępna propozycja"
  ],
  [
    "No — manual review required",
    "Nie — wymagane ręczne sprawdzenie"
  ],
  [
    "None — editable draft only",
    "Brak — tylko edytowalny szkic"
  ],
  [
    "None — manual review required",
    "Brak — wymagane ręczne sprawdzenie"
  ],
  [
    "Final",
    "Wersja ostateczna"
  ],
  [
    "Publication",
    "Zapis do eksportu"
  ],
  [
    "Source verification",
    "Weryfikacja źródła"
  ],
  [
    "Candidate",
    "Propozycja"
  ],
  [
    "Dictionary",
    "Słownik"
  ],
  [
    "Statistics",
    "Statystyki"
  ],
  [
    "Warnings",
    "Ostrzeżenia"
  ]
]) guiPolish.set(en.trim(), pl);
const guiPolishErrorDescriptions = new Map([
  [
    "GUI_DRY_RUN_REQUIRED",
    "Najpierw zaplanuj przetwarzanie i sprawdź plan dla dokładnie tego pliku, katalogu wyników, języka i liczby mówców. Następnie dodaj plik do kolejki."
  ],
  [
    "GUI_OUTPUT_REQUIRED",
    "Wprowadź wspólny katalog wyników przed zaplanowaniem przetwarzania lub dodaniem pliku do kolejki."
  ],
  [
    "GUI_CONFIRMATION_REQUIRED",
    "Potwierdź sprawdzenie planu przed dodaniem zadań do kolejki."
  ],
  [
    "GUI_CORRECTION_OUTPUT_ROOT_REQUIRED",
    "Wybierz katalog wyników korekty przed pominięciem korekty."
  ],
  [
    "GUI_CORRECTION_RESULT_REQUIRED",
    "Wybierz wynik transkrypcji przed pominięciem korekty."
  ],
  [
    "GUI_TRANSLATION_CANDIDATE_NOT_FOUND",
    "Nie można otworzyć przeglądu tłumaczenia, ponieważ brakuje jego wstępnej propozycji."
  ],
  [
    "GUI_TRANSLATION_OUTPUT_REQUIRED",
    "Wybierz katalog wyników tłumaczenia przed rozpoczęciem ręcznego tłumaczenia."
  ],
  [
    "GUI_TRANSLATION_RESULT_REQUIRED",
    "Wybierz wynik transkrypcji przed rozpoczęciem ręcznego tłumaczenia."
  ],
  [
    "GUI_WORKSPACE_SELECTION_REQUIRED",
    "Najpierw wybierz zapisany obszar pracy."
  ],
  [
    "GUI_API_UNAVAILABLE",
    "Lokalny serwer GUI jest niedostępny. Sprawdź, czy nadal działa, i ponów operację."
  ],
  [
    "GUI_REVIEW_CHANGED_DURING_SAVE",
    "Zapisano wcześniejszy szkic. Nowsze zmiany pozostają w edytorze; zapisz je i ponownie zatwierdź tekst."
  ],
  [
    "GUI_REVIEW_SESSION_NOT_FOUND",
    "Nie znaleziono zapisanego przeglądu dla tego nagrania."
  ],
  [
    "GUI_REVIEW_SPEAKER_IN_USE",
    "Ten mówca jest przypisany do tekstu. Zmień przypisanie wszystkich jego fragmentów przed usunięciem."
  ],
  [
    "GUI_REVIEW_SPLIT_CURSOR_REQUIRED",
    "Umieść kursor między całymi słowami, z tekstem po obu stronach podziału."
  ],
  [
    "GUI_TRANSLATION_REVIEW_RESTORE_FAILED",
    "Nie udało się przywrócić przeglądu tłumaczenia. Sprawdź dostępność zapisanego szkicu i jego źródła."
  ],
  [
    "GUI_QUEUE_ACTIVE",
    "Nie można usunąć zadania, które oczekuje na przetwarzanie lub jest właśnie przetwarzane."
  ],
  [
    "GUI_CSRF_REJECTED",
    "Sesja GUI jest nieaktualna. Odśwież stronę i ponów operację."
  ]
]);

function guiPolishDynamicText(text) {
  const diagnostic = /^(PASS|WARNING|FAIL) · ([^:]+): ([\s\S]+)$/.exec(text);
  if (diagnostic) return `${({PASS:"POPRAWNE", WARNING:"OSTRZEŻENIE", FAIL:"BŁĄD"})[diagnostic[1]]} · ${diagnostic[2]}: ${guiUiText(diagnostic[3])}`;
  const rules = [
    [/^(\d+) unavailable queue items? omitted; check missing source or result files before restoring it\.$/, 'Pominięte pozycje kolejki: $1. Sprawdź brakujące pliki źródłowe lub wyniki przed przywróceniem.'],
    [/^(\d+) session-picked queue items? omitted because their temporary source cannot survive a GUI restart\.$/, 'Pominięte tymczasowe pozycje kolejki: $1. Ponownie wybierz oryginalne pliki przed wznowieniem pracy.'],
    [/^(\d+) stale file fields? cleared\.$/, 'Wyczyszczone nieaktualne ścieżki: $1.'],
    [/^Selected: (.+)\. Review the processing plan before adding these jobs to the queue\.$/, 'Wybrano: $1. Sprawdź plan przetwarzania przed dodaniem zadań do kolejki.'],
    [/^(\d+) temporary directories selected; ([\d.]+) MiB\. Confirm deletion within five minutes\.$/, 'Wybrano katalogi tymczasowe: $1; $2 MiB. Potwierdź usunięcie w ciągu pięciu minut.'],
    [/^Temporary directories removed: (\d+)\.$/, 'Usunięte katalogi tymczasowe: $1.'],
    [/^Cleanup stopped\. Removed: (\d+)\. Refresh the inventory before retrying\.$/, 'Zatrzymano usuwanie. Usunięto: $1. Odśwież listę przed kolejną próbą.'],
    [/^Started (\d+) queued job\(s\)$/, 'Uruchomiono zadania: $1'],
    [/^API OK · (.+)$/, 'API działa · $1'],
    [/^(\d+) compatible dictionary option\(s\) loaded\.$/, 'Wczytano pasujące słowniki: $1.'],
    [/^Planning (\d+) \/ (\d+): (.*)$/, 'Planowanie $1 z $2: $3'],
    [/^Added to staged queue: (\d+)\. Already completed: (\d+)\.$/, 'Dodano do kolejki: $1. Już ukończone: $2.'],
    [/^Inspecting (\d+) \/ (\d+): (.*)$/, 'Sprawdzanie $1 z $2: $3'],
    [/^Inspected (\d+) \/ (\d+) episodes\.\s*(.*)$/, 'Sprawdzono $1 z $2 plików. $3'],
    [/^Copying (.+) into this local GUI session…$/, 'Kopiowanie $1 do lokalnej sesji GUI…'],
    [/^Shared output folder selected: (.+)$/, 'Wybrano wspólny katalog wyników: $1'],
    [/^Generating correction (\d+) of (\d+): (.*)$/, 'Generowanie wstępnej korekty $1 z $2: $3'],
    [/^Generating translation (\d+) of (\d+): (.*)$/, 'Generowanie propozycji tłumaczenia $1 z $2: $3'],
    [/^Correction batch finished: (\d+) candidates?, (\d+) errors?\.$/, 'Korekta zakończona: propozycje $1, błędy $2.'],
    [/^Translation batch finished: (\d+) candidates?, (\d+) errors?\. Open each candidate from its semantic review queue row\.$/, 'Tłumaczenie zakończone: propozycje $1, błędy $2. Otwórz każdą propozycję z jej pozycji kolejki przeglądu tłumaczenia.'],
    [/^LLM-assisted correction skipped for (\d+) of (\d+) selected outputs: (.*)$/, 'Pominięto korektę z LLM dla $1 z $2 wybranych wyników: $3'],
    [/^Skipped LLM-assisted translation for (\d+) selected outputs?\. (.*)$/, 'Pominięto tłumaczenie z LLM dla wybranych wyników: $1. $2'],
    [/^Use each semantic review queue row for manual translation\.$/, 'Otwórz odpowiednią pozycję kolejki przeglądu, aby tłumaczyć ręcznie.'],
    [/^(\d+) units$/, 'Liczba jednostek: $1'], [/^(\d+) sections$/, 'Liczba sekcji: $1'],
    [/^(.+) · (pl|en|auto) · speakers: (auto|\d+)$/, '$1 · $2 · liczba mówców: $3'],
    [/^(.*) · source: (.*)$/, (all, before, state) => `${before} · źródło: ${guiUiText(state)}`],
    [/^WARNING: source is (.+), not manually verified\. The non-final translation requires semantic manual review\.$/, (all, state) => `OSTRZEŻENIE: źródło to ${guiUiText(state)} i nie zostało ręcznie zweryfikowane. Wstępne tłumaczenie wymaga sprawdzenia znaczenia.`],
    [/^Error: (.+)$/, (all, error) => `Błąd: ${guiUiText(error)}`],
    [/^Status: (.+)$/, (all, status) => `Stan: ${guiUiText(status)}`],
    [/^Available correction dictionaries$/, 'Dostępne słowniki korekty'],
    [/^Available translation dictionaries$/, 'Dostępne słowniki tłumaczenia'],
    [/^Dictionary document format v(.+); edition is identified by the dictionary ID\.$/, 'Format dokumentu słownika: v$1; wersję identyfikuje ID słownika.'],
    [/^(\d+) occurrence\(s\) across (\d+) case\(s\)$/, 'Liczba wystąpień: $1; liczba nagrań: $2'],
    [/^Example · (.*)$/, 'Przykład · $1'], [/^Before: (.*)$/, 'Przed: $1'], [/^After: (.*)$/, 'Po: $1'],
    [/^Show (\d+) more occurrences$/, 'Pokaż kolejne wystąpienia: $1'],
    [/^(.+): (\d+) candidates; (\d+) pending, (\d+) approved, (\d+) rejected\.$/, '$1: propozycje $2; oczekujące $3, zatwierdzone $4, odrzucone $5.'],
    [/^Draft saved before removing (speaker_\d+)\. Save again when the current review is ready\.$/, 'Zapisano szkic przed usunięciem $1. Zapisz go ponownie po zakończeniu sprawdzania.'],
    [/^(speaker_\d+) removed from this revision-only speaker list\. Save the draft when ready\.$/, 'Usunięto $1 z listy mówców tej rewizji. Zapisz gotowy szkic.'],
    [/^Draft saved before adding (speaker_\d+)\. Rename it if needed, assign it to isolated text, then save again\.$/, 'Zapisano szkic przed dodaniem $1. W razie potrzeby zmień nazwę, przypisz mówcę do wydzielonego tekstu i zapisz ponownie.'],
    [/^(speaker_\d+) added for this revision only\. Rename it if needed, then assign it to isolated text and save the draft\.$/, 'Dodano $1 tylko do tej rewizji. W razie potrzeby zmień nazwę, przypisz mówcę do wydzielonego tekstu i zapisz szkic.'],
    [/^Cleared (\d+) queue items?; reloading the blank work area\.$/, 'Usunięto pozycje kolejki: $1; wczytywanie pustego obszaru pracy.'],
    [/^Workspace auto-saved: (.*)\.$/, 'Automatycznie zapisano obszar pracy: $1.'],
    [/^Saved work state file imported: (.*)\.$/, 'Zaimportowano zapis pracy: $1.'],
    [/^Auto-save could not save the tracked changes and will retry: (.*)$/, (all, error) => `Autozapis nie zapisał zmian i spróbuje ponownie: ${guiUiText(error)}`],
    [/^(\d+) session-picked queue items? omitted because their temporary source cannot survive a GUI restart\.$/, 'Pominięto pozycje kolejki: $1, ponieważ ich tymczasowe źródła nie przetrwają restartu GUI.'],
    [/^(\d+) unavailable queue items? omitted; add its original source again before resuming it\.$/, 'Pominięto niedostępne pozycje kolejki: $1; dodaj ponownie plik źródłowy przed wznowieniem.'],
    [/^(\d+) stale file fields? cleared\.$/, 'Wyczyszczono nieaktualne pola plików: $1.'],
    [/^Inventory complete\. (\d+) saved workspaces? audited\.$/, 'Sprawdzanie zakończone. Liczba sprawdzonych zapisów pracy: $1.'],
    [/^Inventory complete: (\d+) managed cop(?:y|ies), (\d+) eligible; (\d+) saved workspaces? audited\.$/, 'Sprawdzanie zakończone: kopie źródeł $1, możliwe do usunięcia $2; sprawdzone zapisy pracy $3.'],
    [/^(\d+) unreferenced managed source cop(?:y|ies) permanently deleted\. Publication artifacts were not changed\.$/, 'Trwale usunięto nieużywane kopie źródeł: $1. Pliki publikacji pozostały bez zmian.'],
    [/^Select (.+) for permanent managed-source cleanup$/, 'Zaznacz $1 do trwałego usunięcia kopii źródłowej'],
    [/^Select (.+) for a future bulk (.+) operation$/, 'Zaznacz $1 do działania zbiorczego w tej kolejce'],
    [/^Remove (.+)\? This deletes only its saved workspace JSON, not transcripts, reviews, exports, or dictionaries\.$/, 'Usunąć $1? Usunięty zostanie tylko zapis stanu pracy w JSON. Transkrypcje, szkice, eksporty i słowniki pozostaną bez zmian.'],
    [/^Permanently delete (\d+) selected unreferenced managed source cop(?:y|ies)\? This cannot be undone by EWP Transcriber\. Confirm that this output directory and any separate workspace catalogs are backed up\.$/, 'Trwale usunąć zaznaczone nieużywane kopie źródłowe: $1? EWP Transcriber nie może cofnąć tej operacji. Potwierdź wykonanie kopii zapasowej katalogu wyników i katalogów zapisów pracy.'],
    [/^(\d+) saved results? added\.\s*(.*)$/, 'Dodano zapisane wyniki: $1. $2'],

    [/^Accepted Ubuntu (.+) baseline detected\.$/, 'Wykryto obsługiwaną wersję Ubuntu $1.'],
    [/^Executable '(.+)' is available\.$/, 'Program „$1” jest dostępny.'],
    [/^Executable '(.+)' returned an error\.$/, 'Program „$1” zwrócił błąd.'],
    [/^Required executable '(.+)' is missing\.$/, 'Brakuje wymaganego programu „$1”.'],
    [/^Unable to run '(.+)'\.$/, 'Nie można uruchomić programu „$1”.'],
    [/^Pinned local (.+) model snapshot is available\.$/, 'Przypięta lokalna wersja modelu ($1) jest dostępna.'],
    [/^Pinned local (.+) model snapshot is missing; follow WSL config\/MODEL_SETUP.md\.$/, 'Brakuje przypiętej lokalnej wersji modelu ($1); postępuj według WSL config/MODEL_SETUP.md.'],
    [/^Speech dependencies failed to load\.[\s\S]*$/, 'Nie udało się załadować zależności mowy. Zatrzymaj GUI i uruchom bash scripts/repair-dependencies.sh w repozytorium transkrypcji. Szczegóły naprawy są w Ustawieniach. Jeśli problem pojawił się po aktualizacji Ubuntu 24.04 do 26.04, skorzystaj z WSL config/UBUNTU_UPGRADE.md lub /help/ubuntu-upgrade.'],
    [/^(.+) · (correction|translation)( \(removed\))?$/, (all, name, kind, removed) => `${name} · ${kind === "correction" ? "korekta" : "tłumaczenie"}${removed ? " (usunięty z listy)" : ""}`],
    [/^(.+) · (.+) catalog · (available|paths unavailable) · (.*)$/, (all, name, catalog, state, date) => `${name} · katalog ${catalog} · ${state === "available" ? "dostępny" : "ścieżki niedostępne"} · ${date}`],

    [/^([^:]+): (pending|complete|failed|skipped)$/, (all, label, state) => `${guiUiText(label)}: ${guiUiText(state)}`],
  ];
  for (const [pattern, replacement] of rules) {
    if (pattern.test(text)) return text.replace(pattern, replacement);
  }
  return null;
}

for (const [en, pl] of [
  [
    "* or comma-separated recording IDs",
    "* lub ID nagrań oddzielone przecinkami"
  ],
  [
    "Alignment warnings",
    "Ostrzeżenia dopasowania słów"
  ],
  [
    "Append this entire block to the previous block. Set the previous block's speaker first if needed.",
    "Dołącz cały fragment do poprzedniego. W razie potrzeby najpierw ustaw mówcę poprzedniego fragmentu."
  ],
  [
    "Auto-save active. The next change-sensitive check runs within 60 seconds.",
    "Autozapis aktywny. Kolejne sprawdzenie zmian nastąpi w ciągu 60 sekund."
  ],
  [
    "Auto-save is off for this active workspace.",
    "Autozapis jest wyłączony dla bieżącego obszaru pracy."
  ],
  [
    "Canonical JSON",
    "Źródłowy wynik JSON"
  ],
  [
    "Checking; no transcript text is sent",
    "Sprawdzanie; tekst transkrypcji nie jest wysyłany"
  ],
  [
    "Clear EWP browser state and reload? This removes browser-stored paths, active review pointers, and display choices. It does not delete saved reviews, revisions, exports, dictionaries, queued server jobs, or any other files on disk. Unsaved editor changes will be lost.",
    "Wyczyścić stan EWP w przeglądarce i odświeżyć stronę? Usunięte zostaną zapamiętane ścieżki, otwarte przeglądy i ustawienia wyświetlania. Zapisane szkice, rewizje, eksporty, słowniki, zadania serwera i pliki na dysku pozostaną bez zmian. Niezapisane zmiany edytora zostaną utracone."
  ],
  [
    "Clear the current queue and unsaved browser work, then start with a blank slate? Saved work states, transcripts, reviews, revisions, exports, and dictionaries will not be deleted. Active transcription must finish first.",
    "Wyczyścić bieżącą kolejkę i niezapisaną pracę w przeglądarce? Zapisane stany pracy, transkrypcje, szkice, rewizje, eksporty i słowniki pozostaną bez zmian. Aktywna transkrypcja musi najpierw się zakończyć."
  ],
  [
    "Clear the current review from this browser? Saved review files will remain on disk.",
    "Wyczyścić bieżący tekst z przeglądarki? Zapisane pliki pozostaną na dysku."
  ],
  [
    "Clear the current translation review from this browser? Saved drafts remain on disk.",
    "Wyczyścić bieżący przegląd tłumaczenia z przeglądarki? Zapisane szkice pozostaną na dysku."
  ],
  [
    "Current review cleared from the browser. Saved files were not deleted.",
    "Wyczyszczono bieżący tekst z przeglądarki. Nie usunięto zapisanych plików."
  ],
  [
    "Current translation review cleared from the browser. Saved drafts remain on disk.",
    "Wyczyszczono bieżący przegląd tłumaczenia z przeglądarki. Zapisane szkice pozostają na dysku."
  ],
  [
    "Cursor split created two editable blocks. Save and Preview to validate real word alignment before Apply.",
    "Podział utworzył dwa edytowalne fragmenty. Zapisz szkic i zatwierdź tekst, aby sprawdzić dopasowanie słów przed zapisaniem do eksportu."
  ],
  [
    "Default GUI workspace location",
    "Domyślne miejsce zapisów pracy GUI"
  ],
  [
    "Dictionary ID is required",
    "Wymagane jest ID słownika"
  ],
  [
    "Discard the current unsaved translation edits and restore the saved draft?",
    "Odrzucić niezapisane zmiany tłumaczenia i przywrócić zapisany szkic?"
  ],
  [
    "Draft saved before merge. Entire block merged with the previous block; save again before previewing.",
    "Zapisano szkic przed połączeniem. Cały fragment połączono z poprzednim; zapisz ponownie przed zatwierdzeniem."
  ],
  [
    "Draft saved before separation. Selected text isolated; choose its speaker, then save again.",
    "Zapisano szkic przed wydzieleniem tekstu. Wybierz mówcę wydzielonego fragmentu i zapisz ponownie."
  ],
  [
    "Draft saved;",
    "Zapisano szkic;"
  ],
  [
    "Entire block merged with the previous block. Save the draft before previewing.",
    "Połączono cały fragment z poprzednim. Zapisz szkic przed zatwierdzeniem."
  ],
  [
    "Immutable revision already written",
    "Niezmienna rewizja jest już zapisana"
  ],
  [
    "Immutable revision written",
    "Zapisano niezmienną rewizję"
  ],
  [
    "Inspection failed",
    "Sprawdzanie pliku nie powiodło się"
  ],
  [
    "Intentional empty units",
    "Celowo puste jednostki"
  ],
  [
    "Merge this entire block with the previous block? The current unsaved draft can still be cleared or edited before saving.",
    "Połączyć cały fragment z poprzednim? Bieżący szkic nadal można wyczyścić lub edytować przed zapisem."
  ],
  [
    "No compatible dictionaries found in this catalog.",
    "Nie znaleziono pasujących słowników w tym katalogu."
  ],
  [
    "No — semantic review required",
    "Nie — wymagane sprawdzenie znaczenia"
  ],
  [
    "Non-final translation candidate generated; semantic manual review is required.",
    "Wygenerowano propozycję tłumaczenia. Wymaga ręcznej weryfikacji znaczenia."
  ],
  [
    "None — restored editable draft",
    "Brak — przywrócono edytowalny szkic"
  ],
  [
    "None — validation only",
    "Brak — tylko sprawdzenie"
  ],
  [
    "Planned revision",
    "Planowana rewizja"
  ],
  [
    "Preview passed: intentional empty units were recorded and will be omitted from exports. No translation was published.",
    "Sprawdzenie zakończone: zapisano celowo puste jednostki, które zostaną pominięte w eksporcie. Tłumaczenie nie zostało jeszcze zapisane do eksportu."
  ],
  [
    "Preview passed; review remains unpublished",
    "Sprawdzenie zakończone; tekst nie jest jeszcze zapisany do eksportu"
  ],
  [
    "Preview passed; this review is already published",
    "Sprawdzenie zakończone; ten tekst jest już zapisany do eksportu"
  ],
  [
    "Private default workspace catalog",
    "Prywatny domyślny katalog zapisów pracy"
  ],
  [
    "Publish this exact previewed draft as an immutable verified revision.",
    "Zapisz ten dokładnie sprawdzony szkic jako niezmienną, zweryfikowaną rewizję."
  ],
  [
    "Redid the current-editor change. Save before previewing.",
    "Przywrócono zmianę w edytorze. Zapisz przed zastosowaniem tłumaczenia."
  ],
  [
    "Redo applied to the current draft. Preview again before applying.",
    "Przywrócono zmianę w szkicu. Ponownie zatwierdź tekst przed zapisaniem do eksportu."
  ],
  [
    "Revision file",
    "Plik rewizji"
  ],
  [
    "Revision tokens",
    "Tokeny rewizji"
  ],
  [
    "Save the current translation draft before clearing it from this browser? Saved drafts remain on disk.",
    "Zapisać bieżący szkic tłumaczenia przed wyczyszczeniem go z przeglądarki? Zapisane szkice pozostaną na dysku."
  ],
  [
    "Saved applied review restored",
    "Przywrócono zapisany, zweryfikowany tekst"
  ],
  [
    "Saved applied review restored.",
    "Przywrócono zapisany, zweryfikowany tekst."
  ],
  [
    "Saved applied translation review restored for this output.",
    "Przywrócono zapisane i zweryfikowane tłumaczenie tego wyniku."
  ],
  [
    "Saved applied translation review restored from disk.",
    "Przywrócono zapisane i zweryfikowane tłumaczenie z dysku."
  ],
  [
    "Saved translation draft restored for this output; preview is required again.",
    "Przywrócono szkic tłumaczenia tego wyniku; ponownie zastosuj tłumaczenie."
  ],
  [
    "Saved translation draft restored from disk; preview is required again.",
    "Przywrócono szkic tłumaczenia z dysku; ponownie zastosuj tłumaczenie."
  ],
  [
    "Undid the last current-editor change. Save before previewing.",
    "Cofnięto ostatnią zmianę w edytorze. Zapisz przed zastosowaniem tłumaczenia."
  ],
  [
    "Undo applied to the current draft. Preview again before applying.",
    "Cofnięto zmianę w szkicu. Ponownie zatwierdź tekst przed zapisaniem do eksportu."
  ],
  [
    "Unreferenced — eligible for cleanup",
    "Nieużywane — można usunąć"
  ],
  [
    "paths unavailable",
    "ścieżki niedostępne"
  ],
  [
    "this saved work state",
    "ten zapis pracy"
  ],
  [
    "· Timing unavailable",
    "· Znaczniki czasu niedostępne"
  ],
  [
    "Python version is supported.",
    "Wersja Pythona jest obsługiwana."
  ],
  [
    "Python 3.12 is required.",
    "Wymagany jest Python 3.12."
  ],
  [
    "WSL2 environment detected.",
    "Wykryto środowisko WSL2."
  ],
  [
    "WSL2 was not detected.",
    "Nie wykryto WSL2."
  ],
  [
    "Environment differs from the accepted Ubuntu 24.04 / 26.04 baselines.",
    "Środowisko różni się od obsługiwanych wersji Ubuntu 24.04 i 26.04."
  ],
  [
    "NVIDIA GPU visibility is unavailable: nvidia-smi is missing.",
    "Nie można sprawdzić karty NVIDIA: brakuje nvidia-smi."
  ],
  [
    "NVIDIA GPU query failed.",
    "Nie udało się odczytać danych karty NVIDIA."
  ],
  [
    "NVIDIA GPU query returned no usable device.",
    "Nie znaleziono dostępnej karty NVIDIA."
  ],
  [
    "NVIDIA GPU is visible.",
    "Karta NVIDIA jest widoczna."
  ],
  [
    "Unable to verify CUDA availability in PyTorch.",
    "Nie można sprawdzić dostępności CUDA w PyTorch."
  ],
  [
    "CUDA is available in PyTorch.",
    "CUDA jest dostępna w PyTorch."
  ],
  [
    "CUDA is not available in PyTorch.",
    "CUDA jest niedostępna w PyTorch."
  ],
  [
    "Speech dependency test could not finish; repair the locked environment and retry.",
    "Test zależności mowy nie zakończył się. Napraw środowisko zgodnie z plikiem blokady i spróbuj ponownie."
  ],
  [
    "Speech libraries, TorchCodec/FFmpeg and CTranslate2 CUDA load successfully.",
    "Biblioteki mowy, TorchCodec/FFmpeg oraz CTranslate2 CUDA ładują się poprawnie."
  ],
  [
    "HF_TOKEN is present.",
    "HF_TOKEN jest ustawiony."
  ],
  [
    "HF_TOKEN is missing.",
    "HF_TOKEN nie jest ustawiony."
  ],
  [
    "Run Test local dependencies first.",
    "Najpierw uruchom test lokalnych zależności."
  ],
  [
    "All active queue jobs must use the same output directory.",
    "Wszystkie aktywne zadania kolejki muszą używać tego samego katalogu wyników."
  ],
  [
    "Manual verification confirmation is required",
    "Wymagane jest potwierdzenie ręcznego sprawdzenia."
  ],
  [
    "Semantic manual verification confirmation is required",
    "Wymagane jest potwierdzenie ręcznej weryfikacji znaczenia tłumaczenia."
  ],
  [
    "Output path must be a directory",
    "Ścieżka wyników musi wskazywać katalog."
  ],
  [
    "Symbolic-link paths are not allowed",
    "Ścieżki będące dowiązaniami symbolicznymi są niedozwolone."
  ],
  [
    "Path is inside a prohibited operating-system directory",
    "Ścieżka wskazuje chroniony katalog systemu operacyjnego."
  ],
  [
    "Enter one non-empty API key without whitespace.",
    "Podaj jeden niepusty klucz API bez białych znaków."
  ],
  [
    "No desktop folder dialog is available. Enter the output directory path directly.",
    "Systemowe okno wyboru katalogu jest niedostępne. Wpisz ścieżkę katalogu wyników bezpośrednio."
  ]
]) guiPolish.set(en, pl);
for (const [code, description] of [
  [
    "GUI_REVIEW_ACTIVE",
    "Najpierw wyczyść bieżący tekst, aby otworzyć inny przegląd."
  ],
  [
    "GUI_REVIEW_ACTIVE_CHANGED",
    "Aktywny przegląd zmienił się podczas zapisu. Otwórz ponownie wybrane nagranie."
  ],
  [
    "GUI_REVIEW_CURSOR_BOUNDARY",
    "Umieść kursor między całymi słowami. Po obu stronach musi pozostać tekst. Dla zaznaczenia użyj wydzielenia tekstu."
  ],
  [
    "GUI_REVIEW_SELECTION_REQUIRED",
    "Zaznacz całe słowo, kilka słów lub zdanie przed wydzieleniem tekstu."
  ],
  [
    "GUI_REVIEW_SESSION_INPUT_REQUIRED",
    "Najpierw wybierz wynik transkrypcji i katalog zapisu przeglądu."
  ],
  [
    "GUI_REVIEW_STRUCTURE_INVALID",
    "Wybrany fragment zmienił się lub jest niedostępny. Wczytaj aktualny szkic i ponów operację."
  ],
  [
    "GUI_WORKSPACE_REVIEW_SAVE_FAILED",
    "Nie udało się zapisać otwartego szkicu. Sprawdź stan edytora przed zapisaniem obszaru pracy."
  ],
  [
    "GUI_CORRECTION_BACKEND_UNAVAILABLE",
    "API korekty nie odpowiedziało poprawnie na sprawdzenie gotowości. Sprawdź adres API i serwer."
  ],
  [
    "GUI_CORRECTION_BUSY",
    "Inna korekta jest już uruchomiona. Poczekaj na jej zakończenie."
  ],
  [
    "GUI_CORRECTION_CLOUD_OPT_IN_REQUIRED",
    "Korzystanie z OpenRouter wymaga wyraźnej zgody na wysłanie tekstu do chmury."
  ],
  [
    "GUI_CORRECTION_CONFIRMATION_REQUIRED",
    "Potwierdź zasady wysyłania tekstu do dostawcy i konieczność ręcznego sprawdzenia wstępnej korekty."
  ],
  [
    "GUI_CORRECTION_CREDENTIAL_MISSING",
    "Brakuje klucza API OpenRouter w bieżącej sesji GUI."
  ],
  [
    "GUI_CORRECTION_CREDENTIAL_REJECTED",
    "Połączenie z dostawcą działa, ale klucz API nie został poprawnie zweryfikowany."
  ],
  [
    "GUI_CORRECTION_DICTIONARY_INVALID",
    "Wybrany projekt nie pasuje do słownika. Sprawdź ID projektu i słownik."
  ],
  [
    "GUI_CORRECTION_MODEL_REQUIRED",
    "Wybierz lub wpisz dokładne ID modelu korekty."
  ],
  [
    "GUI_CORRECTION_MODEL_UNAVAILABLE",
    "Wybrany model korekty nie jest dostępny u dostawcy."
  ],
  [
    "GUI_CORRECTION_PROVIDER_INVALID",
    "Wybrany dostawca korekty jest nieobsługiwany."
  ],
  [
    "GUI_DICTIONARY_CATALOG_TOO_LARGE",
    "Katalog słowników zawiera ponad 1000 plików JSON. Wybierz mniejszy katalog."
  ],
  [
    "GUI_DICTIONARY_CONFLICT",
    "Propozycja słownika zmieniła się od wczytania. Wczytaj ją ponownie."
  ],
  [
    "GUI_DICTIONARY_DECISIONS_INVALID",
    "Każdy wpis propozycji musi mieć jedną prawidłową decyzję."
  ],
  [
    "GUI_DICTIONARY_ID_REQUIRED",
    "Podaj ID nowej wersji słownika."
  ],
  [
    "GUI_DICTIONARY_PROJECT_REQUIRED",
    "Podaj ID projektu słownika."
  ],
  [
    "GUI_EXPORT_COLOR_INVALID",
    "Wybierz kolor w formacie #RRGGBB dla istniejącego mówcy."
  ],
  [
    "GUI_EXPORT_FORMAT_INVALID",
    "Wybrany format eksportu jest nieobsługiwany."
  ],
  [
    "GUI_GPU_BUSY",
    "Poczekaj na zakończenie aktywnej transkrypcji przed lokalnym tłumaczeniem."
  ],
  [
    "GUI_REVIEW_CONFLICT",
    "Tekst zmienił się od wczytania. Wczytaj aktualną wersję przed zapisem."
  ],
  [
    "GUI_REVIEW_PREVIEW_REQUIRED",
    "Najpierw zatwierdź bieżący zapisany szkic, a następnie zapisz go do eksportu."
  ],
  [
    "GUI_REVIEW_RESULT_MISMATCH",
    "Zapisany przegląd należy do innego wyniku transkrypcji."
  ],
  [
    "GUI_REVIEW_SESSION_INVALID",
    "Zapis sesji przeglądu jest nieprawidłowy. Wybierz właściwy plik i źródło."
  ],
  [
    "GUI_TRANSLATION_BACKEND_UNAVAILABLE",
    "API tłumaczenia nie odpowiedziało poprawnie na sprawdzenie gotowości. Sprawdź adres API i serwer."
  ],
  [
    "GUI_TRANSLATION_BUSY",
    "Inne tłumaczenie jest już uruchomione. Poczekaj na jego zakończenie."
  ],
  [
    "GUI_TRANSLATION_CLOUD_OPT_IN_REQUIRED",
    "Korzystanie z OpenRouter wymaga wyraźnej zgody na wysłanie tekstu do chmury."
  ],
  [
    "GUI_TRANSLATION_CONFIRMATION_REQUIRED",
    "Potwierdź zasady wysyłania tekstu do API i konieczność ręcznego sprawdzenia propozycji tłumaczenia."
  ],
  [
    "GUI_TRANSLATION_CREDENTIAL_MISSING",
    "Brakuje klucza API OpenRouter w bieżącej sesji GUI."
  ],
  [
    "GUI_TRANSLATION_CREDENTIAL_REJECTED",
    "Połączenie z dostawcą działa, ale klucz API nie został poprawnie zweryfikowany."
  ],
  [
    "GUI_TRANSLATION_EXPORT_FORMAT_INVALID",
    "Wybrany format eksportu tłumaczenia jest nieobsługiwany."
  ],
  [
    "GUI_TRANSLATION_LANGUAGE_INVALID",
    "Wybierz polski lub angielski jako język docelowy."
  ],
  [
    "GUI_TRANSLATION_MODEL_REQUIRED",
    "Wybierz lub wpisz dokładne ID modelu tłumaczenia."
  ],
  [
    "GUI_TRANSLATION_MODEL_UNAVAILABLE",
    "Wybrany model tłumaczenia nie jest dostępny u dostawcy."
  ],
  [
    "GUI_TRANSLATION_OUTPUT_MODE_INVALID",
    "Wybrany tryb odpowiedzi tłumaczenia jest nieobsługiwany."
  ],
  [
    "GUI_TRANSLATION_PROVIDER_INVALID",
    "Wybrany dostawca tłumaczenia jest nieobsługiwany."
  ],
  [
    "GUI_TRANSLATION_REASONING_INVALID",
    "Limit tokenów rozumowania musi być nieujemną liczbą całkowitą."
  ],
  [
    "GUI_TRANSLATION_REQUEST_INVALID",
    "Nie udało się utworzyć propozycji tłumaczenia. Sprawdź szczegóły techniczne."
  ],
  [
    "GUI_TRANSLATION_REVIEW_CONFLICT",
    "Szkic tłumaczenia zmienił się od wczytania. Wczytaj aktualną wersję."
  ],
  [
    "GUI_TRANSLATION_REVIEW_PREVIEW_REQUIRED",
    "Ponownie zastosuj zapisany szkic z bieżącym ustawieniem pustych jednostek przed zapisaniem do eksportu."
  ],
  [
    "GUI_TRANSLATION_REVIEW_STRUCTURE_INVALID",
    "Nie można zmieniać tożsamości jednostek tłumaczenia. Wczytaj prawidłowy szkic."
  ],
  [
    "GUI_TRANSLATION_REVIEW_TARGET_REQUIRED",
    "Wybierz polski lub angielski przed otwarciem ręcznego tłumaczenia."
  ]
]) guiPolishErrorDescriptions.set(code, description);

for (const [en, pl] of [
  ["verified", "zweryfikowane"], ["Passed", "Poprawne"], ["None — preview only", "Brak — tylko sprawdzenie"],
  ["Saved applied review restored from disk", "Przywrócono zweryfikowany tekst z dysku"],
  ["Saved applied review restored from workspace", "Przywrócono zweryfikowany tekst z zapisu pracy"],
  ["Saved review for this output restored.", "Przywrócono zapisany tekst tego wyniku."],
  ["Saved review restored from disk; preview is required again", "Przywrócono tekst z dysku; ponownie zatwierdź tekst"],
  ["Saved review restored from workspace; preview is required again", "Przywrócono tekst z zapisu pracy; ponownie zatwierdź tekst"],
  ["Saved review restored; preview is required again", "Przywrócono tekst; ponownie go zatwierdź"],
  ["Selected text isolated. Choose its speaker, then save the draft.", "Wydzielono zaznaczony tekst. Wybierz mówcę i zapisz szkic."],
  ["Failed to fetch", "Nie udało się połączyć z lokalnym serwerem."],
  ["Dictionary changed; refresh the library before removing it", "Słownik zmienił się. Odśwież bibliotekę przed usunięciem z listy."],
  ["Dictionary changed; reopen it before saving a new version", "Słownik zmienił się. Wczytaj go ponownie przed zapisem nowej wersji."],
  ["An edited edition must keep the dictionary kind", "Nowa wersja musi zachować rodzaj słownika."],
  ["Use a new dictionary ID for this version; existing editions are immutable", "Podaj nowe ID wersji słownika. Istniejących wersji nie można nadpisywać."],
  ["Translation dictionary languages must differ", "Języki źródłowy i docelowy słownika muszą się różnić."],
  ["That dictionary ID already exists; choose a new version ID", "To ID słownika już istnieje. Podaj ID nowej wersji."],
  ["Dictionary edit provenance conflict", "Wykryto konflikt pochodzenia edycji słownika."],
  ["Profile name must contain 1–80 printable characters", "Nazwa profilu musi zawierać od 1 do 80 widocznych znaków."],
  ["Use a custom name to preserve configured profiles", "Podaj własną nazwę, aby zachować skonfigurowane profile."],
  ["A profile needs 1–32 colors in #RRGGBB format", "Profil wymaga od 1 do 32 kolorów w formacie #RRGGBB."],
  ["Dictionary document must be a JSON object", "Dokument słownika musi być obiektem JSON."],
  ["Dictionary publication confirmation is required", "Potwierdź sprawdzenie słownika przed zapisaniem wersji."],
  ["Profile colors must be an array of strings", "Kolory profilu muszą stanowić listę wartości tekstowych."],
  ["Workspace name must contain 1 to 100 characters", "Nazwa zapisu pracy musi zawierać od 1 do 100 znaków."],
  ["The selected file size is invalid or exceeds the 16 GiB local limit.", "Rozmiar pliku jest nieprawidłowy lub przekracza lokalny limit 16 GiB."],
  ["This input is already staged, queued, or running.", "Ten plik jest już dodany do kolejki lub przetwarzany."],
  ["This selected audio is already staged or running", "Ten plik audio jest już dodany do kolejki lub przetwarzany."],
  ["A grouped source is already staged or running", "Jedna ze ścieżek nagrania jest już dodana do kolejki lub przetwarzana."],
  ["The staged source changed after dry-run. Inspect and stage the current file again.", "Plik źródłowy zmienił się po zaplanowaniu. Sprawdź go i ponownie dodaj do kolejki."],
  ["The selected audio changed since the reviewed dry-run", "Wybrany plik audio zmienił się od sprawdzenia planu."],
  ["A grouped source changed after dry-run", "Jedna ze ścieżek nagrania zmieniła się po zaplanowaniu."],
  ["No saved GUI review session exists under this output root.", "Brak zapisanego przeglądu GUI w tym katalogu wyników."],
  ["Saved workspace does not exist", "Zapisany obszar pracy nie istnieje."],
  ["Saved workspace is invalid", "Zapisany obszar pracy jest nieprawidłowy."],
  ["Speaker count must be auto or an integer from 1 to 6", "Wybierz wykrywanie automatyczne lub liczbę mówców od 1 do 6."],
  ["Language must be pl, en, or auto", "Język musi mieć wartość pl, en lub auto."],
  ["Queued or running transcription jobs cannot be removed", "Nie można usuwać zadań oczekujących na przetwarzanie lub będących w trakcie przetwarzania."],
  ["Stop or finish active transcription jobs before clearing state", "Przed wyczyszczeniem stanu zakończ aktywną transkrypcję."],
]) guiPolish.set(en, pl);



function guiPolishFallbackError(code) {
  if (/REQUIRED|CONFIRMATION/.test(code)) return "Uzupełnij wymagane dane i potwierdzenia przed ponowieniem operacji. Szczegóły są w komunikacie technicznym.";
  if (/BUSY|ACTIVE/.test(code)) return "Poczekaj na zakończenie aktywnej operacji i spróbuj ponownie. Szczegóły są w komunikacie technicznym.";
  if (/INVALID|MISMATCH|CONFLICT/.test(code)) return "Dane lub zapisany stan wymagają sprawdzenia. Wczytaj aktualne źródło i popraw ustawienia. Szczegóły są w komunikacie technicznym.";
  return "Nie udało się wykonać operacji. Sprawdź komunikat techniczny z dokładną przyczyną i ponów operację po usunięciu problemu.";
}
const guiErrorDiagnostics = new Map();
function clearStaleGuiErrorDiagnostics() {
  for (const [host, details] of guiErrorDiagnostics) {
    if (!host.isConnected || !guiDiagnosticPattern.test(host.textContent.trim())) {
      details.remove(); guiErrorDiagnostics.delete(host);
    }
  }
}
function retainGuiErrorDiagnostic(node, source) {
  const host = node.parentElement;
  if (!host.matches('[role="status"], #review-status, #translation-review-status')) return;
  const coded = guiDiagnosticPattern.test(source.trim());
  let details = guiErrorDiagnostics.get(host);
  if (!coded) { if (details) { details.remove(); guiErrorDiagnostics.delete(host); } return; }
  if (!details) {
    details = document.createElement("details"); details.className = "gui-error-diagnostic";
    const summary = document.createElement("summary"); summary.textContent = "Original technical message";
    details.append(summary, document.createElement("pre")); host.after(details); guiErrorDiagnostics.set(host, details);
  }
  if (details.querySelector("pre").textContent !== source) details.querySelector("pre").textContent = source;
}
guiPolish.set("Original technical message", "Oryginalny komunikat techniczny");

for (const [en, pl] of [
  ["Session file", "Plik sesji"], ["Show fewer occurrences", "Pokaż mniej wystąpień"],
  ["Source tokens", "Tokeny źródła"], ["Target tokens", "Tokeny tłumaczenia"], ["Speaker changes", "Zmiany mówcy"],
  ["The first block in a transcript section has no previous block to merge with.", "Pierwszy fragment sekcji nie ma poprzedniego fragmentu, z którym można go połączyć."],
  ["This saved workspace references unavailable paths. It can still be removed or overwritten.", "Ten zapis pracy wskazuje niedostępne ścieżki. Nadal można go usunąć lub zastąpić nowym zapisem."],
]) guiPolish.set(en, pl);

for (const [en, pl] of [
  ["Language selection information", "Informacja o wyborze języka"],
  ["Choosing EN for Polish recordings has sometimes produced readable English text. This is not a guaranteed translation mode; the result still needs review and correction.", "Wybranie EN dla polskiego nagrania czasem dawało sensowny tekst po angielsku. To nie jest gwarantowany tryb tłumaczenia — wynik nadal wymaga sprawdzenia i korekty."],
  ["Confirm that you manually verified the text before saving and preparing for export.", "Zaznacz „Ręcznie sprawdziłem treść…” przed zapisaniem i przygotowaniem do eksportu."],
  ["Confirm that you manually verified the translation before saving and preparing for export.", "Zaznacz potwierdzenie ręcznej weryfikacji tłumaczenia przed zapisaniem i przygotowaniem do eksportu."],
]) guiPolish.set(en, pl);

guiPolish.set("Manual verification confirmed. Save and prepare for export when ready.", "Potwierdzono ręczną weryfikację. Możesz zapisać i przygotować do eksportu.");

for (const [en, pl] of [
  ["Recording audio", "Odsłuch nagrania"],
  ["Audio source", "Źródło dźwięku"],
  ["Reload recording audio", "Wczytaj ponownie dźwięk nagrania"],
  ["Preparing recording audio…", "Przygotowywanie dźwięku nagrania…"],
  ["Go to this fragment", "Przejdź do tego fragmentu"],
  ["Audio ready. Use Go to this fragment to listen while reviewing.", "Dźwięk jest gotowy. Użyj „Przejdź do tego fragmentu”, aby odsłuchać sprawdzany tekst."],
  ["Audio playback is unavailable. Restore the original recording and reload audio.", "Odsłuch jest niedostępny. Przywróć oryginalne nagranie i ponownie wczytaj dźwięk."],
  ["Playing from the nearest known source timestamp; edited text has no exact audio boundary.", "Odsłuch od najbliższego znanego czasu źródła; zmieniony tekst nie ma dokładnej granicy w nagraniu."],
  ["Playing from this fragment's source timestamp.", "Odsłuch od początku tego fragmentu w nagraniu źródłowym."],
  ["Press Play in the recording audio player.", "Naciśnij odtwarzanie w odtwarzaczu nagrania."],
  ["Choose an audio source from the current recording.", "Wybierz źródło dźwięku bieżącego nagrania."],
  ["The recording source differs from its transcription. Restore the original file before playback.", "Plik nagrania różni się od źródła transkrypcji. Przywróć oryginalny plik przed odsłuchem."],
  ["The recording source changed while preparing playback.", "Plik nagrania zmienił się podczas przygotowywania odsłuchu."],
  ["The original recording is unavailable. Restore it at its original location, then reload recording audio. Transcript editing remains available.", "Oryginalne nagranie jest niedostępne. Przywróć je w pierwotnej lokalizacji i ponownie wczytaj dźwięk. Nadal możesz edytować transkrypcję."],
  ["Choose an existing transcript section.", "Wybierz istniejącą sekcję transkrypcji."],
  ["Choose an existing transcript block.", "Wybierz istniejący fragment transkrypcji."],
  ["Transcript section has invalid source anchors.", "Sekcja transkrypcji ma nieprawidłowe odwołania do źródła."],
  ["Choose audio or video files…", "Wybierz pliki audio lub wideo…"],
  ["Add audio or video files…", "Dodaj pliki audio lub wideo…"],
  ["Choose existing audio or video files with the browser's native picker.", "Wybierz pliki audio lub wideo w oknie wyboru plików przeglądarki."],
]) guiPolish.set(en, pl);
guiPolishErrorDescriptions.set("NO_AUDIO_STREAM", "Plik nie ma ścieżki audio. Wybierz nagranie zawierające dźwięk.");
guiPolishErrorDescriptions.set("MULTIPLE_AUDIO_STREAMS", "Plik ma kilka ścieżek audio. Wyeksportuj wybraną ścieżkę do osobnego pliku, a następnie sprawdź go i przetwórz.");

for (const [en, pl] of [
  [
    "Complete episode (mixed audio)",
    "Cały odcinek (wspólny odsłuch)"
  ],
  [
    "Inspecting recording",
    "Sprawdzanie nagrania"
  ],
  [
    "Planning outputs",
    "Planowanie wyników"
  ],
  [
    "Preparing audio",
    "Przygotowywanie dźwięku"
  ],
  [
    "Transcribing",
    "Transkrypcja"
  ],
  [
    "Aligning words",
    "Dopasowywanie czasów słów"
  ],
  [
    "Organizing transcript",
    "Porządkowanie transkrypcji"
  ],
  [
    "Identifying speakers",
    "Rozpoznawanie mówców"
  ],
  [
    "Assigning speakers",
    "Przypisywanie mówców"
  ],
  [
    "Combining tracks",
    "Łączenie ścieżek"
  ],
  [
    "Saving result",
    "Zapisywanie wyniku"
  ],
  [
    "Exporting files",
    "Eksportowanie plików"
  ],
  [
    "Finishing cleanup",
    "Kończenie porządkowania"
  ],
  [
    "Approximate processing progress",
    "Orientacyjny postęp przetwarzania"
  ],
  [
    "Approximate phase progress; percentages within a phase use earlier timings from this machine.",
    "Orientacyjny postęp etapów; procent wewnątrz etapu korzysta z wcześniejszych pomiarów na tym komputerze."
  ],
  [
    "Elapsed",
    "Upłynęło"
  ],
  [
    "ETA",
    "Pozostały czas"
  ],
  [
    "Taking longer than estimated",
    "Trwa dłużej niż przewidywano"
  ],
  [
    "ETA: calibrating on this machine",
    "Pozostały czas: kalibracja na tym komputerze"
  ]
]) guiPolish.set(en, pl);

guiPolish.set("FFmpeg could not mix recording audio", "FFmpeg nie mógł przygotować wspólnego odsłuchu nagrania.");
guiPolish.set("A new mix requires at least two prepared audio files", "Wspólny odsłuch wymaga co najmniej dwóch przygotowanych plików audio.");

for (const [en, pl] of [
  [
    "Episodes",
    "Odcinki"
  ],
  [
    "Files",
    "Pliki"
  ],
  [
    "Skipped",
    "Pominięte"
  ],
  [
    "Auto-detect *",
    "Wykryj automatycznie *"
  ],
  [
    "* Selected processing values: recording metadata does not provide language or speaker count. Auto-detect is a processing request, not a detected value.",
    "* Wybrane ustawienia przetwarzania: metadane nagrania nie podają języka ani liczby mówców. Wykrywanie automatyczne jest żądaniem przetwarzania, a nie rozpoznaną wartością."
  ],
  [
    "Merge with previous block",
    "Połącz z poprzednim blokiem"
  ],
  [
    "Playback speed",
    "Tempo odtwarzania"
  ],
  [
    "Sections make correction easier. Check speaker assignments carefully. Splitting a speaker block here does not determine subtitle line breaks.",
    "Podział na sekcje ułatwia korektę. Najważniejsze jest poprawne przypisanie mówców. Podział bloku mówcy na mniejsze części nie określa podziału napisów."
  ],
  [
    "ASR sentence boundaries appear incomplete. Text may be divided incorrectly; pay extra attention to punctuation and speaker assignments during correction.",
    "ASR mógł niedokładnie rozpoznać granice zdań. Tekst może być podzielony nieprawidłowo; podczas korekty zwróć szczególną uwagę na interpunkcję i przypisanie mówców."
  ],
  [
    "User preferences",
    "Preferencje użytkownika"
  ],
  [
    "Show estimated remaining time (ETA)",
    "Pokaż szacowany pozostały czas (ETA)"
  ],
  [
    "ETA is off by default. Estimates become available after 3 successful transcriptions with comparable language, models and track configuration on this computer. Timing history stays on this computer and is not transferred with a profile.",
    "ETA jest domyślnie wyłączone. Oszacowanie będzie dostępne po 3 udanych transkrypcjach z porównywalnym językiem, modelami i układem ścieżek na tym komputerze. Historia czasów pozostaje na tym komputerze i nie jest przenoszona z profilem."
  ],
  [
    "User profile",
    "Profil użytkownika"
  ],
  [
    "Profile name",
    "Nazwa profilu"
  ],
  [
    "Save profile",
    "Zapisz profil"
  ],
  [
    "Load saved profile",
    "Wczytaj zapisany profil"
  ],
  [
    "Export profile…",
    "Eksportuj profil…"
  ],
  [
    "Import profile…",
    "Importuj profil…"
  ],
  [
    "One JSON file contains preferences, current workflow settings, saved workspace manifests, custom palettes and dictionaries from the selected library and referenced workspaces. Media, transcripts, API keys, permissions and running jobs are excluded. Other workspace catalogs must be selected before saving. Referenced recordings and outputs must be transferred separately.",
    "Jeden plik JSON zawiera preferencje, bieżące ustawienia pracy, zapisy obszarów pracy, własne palety oraz słowniki z wybranej biblioteki i zapisanych obszarów pracy. Nie zawiera mediów, transkrypcji, kluczy API, zgód ani uruchomionych zadań. Inne katalogi obszarów pracy trzeba wybrać przed zapisem. Nagrania i wyniki należy przenieść osobno."
  ],
  [
    "Profile loaded. Open Saved work & cleanup to select a restored workspace. Missing recordings or outputs must be restored before loading that workspace. The active queue and editor are unchanged.",
    "Profil wczytany. W sekcji Zapisana praca i porządkowanie wybierz przywrócony obszar pracy. Brakujące nagrania i wyniki trzeba przywrócić przed jego wczytaniem. Aktywna kolejka i edytor pozostają bez zmian."
  ],
  [
    "Profile saved and exported as one JSON file.",
    "Profil zapisany i wyeksportowany jako jeden plik JSON."
  ],
  [
    "Profile saved on this computer.",
    "Profil zapisany na tym komputerze."
  ],
  [
    "Export dictionary…",
    "Eksportuj słownik…"
  ],
  [
    "Dictionary imported. Original version, hash and provenance preserved.",
    "Słownik zaimportowany. Zachowano oryginalną wersję, skrót i pochodzenie."
  ],
  [
    "Dictionary exported without changing its contents.",
    "Słownik wyeksportowany bez zmiany zawartości."
  ],
  [
    "No user profile has been saved on this computer",
    "Na tym komputerze nie zapisano jeszcze profilu użytkownika"
  ],
  [
    "User profile exceeds the 16 MiB limit",
    "Profil użytkownika przekracza limit 16 MiB"
  ],
  [
    "That dictionary ID already exists with different content; import into another directory or create a new version",
    "Słownik z tym ID ma już inną zawartość. Zaimportuj go do innego katalogu lub utwórz nową wersję."
  ]
]) guiPolish.set(en, pl);
guiPolishErrorDescriptions.set("GUI_BATCH_CHANGED", "Lista plików lub ustawienia zmieniły się podczas planowania. Sprawdź i zaplanuj bieżącą listę ponownie.");
guiPolishErrorDescriptions.set("GUI_PROFILE_INVALID", "Nie udało się zapisać lub wczytać profilu. Sprawdź poprawność pliku, ścieżki i dostępność biblioteki słowników.");
guiPolishErrorDescriptions.set("GUI_DICTIONARY_SELECTION_REQUIRED", "Przed eksportem wybierz słownik z listy.");

for (const [en, pl] of [
  ["Profile API endpoints must not contain credentials", "Adresy API w profilu nie mogą zawierać danych dostępowych. Użyj okna klucza API dla bieżącej sesji."],
  ["User profile contains invalid or unsupported settings", "Profil zawiera nieprawidłowe lub nieobsługiwane ustawienia."],
  ["Dictionary document does not match a supported dictionary format", "Plik nie jest zgodny z obsługiwanym formatem słownika."]
]) guiPolish.set(en, pl);

for (const [en, pl] of [
  ["Auto-detect **", "Wykryj automatycznie **"],
  ["* Recording language: selected processing value because media metadata does not provide it. Auto-detect requests detection during processing.", "* Język nagrania: wybrana wartość, ponieważ metadane pliku jej nie podają. Opcja automatyczna oznacza wykrywanie podczas przetwarzania."],
  ["** Number of speakers: selected processing value because media metadata does not provide it. Auto-detect requests detection during processing.", "** Liczba mówców: wybrana wartość, ponieważ metadane pliku jej nie podają. Opcja automatyczna oznacza wykrywanie podczas przetwarzania."]
]) guiPolish.set(en, pl);

// Package A maintenance and artifact download copy.
for (const [en, pl] of [
  [
    "Cancel task",
    "Anuluj zadanie"
  ],
  [
    "Retry from beginning",
    "Ponów od początku"
  ],
  [
    "Cancellation requested…",
    "Oczekiwanie na anulowanie…"
  ],
  [
    "CANCEL_REQUESTED",
    "OCZEKIWANIE NA ANULOWANIE"
  ],
  [
    "CANCELLED",
    "ANULOWANO"
  ],
  [
    "Cancelled",
    "Anulowane"
  ],
  [
    "Failed",
    "Błąd"
  ],
  [
    "Active",
    "W toku"
  ],
  [
    "Interrupted",
    "Przerwane"
  ],
  [
    "Stage a fresh attempt with the same settings. Source hashes are checked again.",
    "Przygotuj nową próbę z tymi samymi ustawieniami. Pliki wejściowe zostaną ponownie sprawdzone."
  ],
  [
    "Cancellation waits for the current processing stage to return. Final publication cannot be cancelled.",
    "Anulowanie nastąpi po zakończeniu bieżącego etapu przetwarzania. Publikacji końcowej nie można anulować."
  ],
  [
    "Temporary work directories",
    "Katalogi plików tymczasowych"
  ],
  [
    "Only the configured temporary root is inspected. Active jobs, referenced paths, legacy workdirs and unknown artifacts are protected. References cover the current queue and the default and selected workspace catalogs; check other catalogs separately.",
    "Sprawdzany jest tylko skonfigurowany katalog tymczasowy. Aktywne zadania, używane ścieżki, starsze katalogi i nieznane pliki są chronione. Sprawdzane są odwołania w bieżącej kolejce oraz domyślnym i wybranym katalogu obszarów roboczych; pozostałe katalogi sprawdź osobno."
  ],
  [
    "Retention reason",
    "Powód zachowania"
  ],
  [
    "All",
    "Wszystkie"
  ],
  [
    "Successful, retained",
    "Ukończone, zachowane"
  ],
  [
    "Minimum age (days)",
    "Minimalny wiek (dni)"
  ],
  [
    "Refresh temporary inventory",
    "Odśwież listę katalogów tymczasowych"
  ],
  [
    "Preview cleanup",
    "Podgląd usuwania"
  ],
  [
    "Confirm deletion",
    "Potwierdź usunięcie"
  ],
  [
    "Legacy: creation time unknown",
    "Starszy katalog: nieznany czas utworzenia"
  ],
  [
    "Active — protected",
    "Aktywne — chronione"
  ],
  [
    "Referenced — protected",
    "W użyciu — chronione"
  ],
  [
    "Legacy owner unknown — protected",
    "Nieznany właściciel starszego katalogu — chronione"
  ],
  [
    "Unknown artifact — protected",
    "Nieznany plik — chronione"
  ],
  [
    "Unsafe entry — protected",
    "Niebezpieczna ścieżka — chronione"
  ],
  [
    "Select unprotected temporary directories, then preview cleanup.",
    "Wybierz niechronione katalogi tymczasowe, a następnie sprawdź podgląd usuwania."
  ],
  [
    "No temporary work directories match these filters.",
    "Brak katalogów tymczasowych pasujących do filtrów."
  ],
  [
    "Existing export downloads",
    "Pobieranie zapisanych eksportów"
  ],
  [
    "Refresh existing exports",
    "Odśwież zapisane eksporty"
  ],
  [
    "Download the exact published file. Refreshing checks existing artifacts and does not run transcription or create exports.",
    "Pobierz dokładnie zapisany plik. Odświeżanie sprawdza istniejące pliki bez uruchamiania transkrypcji i tworzenia eksportów."
  ],
  [
    "Verified existing exports are ready to download.",
    "Sprawdzone eksporty są gotowe do pobrania."
  ],
  [
    "Some published exports are missing or changed and cannot be downloaded.",
    "Niektórych eksportów brakuje lub zmieniono je; nie można ich pobrać."
  ],
  [
    "No verified exports found for this applied version. Export it first. Legacy exports with a custom palette may require their original settings.",
    "Brak sprawdzonych eksportów tej zapisanej wersji. Najpierw wykonaj eksport. Starsze eksporty z własną paletą mogą wymagać pierwotnych ustawień."
  ],
  [
    "Queue job does not exist",
    "Zadanie nie istnieje w kolejce"
  ],
  [
    "Final publication has started; this job can no longer be cancelled",
    "Rozpoczęła się publikacja końcowa; tego zadania nie można już anulować"
  ],
  [
    "Only waiting or running jobs can be cancelled",
    "Można anulować tylko zadania oczekujące lub przetwarzane"
  ],
  [
    "Only failed or cancelled jobs can be retried",
    "Można ponowić tylko zadania zakończone błędem lub anulowane"
  ],
  [
    "This recording already has an active attempt",
    "To nagranie ma już aktywną próbę przetwarzania"
  ],
  [
    "Select temporary work directories to preview",
    "Wybierz katalogi tymczasowe do podglądu usuwania"
  ],
  [
    "Selected work directory is unavailable or protected",
    "Wybrany katalog jest niedostępny lub chroniony"
  ],
  [
    "Selected work directory became protected",
    "Wybrany katalog został objęty ochroną"
  ],
  [
    "Cleanup preview expired; preview the selection again",
    "Podgląd usuwania wygasł; sprawdź wybrane katalogi ponownie"
  ],
  [
    "A work directory changed after preview; refresh and preview again",
    "Katalog zmienił się od podglądu; odśwież listę i sprawdź podgląd ponownie"
  ],
  [
    "A work directory changed or became protected after preview",
    "Katalog zmienił się lub został objęty ochroną po podglądzie"
  ],
  [
    "Preview and confirm temporary work directory cleanup",
    "Sprawdź podgląd i potwierdź usuwanie katalogów tymczasowych"
  ],
  [
    "older_than_days must not be negative",
    "Minimalny wiek katalogów nie może być ujemny"
  ],
  [
    "Choose an applied manual revision before downloading exports",
    "Wybierz zapisaną ręcznie zweryfikowaną wersję przed pobraniem eksportów"
  ],
  [
    "Only manually verified revision exports can be downloaded",
    "Można pobierać tylko eksporty ręcznie zweryfikowanych wersji"
  ],
  [
    "Choose a verified manual translation of this canonical result",
    "Wybierz ręcznie zweryfikowane tłumaczenie tego wyniku"
  ],
  [
    "Translation revision identity differs from the selected revision",
    "Tłumaczenie odnosi się do innej wersji źródła niż wybrana"
  ],
  [
    "Symbolic-link export paths are not allowed",
    "Ścieżki eksportów z dowiązaniami symbolicznymi są niedozwolone"
  ],
  [
    "Export download registry is invalid",
    "Rejestr pobierania eksportów jest nieprawidłowy"
  ],
  [
    "Published export identity changed; download registration rejected",
    "Tożsamość zapisanego eksportu zmieniła się; odmówiono rejestracji pobierania"
  ],
  [
    "Download is unavailable or changed. Refresh existing exports.",
    "Plik jest niedostępny lub zmieniony. Odśwież zapisane eksporty."
  ],
  [
    "Export download registry is full",
    "Rejestr pobierania eksportów jest pełny"
  ],
  [
    "Export file is not a bounded regular file",
    "Plik eksportu jest zbyt duży lub nie jest zwykłym plikiem"
  ],
  [
    "Export file is too large",
    "Plik eksportu jest zbyt duży"
  ]
]) guiPolish.set(en, pl);

guiPolish.set("Minimum age must be a whole number between 0 and 36500", "Minimalny wiek musi być liczbą całkowitą od 0 do 36500");

guiPolish.set("Current workspace fields are invalid", "Bieżące pola obszaru roboczego są nieprawidłowe");

guiPolish.set("CANCELLATION REQUESTED", "OCZEKIWANIE NA ANULOWANIE");

// Owner package-A acceptance corrections.
for (const [en, pl] of [
  [
    "Retry",
    "Ponów"
  ],
  [
    "ASR completed",
    "ASR ukończony"
  ],
  [
    "Workflow completed",
    "Całe zadanie ukończone"
  ],
  [
    "Next step: transcription",
    "Następny krok: transkrypcja"
  ],
  [
    "Loading",
    "Wczytywanie"
  ],
  [
    "Restoring saved queue and editors…",
    "Przywracanie zapisanej kolejki i edycji…"
  ],
  [
    "Wait until saved work is fully restored. Transcription does not start automatically.",
    "Poczekaj na pełne przywrócenie pracy. Transkrypcja nie uruchomi się automatycznie."
  ],
  [
    "Selected for planning",
    "Wybrano do planowania"
  ],
  [
    "Media copied locally. Plan processing, review and confirm the plan, then start the queue. Copies become durable only when staged.",
    "Pliki skopiowano lokalnie. Zaplanuj przetwarzanie, sprawdź i potwierdź plan, a następnie uruchom kolejkę. Kopie zostają zachowane po dodaniu do kolejki."
  ],
  [
    "Only the configured temporary root is inspected. Active jobs, referenced paths, legacy workdirs and unknown artifacts are protected. Durable media copies are separate; use Managed source copies to remove unreferenced sources. References cover the current queue and the default and selected workspace catalogs; check other catalogs separately.",
    "Sprawdzany jest tylko skonfigurowany katalog tymczasowy. Aktywne zadania, używane ścieżki, starsze katalogi i nieznane pliki są chronione. Trwałe kopie nagrań są osobne; nieużywane kopie usuwa się w sekcji Zarządzane kopie plików źródłowych. Sprawdzane są odwołania w bieżącej kolejce oraz domyślnym i wybranym katalogu obszarów roboczych; pozostałe katalogi sprawdź osobno."
  ],
  [
    "Saved work is already being restored",
    "Trwa już przywracanie zapisanej pracy"
  ],
  [
    "Saved-work restore identity is invalid",
    "Identyfikator przywracania pracy jest nieprawidłowy"
  ],
  [
    "Saved file reference is invalid",
    "Zapisana ścieżka pliku jest nieprawidłowa"
  ],
  [
    "Saved file reference must not be a directory",
    "Zapisana ścieżka pliku nie może wskazywać katalogu"
  ]
]) guiPolish.set(en, pl);

guiPolish.set("Saving current work…", "Zapisywanie bieżącej pracy…");
guiPolish.set("Restoring saved work…", "Przywracanie zapisanej pracy…");

guiPolish.set("Refreshing temporary inventory…", "Odświeżanie listy katalogów tymczasowych…");
