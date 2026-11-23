# Focused managed-installer acceptance / Test instalatora zarządzanego

This checks new distribution behavior, not the already accepted long ASR/correction/export workflow.
Read [EN instructions](../docs/gui/installation.md) / [instrukcję PL](../docs/gui/pl/installation.md).
Current package: 0.22.0. Native target: Windows 11 x64; owner keeps the existing checkout until done.

## Before testing / Przed testem

1. Save a normal work checkpoint and back up outputs/hidden sources/custom workspace catalogs.
   Zapisz stan pracy i kopię wyników, ukrytych źródeł i osobnych katalogów zapisów.
2. Stop the old GUI server. Download/check the exact package with SHA256SUMS. Use a NEW empty
   managed install location. Nie wskazuj starego repozytorium jako katalogu instalacji.
3. Existing model snapshots can be reused. No paid audio/API request or model-quality benchmark is
   required. Można użyć istniejących modeli; nie trzeba płatnych wywołań ani długiej transkrypcji.

## Windows wizard / Kreator Windows

- [ ] EXE opens with version 0.22.0, readable EN/PL, framed icon, original logo and custom gear.
  Okno otwiera się, pola/przyciski są czytelne; sprawdź także połowę ekranu i skalowanie Windows.
- [ ] Host test reports disk/OS/architecture/VC++/GPU without sending audio. Select local models;
  accepted cached models can use a blank HF field. Nie wpisuj tokenu do raportu ani rozmowy.
- [ ] Optional OR key check reports readiness without audio. Installing with the field filled saves
  it only in the OS store; otherwise local install works without OR. Sprawdź, że w aplikacji da się
  użyć zapisanego klucza; samo zapisanie nie zaznacza zgody na wysłanie.
- [ ] Install to the empty managed location. Version/app doctor/media tools are ready for the chosen
  mode; source checkout and existing outputs remain intact. Zębatka/etapy działają, raport można zapisać.
- [ ] Desktop shortcut opens the GUI. About/CLI show 0.22.0. Close the server before maintenance.
  Skrót działa, „Dodaj/usuń programy” ma właściwy wpis i lokalizację.
- [ ] Open one existing canonical result/workspace and confirm files remain available. No full ASR
  rerun required solely to prove installer correctness. Wystarczy krótka kontrola istniejącej pracy.

## Maintenance / Utrzymanie

- [ ] Repair from the same bundle preserves work/models/key and retains a previous verified runtime.
  Naprawa nie powinna pobierać całych kompletnych modeli ponownie.
- [ ] While the managed GUI server runs, update/removal is blocked. After stopping, the operation
  works. Blokada nie może wymagać zamknięcia wyłącznie karty przeglądarki.
- [ ] Restore previous version works after repair/update; existing user work is unchanged.
  Nową wersję do rzeczywistej aktualizacji będzie można sprawdzić przy kolejnym buildzie.
- [ ] Uninstall first shows a plan. Default confirmation removes app/private runtime/shortcut/OS entry
  after the wizard closes, while results/workspaces/models/key remain. Sprawdź foldery po zamknięciu.
- [ ] Reinstall works. Optional model/key removal is a separate deliberate test only if you actually
  want to remove those shared assets. Nie usuwaj modeli wyłącznie dla formalnego checkboxa, jeśli
  nadal używa ich Twój stary checkout. Zamiast tego odnotuj „nie testowano — modele współdzielone”.

## Terminal / Terminal

- [ ] Downloaded Windows ZIP installs using README commands without cloning a repository or requiring
  preinstalled Python/uv. Root paths with spaces/Polish letters work.
- [ ] Ubuntu tar/terminal route is checked on the actual available host; report WSL/native Ubuntu
  explicitly. Agent's real Ubuntu VM install/update/rollback/uninstall evidence is separate from Windows 11.

Report only failing item, stage/version/platform and sanitized report. Do not paste HF/OR tokens,
private recordings/transcript content or entire unreviewed logs. Existing full-workflow PASS remains.
Public release/online download activation and code-signing are separate delivery decisions after
native acceptance; a successful compile/CI startup is not claimed as complete owner installation.
