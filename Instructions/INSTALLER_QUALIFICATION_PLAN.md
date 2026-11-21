# Deferred installation and removal qualification

Owner decision, 2026-11-21: fresh-install/reinstall checks are not part of routine GUI-update
acceptance. Native Windows installation/model preparation/doctor already passed. Keep using that
environment. Diagnose a concrete dependency error before requesting repair or model downloads.

At the later uninstall-script milestone, prepare a dedicated disposable-machine checklist for:

- Clean native Windows 11 x64 setup, using [the existing setup instructions](WINDOWS_NATIVE.md).
- Explicit pinned-model/language-data preparation, locked runtime and dependency checks, first
  launch and a short local workflow. No model download during ordinary use.
- Uninstall with models retained, then optional removal of application-owned models. Preserve
  recordings, publications, unrelated/shared caches and other applications' runtimes.
- Reinstall after those removals, with retained/removed models handled explicitly.

At the subsequent graphical-distribution milestone, qualify the standalone EXE installer without
a repository checkout, desktop shortcut, Add/Remove Programs entry, graphical uninstaller and
upgrade behavior. No installer/uninstaller is implemented or qualified by this document.
