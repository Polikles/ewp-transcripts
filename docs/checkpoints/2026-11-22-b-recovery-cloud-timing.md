# B saved-work, pending-media and OpenRouter word timing feedback

2026-11-22, baseline clean main 7a1c2da. Follow opening TODO for every owner-reported item.
Owner confirms favicon, API check, mixed-provider queue and fresh restored cloud consent blocking.
New issues: viewport artwork gutters, misleading active session-key button, missing failed/cancelled
rows/partial loading and workspace name, lost pending-media input/duplicate selections, provider
responses without word timing (Whisper Large and Scribe). Terminal fails at parse_transcript, not
initial path validation. Inspect private supplied ZIPs read-only; preserve media/failure artifacts.

Do not claim a cause until reproduced. Use a dedicated disposable root for extracted diagnostic
metadata/reproductions; never commit transcript/audio/keys. No fresh model install or artist ZIP
changes. Existing server-session keys intentionally survive GUI-state clearing, and loading an OS
key activates it immediately. Owner terminology decisions: after functional completion export stable
field/message ID + editable EN/PL locally on VM; owner may correct EN too; apply and commit approved
version as the reference for later corrections/translations, then manuals. No premature full review.

Next: inspect archived JSON structures and runtime/restore code, establish failures, implement with
meaningful tests and evidence. Retain prior live pilot total USD 0.0153610111540591670; do not run a
broad paid requalification. Any diagnostic paid retry must be narrowly justified within existing
explicit provider/sample/budget scope, avoid repeat calls without new evidence.

## Findings / implementation in progress

Both private ZIPs contain durable media and failure/publication artifacts but no workspace manifest
(no workspace_version/staged_jobs/terminal_jobs record). Owner confirms full output folders were
zipped. Do not assert a save was lost: a selected legacy save can still live in the private catalog.
Expose actual saved-work file path in GUI and retain named-save identity (readonly existing name;
Save as new unlocks editing). Favicon/API check/fresh cloud consent remain accepted.

Reproduced stale-snapshot restoration hazard in code/tests: saved staged job later creates a failed/
cancelled reservation, so a fresh plan selects another version and old restoration aborts after
terminal rows appear. Restore matching terminal state using validated source hashes plus current
planned episode signature, keep its failure files, no automatic retry. Other safely replanned staged
items may allocate the current free output version. Partial load previously left name/highlight stale.

Pending picker media were never serialized (only input form path, stripped on save for temporary
sources). New workspace v3 carries bounded typed hash-bound pending media, preserves picker copies
on explicit save under output/.ewp-gui-sources/media and replans metadata on load with confirmation
unchecked; versions1/2 still readable. Profiles preserve references only and cleanup protects pending
media. Upload replies supply source digest, so same-name/same-content re-selection is deduplicated.
Keep valid same-name/different-content identities separate. Regression tests cover pending durability
and changed-source rejection plus later failed/cancelled snapshot recovery.

Cloud diagnostic checks use only supplied s0e01 audio and existing authorized shared test key/budget.
8s Szymon Whisper + Scribe and 8s Damian Whisper all return timed words. Two normalized 120s
Whisper clips (first and quietest measured chunk) also return real words. These five calls cost
USD0.0024088888888888. A targeted single complete Szymon-track session is in progress, stops on first
failure; original 0.03 estimate preflight rejected before any audio (zerocharge), 0.08 preflight now
allows it within original USD2 budget. Do not call this a model benchmark or native acceptance.
Original provider word-timing failure is not reproduced yet; do not invent a root cause or fake
alignment. Raw responses are private disposable files only, never committed or printed as text.

Disposable root: /tmp/ewp-b-recovery.nTxlJ0. Browser Playwright setup underway. Still need runtime
response-shape diagnostics/empty-speech tests as justified, full browser pending/restart/mixed status
checks, metadata/docs mirrors/localizations, standard+integration gates, evidence and cleanup/push.

## OpenRouter cause reproduced and targeted fix verified

Single Szymon track: chunks1–9 return real words through DeepInfra; chunk10 (last31.7045s) routes to
Together and returns nonempty text/one segment but words:[]. Generation metadata confirms vendors.
The original missing-word error reproduced exactly. Price alone cannot promise word-timing support.
Whisper routing now allows only DeepInfra/Groq (no fallback outside that set); read-only estimate
and start price ceilings use the same endpoint subset. Targeted original failing tail now returns
17 real timed words for Whisper, 14 for Scribe. A Groq 8s capability probe returns timed words too.
No timings inferred or text-only results accepted. Scribe's original user failure is not reproduced;
explicit empty-speech handling is tightened separately and malformed responses gain content-free
technical diagnostics/ledger status, so future provider omissions can be distinguished.

Actual diagnostic spend this task: USD0.0137851119444436699; cumulative authorized cloud spend USD0.0291461230985028369
within original USD2. Includes5 narrow source probes,10 sequential full-track diagnostic chunks and
3 final targeted checks. No automatic retry. Initial 0.03 budget refusal and existing-destination
preparation refusal sent no audio. Stop paid tests now; use recorded real responses for regression
replay. All raw responses/audio remain only in disposable root and must be removed after evidence.

## Browser findings / current resume point

Pending save/load now physically preserves both grouped media files in output, restores paths,
regenerates dry-run with approvals unchecked and deduplicates native re-selection. Null optional
stream_index from persisted models needed frontend normalization (otherwise selected_streams:null
caused invalid-stream error); fixed. Existing selected workspace name is readonly, switching to
Save as new unlocks it. A real browser test exposed an asynchronous list-refresh race: entering
Saved work started a request with old selected key, which could undo Save as new and overwrite the
old workspace. Revision/request counters now keep the latest user choice and discard stale list
responses; Save captures intended name/reference before awaits. Show actual manifest path from
list/save/load so legacy private catalog saves aren't mistaken for missing output-folder files.

Standard gate currently1042 passed/mypy115;17 integrations still to run after all code settles.
Focused pending browser first phase passed before race test enhancement, but restart initially
found the overwritten pending-name manifest, establishing the race. Latest server now runs current
code on8876 and latest focused phase uses /tmp/ewp-b-recovery.nTxlJ0/pending-complete; finish it,
restart actual server and run --recover. Earlier failed test roots are synthetic only, clean later.
Browsers installed only in disposable root (Playwright1.65.2/Chromium159). Need final focused/full
GUI suites with fresh XDG state on another port, original cloud-consent regression, docs/guides
mirrors/changelog/metadata translations, content-free evidence, cleanup and commit/push.

Live timing fix is verified; no further paid calls. Replay of first9 genuine responses + corrected
tail through CloudSpeechSession produced777 timed words ending at1110070ms,10 requests replayed,
zero provider calls. Cumulative actual cloud spend remainsUSD0.0291461230985028369. Preserve that
number in policy/roadmap/evidence before deleting private raw/audio root. Scribe original owner's
failure not reproduced on live supplied samples/tail; don't claim Together caused Scribe failure.

## Final verification / delivery

- `make check`:1043 passed; Ruff/format pass; mypy115 source files. Integration gate17 passed,
  4 deselected. Updated mock endpoint fixtures now include real provider tags and catalog summaries
  include their file paths, matching the new additive contract. These fixture corrections did not
  weaken source hash/consent/atomic publication tests.
- Full Chromium159/Playwright1.65.2:216 cases,9 widths390–3840, EN/PL and light/dark. No browser
  errors/external requests or overflow; full-viewport patterned gutters visually inspected at4K.
- Focused pending recovery passes both phases across actual process restart: selected two-file group
  remains2 files/1 planned task, valid durable input, duplicate re-selection ignored; Add to queue
  works. Two distinct named manifests persist. Completed plus later-failed cloud row restore2/2,
  loaded name clears validation, no ASR/approval restored. Unit cases also cover cancelled history
  and repeated-load deduplication. Saved pending media protect both tracks from cleanup; profiles
  preserve foreign references without copying media/starting work.
- Prior fresh-consent48 layout/security cases pass (boolean-only/programmatic checkbox blocked),
  key/OS mock and source/translation workflow/export polish pass with deterministic translation.
  Actual full saved source/translation drafts/applied exports restore after process restart.
- Live provider diagnosis/fix and the777-word genuine-response replay are recorded above. No local
  models/ML pins changed, no native Windows qualification inferred. Original native Scribe incident
  remains unreproduced; live supplied Scribe tail and sample pass, new content-free diagnostics help
  identify any remaining native/provider omission. Do not rerun paid tests after context reset.

Changed-step guides and bundled mirrors, contract, checklist, changelog, policy and roadmap updated.
Task10 decisions recorded without prematurely generating the full review table. Owner follows
`Instructions/GUI_UPDATE_TEST_CHECKLIST.md`, not reinstall/full four-model benchmarks. A remains
accepted; full B native/WSL acceptance and final terminology/manual gates stay separate. Sent artist
ZIP hash remains1265a795495f37dd0e18b88d57a80bee502dbb707e55289a55551f17b451f6f1.

Content-free evidence:`docs/evidence/2026-11-22-b-recovery-cloud-timing.json`. Reproduce focused
browser scenario with isolated XDG/work roots and a no-provider transcription stub that writes a
matching failed state; run `tools/check_gui_pending_recovery.py --url <loopback> --output <temporary>
--confirm-fake-service`, restart server, then same output with `--recover`. Never run its deliberate
failed-start phase against a real provider service. Full GUI helper needs a fresh dictionary catalog;
`--recover <checkpoint.json>` checks source/translation restoration after restart.

Delivery: temporary servers stopped and /tmp/ewp-b-recovery.nTxlJ0 removed after content-free
evidence/totals were saved. Guide mirrors and Git diff verified. Delivered on main; next is owner
update-only retest, including observing the previously unreproduced native Scribe case if it recurs.
