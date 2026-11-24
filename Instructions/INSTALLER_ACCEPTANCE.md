# Installer0.23.0 review / Przegląd instalatora0.23.0

Owner confirms successful0.22.2 installation, desktop launch and one episode transcription.
Retain that pass. Focus this review on the new lifecycle/operation/startup behavior below.

- [ ] Location field is compact; alternate installation opens the folder picker immediately.
  Repair/Add models run host checks automatically. The disk row distinguishes full local budget
  and additional free space.
- [ ] Unchanged-model update and program-only repair need no HF/OR. Repair offers offline model
  hash checks and explicit selective download; only selected gated downloads show HF controls.
- [ ] HF info highlights on hover/focus and has a short tooltip. Larger left gear, stages,
  activity/elapsed and measured download progress are visible. Reports have dated names/entries.
- [ ] Desktop and installed-program entries show EwP artwork; program-list size includes models.
  Installed-program maintenance offers Repair/Rollback/Uninstall; uninstall.exe offers Repair/Uninstall.
- [ ] Closing then Ctrl+C stops the idle app without a traceback or nested batch-job question.
  Startup autosave restores output/pending work after restart, without automatic transcription
  or restored cloud consent. Native Windows app interface remains a later task.
- [ ] Removal cleans program/dependencies after wizard closure, preserving user work and shared
  models by default. Remove-EwP.ps1 opens without a Plan prompt; a failed cleanup retains a report.

The owner rejected0.22.0 before installation. That archive stays unchanged. Review this corrected
wizard first; do not start installation until its layout/flow is acceptable. Existing application
workflow PASS is retained. No paid API/audio request or long ASR rerun is needed.

## GUI first / Najpierw GUI

- [ ] EXE has the centered framed EwP icon in Explorer; the window/header use the same centered
  mark. Subtitle appears below EwP Transcripts in EN and PL.
- [ ] First page has language and aligned radio cards (dot/text on one center line). Choose Install/Update/Repair/Add local models/
  Rollback/Uninstall and use Next/Back: later screens visibly match that action. Close/Cancel
  before execution leaves the existing installation unchanged. Changing actions resets later
  paths/results/credentials. Maintenance detects a managed install automatically; only a missing
  installation asks for a folder. A source checkout is not a managed install.
- [ ] Step2 says Location and checks / Lokalizacja i test. Install page says Program installation folder / Folder instalacji programu; choosing a folder
  automatically shows that volume's space. Agent tests cover below/exact25GB; do not fill a disk
  solely for a manual checkbox. An empty D:\Transcripts-test-01 is valid. Program Files uses a
  dedicated subfolder; only execution may request same-account Windows elevation. No bundle/version
  ZIP picker appears.
- [ ] Check this computer / Sprawdź komputer shows CPU model, OS, disk, GPU+driver and Visual C++
  with OK states. Switch language after checking: descriptions/numbers/status remain coherent,
  without English disk phrases in PL. VC link opens Microsoft instructions without an automatic
  EXE download. It is absent before checks and after a successful VC check; missing/inconclusive
  VC results reveal it. Windows shows its release name; older/unknown versions show a warning.
- [ ] Local-model checkbox reveals four fixed checked/disabled models and space requirement.
  Clearing it hides HF/model controls; OpenRouter/review use remains available.
- [ ] A real information icon gives short account/terms/Read-token instructions and full repository link. Token modal
  masks input, checks after paste and supports manual retry. OK requires valid access; after OK
  main page only says Token valid and enables the separate terms acknowledgment.
- [ ] Optional OR modal masks/validates the key analogously. Main page only says Key valid.
  No key is required for local work. Nothing is saved in the OS store before actual installation.
- [ ] Licenses/artwork is bottom-left on every screen. Save report is immediately below technical
  details. Credits have readable paragraphs and lines. Navigation/Close is bottom-right. Escape closes credential/help windows normally.

**Next / Dalej on the models page starts the selected operation.** Token/key checks only read
access/authentication endpoints and do not send recordings. Do not paste secrets into reports.

## Only after visual approval / Dopiero po akceptacji wyglądu

1. Keep the old checkout and back up work. Stop the old GUI server. Install into a NEW empty
   managed location; the old source checkout is never adopted or deleted.
2. Check that stages/custom gear work and the chosen local/cloud mode becomes ready. Reuse cached
   models; do not remove shared models simply for a test checkbox. Complete unchanged models are
   reused without an HF prompt. HF access/terms are required only for a selected gated download.
3. Open the desktop shortcut and check About/CLI0.23.0; open one existing result/workspace.
4. Stop the managed server, try Repair and matching-version Add local models when relevant.
   Those operations must not silently upgrade an older installation. Update must be chosen explicitly.
5. Uninstall first shows its plan. Default removal preserves work/models/key and finishes locked
   file removal after Close. Optional model/key deletion is only for assets you actually want gone.

No repeated full transcription/correction/translation workflow, reinstall campaign or paid test
is required for this UI correction. Native CI previews and model-free regressions are evidence
of UI behavior, not a claim of owner Windows11/GPU installation success. The EXE is unsigned;
public release/online bootstrap activation remain separate after native installer acceptance.
