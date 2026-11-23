# Installer0.22.1 review / Przegląd instalatora0.22.1

The owner rejected0.22.0 before installation. That archive stays unchanged. Review this corrected
wizard first; do not start installation until its layout/flow is acceptable. Existing application
workflow PASS is retained. No paid API/audio request or long ASR rerun is needed.

## GUI first / Najpierw GUI

- [ ] EXE has the centered framed EwP icon in Explorer; the window/header use the same centered
  mark. Subtitle appears below EwP Transcripts in EN and PL.
- [ ] First page has language and radio actions. Choose Install/Update/Repair/Add local models/
  Rollback/Uninstall and use Next/Back: later screens visibly match that action. Close/Cancel
  before execution leaves the existing installation unchanged.
- [ ] Install page says Program installation folder / Folder instalacji programu; choosing a folder
  automatically shows that volume's space. Agent tests cover below/exact25GB; do not fill a disk
  solely for a manual checkbox. No bundle/version ZIP picker appears.
- [ ] Check this computer / Sprawdź komputer shows CPU model, OS, disk, GPU+driver and Visual C++
  with OK states. Switch language after checking: descriptions/numbers/status remain coherent,
  without English disk phrases in PL. VC link opens Microsoft instructions without an automatic
  EXE download.
- [ ] Local-model checkbox reveals four fixed checked/disabled models and space requirement.
  Clearing it hides HF/model controls; OpenRouter/review use remains available.
- [ ] (i) gives short account/terms/Read-token instructions and full repository link. Token modal
  masks input, checks after paste and supports manual retry. OK requires valid access; after OK
  main page only says Token valid and enables the separate terms acknowledgment.
- [ ] Optional OR modal masks/validates the key analogously. Main page only says Key valid.
  No key is required for local work. Nothing is saved in the OS store before actual installation.
- [ ] Licenses/artwork is bottom-left on every screen. Save report is immediately below technical
  details. Navigation/Close is bottom-right. Escape closes credential/help windows normally.

**Next / Dalej on the models page starts the selected operation.** Token/key checks only read
access/authentication endpoints and do not send recordings. Do not paste secrets into reports.

## Only after visual approval / Dopiero po akceptacji wyglądu

1. Keep the old checkout and back up work. Stop the old GUI server. Install into a NEW empty
   managed location; the old source checkout is never adopted or deleted.
2. Check that stages/custom gear work and the chosen local/cloud mode becomes ready. Reuse cached
   models; do not remove shared models simply for a test checkbox. The HF wizard requires a valid
   access check before its terms acknowledgment even when complete model files can be reused.
3. Open the desktop shortcut and check About/CLI0.22.1; open one existing result/workspace.
4. Stop the managed server, try Repair and matching-version Add local models when relevant.
   Those operations must not silently upgrade an older installation. Update must be chosen explicitly.
5. Uninstall first shows its plan. Default removal preserves work/models/key and finishes locked
   file removal after Close. Optional model/key deletion is only for assets you actually want gone.

No repeated full transcription/correction/translation workflow, reinstall campaign or paid test
is required for this UI correction. Native CI previews and model-free regressions are evidence
of UI behavior, not a claim of owner Windows11/GPU installation success. The EXE is unsigned;
public release/online bootstrap activation remain separate after native installer acceptance.
