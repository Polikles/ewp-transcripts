# Package A closure and B preparation

Date: 2026-11-21. Baseline: clean main edda543.

The owner passed the complete focused A retest and accepts the package. One final source-review
layout adjustment is authorized without another owner retest. No B product implementation,
provider/media upload or spending is part of this closure task.

## Tasks

- [x] Remove the redundant Prepare text for review button in source-review step 4; opening source
  review/export must still prepare/load the editable draft.
- [x] Merge the two action columns: Undo, Redo, Save draft, Restore saved draft in the first row;
  Apply and Clear current draft in the second row. Keep EN/PL names coherent.
- [x] Verify the changed UI and run make check. Preserve revision/confirmation/publication behavior.
- [x] Close A in TODO/roadmap/policy/status, commit/push and leave B preparation as the resume point.

## Evidence / resume

The redundant button is removed, rather than hidden. Correction-candidate opening now calls the
preparation function directly; queue opening still prepares/restores automatically. The single
bordered panel contains the requested two ordered rows, wrapping on narrow mobile viewports.
Restore saved draft / Przywróć zapisany szkic and Clear current draft / Wyczyść bieżący szkic are
coherent in EN/PL. Required revision confirmation and immutable publication behavior are unchanged.
Minimal affected guide text and packaged mirrors are current; full manuals remain deferred.

- make check PASS: Ruff/format, mypy 106 source files, **928 tests**.
- Optional browser-helper Ruff/format PASS.
- Chromium 159.0.8154.6 / Playwright 1.65.2: **24** EN/PL × light/dark ×
  1920/1440/960/900/768/390 viewport checks. Single panel, ordered rows, no page overflow or
  feedback overlap. First four buttons share one row at desktop/half-screen widths.
- Real synthetic queue opening, Undo/Redo, Save draft, Apply/validation, Clear/Restore and opening
  a deterministic mock correction candidate all pass, including exact candidate-parent provenance.
  Custom gear hooks also pass. Zero page errors or external browser requests.
- No pipeline/filesystem/FFmpeg/ML changes; no new GPU, provider or native-Windows qualification.
  Integration/model checks were not repeated for this frontend-only adjustment. Existing accepted
  WSL, cancellation, cleanup, player, recovery and download evidence remains accepted.
- Artist ZIP SHA-256 is unchanged:
  1265a795495f37dd0e18b88d57a80bee502dbb707e55289a55551f17b451f6f1.

Package A is closed; no further owner retest is required. Next: prepare B5. Target/execution is
confirmed by the owner: Windows 11 x64; agent implements/checks on this Linux VM and pushes to
GitHub, owner pulls/tests natively. No native Windows access is implied. B product implementation
is not part of this closure; cloud provider/model/cost/media choices remain deferred until B8a.
Final complete EN–PL terminology approval and full EN/PL manuals remain after B/feature completion.

Disposable root /tmp/ewp-a-closure.S1nioh was removed after evidence capture. Test server/browser
are closed. Screenshots, synthetic media/reviews and downloaded tools are not committed.
