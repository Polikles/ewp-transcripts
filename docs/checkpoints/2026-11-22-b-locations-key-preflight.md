# B recent locations, readable save files and cloud key preflight

2026-11-22. Baseline clean main 5d60f7f. Read opening TODO and WORK_POLICY after resume.
Owner confirms save/load in Desktop output folder, cloud ASR once key loaded, complete subtitle
workflow and correct queue status. Earlier failed/cancelled native retest not repeated because
old material is gone; preserve automatic qualification rather than claim owner pass.

Scope: automatic last directory/catalog recall and list refresh; workspace filenames starting
with user-supplied name while preserving UUID compatibility/safe Windows paths; key dialog action
rows/short names/secondary clear-delete/Close bottom-right; missing key rejection before cloud
queue workers begin. Supplied stack terminates at openrouter.py:274 (missing-key raise), so treat
it as one exception with call frames, not many independent errors. Verify code before concluding.

No paid calls, model changes/reinstall, artist ZIP update or final ID–EN–PL/manual generation.
Prior cloud spend remains USD0.0291461230985028369.

## Implementation and diagnosis

- Local private directory registry remembers output/optional catalog and up to 20 recent catalogs.
  Safe existing locations reappear at startup and list refresh is automatic. Recall leaves a user's
  in-flight edits alone and restores no work, approval or key by itself.
- Atomic `<safe name>--<UUID>.workspace.json` publication preserves stable IDs, duplicate display
  names and old UUID-only v1/v2/v3 reading. Resave migrates old filenames; profile import uses the
  same naming rule. Windows-invalid/reserved names and UTF-8 filename length are bounded.
- Dialog labels/rows/secondary actions and bottom-right Close updated in EN/PL. Stable modal ID
  makes its secondary button styles apply correctly. Existing activation/API-check semantics remain.
- HTTP Start validates fresh exact-queue consent, key presence and read-only `/key` authentication
  before any worker starts. Missing/rejected key leaves all jobs staged, including local tasks in
  mixed queues; no failure/partial files or media prep. Recheck key/grant/staged IDs under lock
  after authentication; consume authorization only at Start. No implicit OS unlock.
- Supplied `openrouter.py:274` is the missing-key raise. The printed files/line chain belongs to
  that single `SpeechEngineError`; no evidence of additional independent exceptions in this log.

## Verification

Dedicated root `/tmp/ewp-b-locations.QrHmIZ`; synthetic media and fake credential/provider only.
Final make check:1046 tests, Ruff/format and mypy115 pass; integrations17 pass/4 deselected.
Filename regression includes duplicate names, legacy migration, reserved characters and byte limits.
Actual server restart passes: directories/list recalled with no picker/Refresh, both named saves
present, restored cloud task remains staged on absent/invalid key and starts only after valid fake
key plus new consent. Dialog12 EN/PL/theme/390/960/1920 cases pass. Zero external requests/page errors.
Full Chromium regression:216 cases at nine widths390–3840 in EN/PL/light/dark pass; real process
restart restores source/translation drafts, applied revisions and existing export downloads.
Five changed JS syntax checks, guide mirror consistency and helper Ruff/format pass. Stale helper
label and short-guide/doc mismatch were corrected before the final gates. No native/GPU/live
provider qualification is inferred from these model-free checks.

Content-free [evidence](../evidence/2026-11-22-b-locations-key-preflight.json) records all results.
No real key/model/private recordings accessed; zero paid/provider calls. Frozen artist ZIP hash
still1265a795495f37dd0e18b88d57a80bee502dbb707e55289a55551f17b451f6f1.

Disposable server stopped and `/tmp/ewp-b-locations.QrHmIZ` removed after evidence capture.
Delivery targets main; next is the owner
[focused update check](../../Instructions/GUI_UPDATE_TEST_CHECKLIST.md). Retain current accepted
cloud/export behavior without another paid test or reinstall. A stays closed; full B acceptance
and task10 remain separate. Artist ZIP frozen.
