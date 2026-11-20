# Package A owner acceptance checklist

Current owner-feedback retest: [focused follow-up](GUI_PACKAGE_A_RETEST.md).

Date: 2026-11-20. Scope: A1 recovery, A2 cancellation/retry, A3 temporary-workdir maintenance,
A4 existing-export downloads. Package B stays gated on this checklist and fixes/retest acceptance.
Use your working WSL installation and disposable recordings/output for cancellation tests. Existing
owner-qualified transcription, MP4, mixed playback and local export results remain accepted.
There is no API/provider step, paid call, new model download or artist-package action in this test.

Record: commit (`git rev-parse --short HEAD`), Ubuntu/Python/browser versions, EN or PL interface,
GPU, output root and workspace catalog/name. Mark each case PASS / FAIL / NOT RUN. For a failure,
record the case ID, clicks, diagnostic code and small relevant terminal excerpt. Do not attach keys,
private transcript content or full profiles to public issues.

## Start

1. Pull the delivered main branch in the WSL checkout using your normal update procedure.
2. Start `uv run --locked transcriber gui`. Confirm the GUI opens.
3. Use a new output root for disposable ASR/cancellation attempts. Keep your existing outputs.
4. Optional: run Test local dependencies if the environment changed. No dependency repair is
   required merely for testing this package.

## A1 — full restart recovery

- [ ] A1.1 Open an existing completed canonical result and stage another disposable recording
  without starting it. Edit and save a source-review draft. Note the exact recording and wording.
- [ ] A1.2 Apply an explicitly manually verified source revision and export two chosen formats.
  Prepare/save a manual translation; apply/export it after semantic verification. No LLM is needed.
  Note the source revision and translation filenames, and the current selected recording.
- [ ] A1.3 Save current work state under a recognizable name. Note its catalog. Stop the server,
  restart it, and load that workspace from Saved work & cleanup. Check queue identities, saved
  source/translation wording, applied pointers and export availability. No ASR starts on load.
  Human verification/disclosure boxes stay unset, and any session API key stays absent.
- [ ] A1.4 Optional, disposable copy only: move original media after completed ASR, save/reload the
  completed workspace. Review/export should recover while playback honestly needs its original
  media. Restore the media afterwards. Staged work and actual retries still require their input; failed/cancelled terminal history can load without it.

## A2 — cancellation and retry

- [ ] A2.1 Stage two disposable episodes. Start the queue and cancel the waiting second row.
  It should become Cancelled without loading its speech models; the first continues.
- [ ] A2.2 Cancel the running first row during ASR/alignment/diarization. A request may remain
  pending until the current native call returns. Wait for Cancelled; the UI/server should remain
  usable. The cancelled attempt must not publish a partial canonical result or derived export.
  Cancellation requested just after publication begins may be refused: the completed publication
  remains valid. Do not expect forced GPU/thread termination or instant cancellation.
- [ ] A2.3 Choose Retry from beginning on a cancelled/failed row. A fresh staged attempt appears;
  Start queue enables and processes it from the beginning. The selected old terminal row is replaced; its retained files remain. Completed ASR from other rows must not run again.
- [ ] A2.4 Save/restart/load after cancellation. Cancelled history should remain terminal, not
  resume itself. Optional disposable negative case: change a staged source before starting;
  hash mismatch must reject it and require a new Inspect/Dry-run/confirmation.

## A3 — temporary-workdir maintenance

- [ ] A3.1 In Settings & About open Temporary work directories and Refresh temporary inventory.
  Check reason/creation time/size for retained cancellation/failure work. Default successful work
  is normally deleted; successful-retained appears only when configured to keep successful work.
- [ ] A3.2 Check reason and minimum-age filters (0 days includes fresh retained work). Active
  owners, referenced paths, unknown/final artifacts and legacy workdirs must be protected. Legacy
  creation time is unknown; interrupted identifies a dead owner, not a completed task.
- [ ] A3.3 Select only a disposable, unprotected cancelled/failed workdir. Preview cleanup must
  show its exact count/size before deletion. Confirm deletion; that workdir disappears while source
  files, output publications, models and other workdirs remain. A changed/expired preview must
  require refresh/preview again. Do not move real publications into workdirs for this test.
- [ ] A3.4 If custom workspace catalogs are used, select the relevant one before maintenance.
  The current queue plus default/selected catalogs are checked; other catalogs must be checked
  separately. This maintenance panel is distinct from durable managed-source copy cleanup.

## A4 — download existing exports

- [ ] A4.1 In source review/export open Existing export downloads and refresh. Click the exact
  TXT/subtitle filename(s). Browser downloads must match the existing disk files and version names.
  If useful compare `sha256sum <original-file> <downloaded-file>` in WSL; the UI also shows SHA-256.
- [ ] A4.2 Export another palette/version, then refresh. Older registered versions should remain
  separately downloadable and unchanged. No ASR should run during export or download.
- [ ] A4.3 Repeat from translation review/export, including one subtitle and its provenance JSON.
  Restart/load saved work again and refresh both download lists; downloading must work without
  regenerating candidates or re-exporting. Old session links expire; refresh obtains new ones.
- [ ] A4.4 A missing/changed registered export should be withheld, never silently regenerated.
  This negative case is automated; there is no need to alter real published files manually.
  Older pre-registry custom-palette exports may require their original settings for read-only
  verification. Raw/LLM candidate artifacts and arbitrary filesystem paths are not download targets.

## Finish

- [ ] Check new controls in the preferred locale/theme and half-screen view. Report any untranslated
  new control/message or overlap. The complete terminology approval remains task 10 after features.
- [ ] Report case IDs/results and any limitations. Stop before package B until fixes pass and you
  explicitly accept progression. Full profile transfer/native Windows/GPU hardware qualification
  are not established by the model-free VM checks recorded below.

## Agent verification record

Fill final counts/commands in the [package checkpoint](../docs/checkpoints/2026-11-20-package-a.md).
Coverage includes regression/unit tests, actual FFmpeg with fake speech engines, real browser
workspace restart and attachment downloads, synthetic-service cancellation and temporary cleanup,
EN/PL layouts and package/resource checks. Real pinned-model cancellation on the owner's WSL/GPU
is intentionally left to A2 above. No new quality/ETA/research campaign is a completion gate.
