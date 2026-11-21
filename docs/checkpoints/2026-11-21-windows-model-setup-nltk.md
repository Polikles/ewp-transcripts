# Windows model preparation: NLTK import security

Date 2026-11-21. Baseline 16e1099, clean main. Owner step 4 fails at `from nltk import download`
with blocked regex inside C:\Users\DS\Documents\github\ewp-transcripts\.venv. NLTK 3.10.1
in the lock treats any dependency under current working directory as unsafe, including .venv.
Reproduced on Linux using the same lock: python -P also fails. Import outside checkout succeeds.
The Ubuntu helper already invokes the NLTK downloader outside the checkout; Python helper did not.

## Plan / acceptance

- [x] Explicit language-data preparation in an isolated child using the installed interpreter,
  private neutral temp cwd and -I. Keep NLTK hook active; never set NLTK_DISABLE_IMPORT_SECURITY.
  Preserve parent cwd/config/model paths and resolve relative NLTK_DATA against caller cwd.
- [x] Error propagates clearly; --help/cancel does not import/download NLTK or any models.
- [x] Reproduce real installed NLTK import in isolated child with no downloads. Stub end-to-end
  Hugging Face/NLTK preparation and verify pins/custom directories/failure behavior.
- [x] Quality gate, necessary Windows instruction/changelog updates, cleanup, commit/push.

A remains accepted, artist ZIP frozen. Native Windows/GPU and full B workflow remain owner-run;
this task fixes the explicit preparation failure and does not claim native ASR qualification.

## Verification and handoff

Reproduced locked NLTK 3.10.1 import failure from the checkout even with -P; import outside the
checkout succeeds. Real subprocess regression imports the installed NLTK and regex successfully
with -I from the neutral temporary cwd, confirms NLTKSafeImportFinder remains active and ignores
a hostile parent PYTHONPATH. No network or model downloads in this test. Stubbed setup verifies
public snapshot IDs/revisions/target paths, failure before any HF download, no help/cancel side
effects, relative NLTK_DATA resolution, unchanged parent cwd/env and temporary-directory cleanup.

make check PASS: 987 tests, Ruff/format, mypy 114 source files. make test-integration PASS:
15 passed / 4 deselected. Explicit Ruff/format check covers scripts/setup-models.py (outside the
ordinary src gate). No changes to dependencies/lock, model pins or runtime speech adapters; no
native Windows/GPU qualification claimed. Windows guide and bundled mirror/checklist updated.

Disposable verification root /tmp/ewp-nltk-setup.AScITi removed after evidence capture. Next:
owner git pull --ff-only and rerun uv run --locked --no-sync python scripts/setup-models.py from
the same Windows checkout, then doctor and continue the existing B checklist. No reinstall is
needed for this script-only fix. Retain native acceptance as pending until owner tests it.
