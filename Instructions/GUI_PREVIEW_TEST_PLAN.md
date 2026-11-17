# Integrated GUI preview — one consolidated owner session

Start with [GUI quick start](GUI_QUICKSTART.md). This combines GUI-34a's pending checks with the new
preview. No separate acceptance round is needed for each internal commit. GUI-55 is already closed.
The target is Ubuntu 26.04 in WSL with a Windows 11 browser. Docker, native Windows and bare-metal
Ubuntu are not part of this session. No full 24-episode transcription rerun is requested.

Record: full tested SHA (`git rev-parse HEAD`), application version, Windows/browser version,
`wsl.exe --list --verbose` distribution/version, launch command and URL. Record whether source/output
paths are on the WSL filesystem or a Windows mount and which OS owns any folder dialog.

## Minimal materials

Use a dedicated temporary test root, for example `preview_root=$(mktemp -d /tmp/ewp-gui-owner.XXXXXX)`.
Keep disposable candidates, resume state, reviews and exports there, outside the private corpus.
Use two completed canonical results with compatible review/revision/translation artifacts when
available, including one longer multi-speaker example and a long Unicode filename. Keep exact hashes
and lineage; do not hand-edit the originals. English audio is not required. For real transcription,
select one short published Polish recording (about 6.5 minutes); a second episode is enough to check
queue independence. Stop after the bounded test, retain only useful content-free notes, and remove
that test root after any needed diagnosis. Never delete production sources or model caches.

## Test sequence

| ID | Actions | Expected behavior |
| --- | --- | --- |
| P01 | Pull/start with the quick start; record SHA/version. Open Settings & About and bundled help. | One real application with larger logo/title, smaller subtitle, local EwP background patterns in both themes, service status above navigation, version/license/source links, asset notices, local audio and optional local/cloud provider explanation. Short Settings/Saved work pages retain compact header/context heights. Graphic creator URL remains explicitly unverified. |
| P02 | Switch PL/EN and system/light/dark, then reload. Change audio language/translation target separately. | Preferences persist. UI language does not change processing values, transcript text, paths, IDs, provider models or consent. Technical diagnostic codes/provider messages may remain in their original language. |
| P03 | Select two audio files, cancel/reselect, use a Unicode name and two files with the same basename from different directories. Run **Test local dependencies** before real transcription. Select `s0e00-Szymon.wav` and `s0e00-Damian.wav` together, inspect/dry-run the single grouped episode, explicitly stage and review both sources. Also select tracks for a different episode. Try Add to queue without planning and a corrupt input separately. | Native-library failures show check details even if the ffmpeg command works. Shared-prefix speaker tracks form one job; distinct episode prefixes remain separate. Both files survive staging/recovery. Select episode gives feedback; missing-plan staging focuses/highlights Dry-run. Failed jobs show a code, failure details and dependency-test guidance. Actual file contents are copied locally, with isolated failures. No ASR starts on selection. Exact plans/settings are confirmed before staging. Durability/recovery follows staging. Direct paths and an explained folder-dialog fallback remain available. |
| P04 | Import two completed canonical results, including a versioned result. Select one for correction/translation batch work while opening the other for review. Skip an optional stage; retry a failed operation if present. | Active recording and stage are clear. Batch selection is independent. Per-file/stage text and markers distinguish pending/running/completed/failed/skipped. A failure does not hide completed work. No provider call occurs on selection or navigation. |
| P05 | At 1440×1000, 960×1080, 768px, about 720px, and 900×1440 portrait: navigate all stages, provider/settings controls, speaker panel and workspace cleanup. Test actual browser zoom through 200%. At about 390px check monitoring/simple actions. | No lost context functions, overlap or page-level clipping. The queue may scroll locally. Keyboard focus remains visible and rightmost queue actions are reachable. Full phone long-text comfort is not required. Resizing is not browser zoom. |
| P06 | Type unsaved source and target edits; change stage, theme and locale; switch recording. Check the requested recording in the editor and the active context. | Navigation retains dirty drafts. File switching checkpoints or guards the draft and loads the correct document; batch checks stay independent. No text changes from language/theme selection. |
| P07 | Test **Split at cursor** at a word boundary, block start/end, inside a word, punctuation/newlines/Polish text; test **Separate selected text** separately. Use pointer and keyboard, Undo/Redo, merge and Preview. | Cursor split requires a collapsed caret and two nonempty word-boundary sides; selection isolation requires complete selected words. Invalid requests explain the boundary. Stable anchors/speaker IDs are retained; Preview validates real word alignment. No midpoint timestamps. |
| P08 | Rename/reassign speakers, add speakers through at least speaker 007, attempt to remove one still used, and choose a custom color. Reload/save/recover. Compare brand reset with configured production profile. | Dynamic rows follow stable IDs; six palette roles do not cap review speakers. In-use removal is refused. Custom overrides survive; adopting brand colors requires an explicit action. Existing exports remain unchanged. |
| P09 | Preview source edits, inspect warnings, explicitly verify and Apply. Export TXT/SRT/VTT/HTML and production YTT before translation. | Immutable verified revision and usable source-language exports; translation/dictionaries are not required. A later edit invalidates Preview/approval. Repeat export does not overwrite prior artifacts. |
| P10 | Use **Open manual translation**, verify direction/source/revision; edit side by side, Preview, explicitly approve and export. Test an empty target with omission permission off, then deliberately enable it for one unit and repeat Preview. | Sources/ownership remain immutable. Translation has separate human approval. Empty targets fail by default; explicit omissions retain provenance and are omitted from exports. Confirmation is not restored. |
| P11 | Optional real provider check: choose exact local/cloud endpoint/model, check readiness, then explicitly consent for one small correction or translation operation. Skip if no provider is available or paid use is not desired. | Actual provider state/disclosure is visible; a candidate is not final. No audio is sent for correction/translation. Errors are bounded and retryable; keys do not enter browser/workspace/log artifacts. A separately operated local API is not a promise about third-party retention. |
| P12 | Apply a newer verified source after creating a translation. Reopen stages and inspect old translation/export identities. | Old outputs remain available, with a visible stale-source warning when applicable. Reopening for the newer source requires renewed review; nothing silently overwrites accepted work. |
| P13 | Open optional dictionary management and project/language/direction selectors. Generate/review proposals if suitable compatible artifacts exist; keep approved/rejected decisions. | Correction dictionaries remain distinct from translation dictionaries. Publication is versioned and requires completed decisions. Normal export never depends on dictionary work. |
| P14 | Save work with visibly distinct source and target draft markers. Note catalog/root; stop GUI with Ctrl+C. Restart it and preferably use a fresh browser/private window. Load the saved workspace. | Loading succeeds and restores exact result/review paths, draft values and queue sources—not merely two existing rows. No automatic restart of GPU work. Keys and human/omission confirmations remain absent. |
| P15 | Refresh managed-source inventory. Remove an inactive queue row and inspect retention reasons; saved workspace/review lineage must still protect required sources. Exercise deletion only on a demonstrably disposable, unreferenced test copy. | Catalog routing, inline feedback and reference-aware cleanup remain intact. Publications and referenced sources are never deleted. No additional GUI-55 test is required. |
| P16 | Generate **new** YTT files with the brand profile; upload them through the owner's established YouTube process and compare timing, wrapping, colors and speaker identity with the production profile. | Exact new colors, readability and timing receive fresh manual qualification. Production configuration stays available; prior successful YouTube evidence is retained without claiming the new palette passed. |

## Results

Use PASS, FAIL or NOT_RUN. A mocked/model-free VM test is not real GPU, provider or YouTube evidence.
Screenshots or logs are useful for a failed layout, diagnostic, wrong identity or restoration mismatch;
no extensive evidence is needed for each successful click. Exclude keys, private transcript text and
unnecessary source paths from shared evidence.

| ID | PASS / FAIL / NOT_RUN | Observed behavior | Notes / useful evidence |
| --- | --- | --- | --- |
| P01–P16 (one row per tested scenario) | | | |

Send the tested full SHA plus failures and any NOT_RUN items. Keep production acceptance separate from
this preview's headless VM checks. If diagnosis needs artifacts, provide only a small exact-lineage
example set; the full corpus is unnecessary.
