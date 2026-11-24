# Session handoff — installer 0.22.2 under owner review

Updated 2026-11-24 UTC. This is the current resume point. Older handoffs, milestones and
unchecked historical boxes do not override the status below or the owner's next message.

## Stop/resume boundary

The owner is reviewing the installer **0.22.2** on Windows and will send comments in a NEW
session. This turn requests a local project handoff only. Do not start another product change,
rebuild, installer acceptance test, copy-review workbook, release or artist package now.
On the next session, read the new feedback, add its tasks/checkpoint, then implement that scope.
There are no outstanding questions the owner must answer before sending the review.

## Workspace and identities

- Workspace: `/home/linuch/project-ewp`; repository: `/home/linuch/project-ewp/ewp-transcripts`.
- GitHub: `Polikles/ewp-transcripts`, branch `main`.
- Last pushed HEAD before this handoff: `f696f308174985d3e51ff0647e4af31e08e130aa`
  (`docs(installer): record verified 0.22.2 Windows delivery`).
- Actual 0.22.2 artifact source: `d51b1068aefc347babc8277b28b08642e025bbc9`.
  Later documentation commits do not change those already delivered bytes.
- Application version: `0.22.2`, single source `src/ewp_transcripts/_version.py`.
- Working tree was clean before this handoff. This turn leaves LOCAL documentation-only edits
  and this checkpoint; no commit/push or product/version/artifact changes are intended.
- User communication: Polish. Repository prose/code: English, except Polish manuals/localization.
- Scope: a practical podcast/recording workflow tool, not a general transcription research platform.

Read next: root `AGENTS.md`, `WORK_POLICY.md`, opening `TODO.md` and `WORK_STATUS.md`, then this
file. For detailed implementation evidence use the 2026-11-23 installer-location checkpoint/JSON.
`docs/99-roadmap-v2.md` retains historical plans; newest status and owner scope take precedence.

## Delivered application work — keep closed

- Package A (recovery, cancellation/retry, cleanup, exact export downloads) is accepted.
- Package B native Windows/WSL workflow, OS keys, locations, media stream controls and OpenRouter
  ASR are implemented. Owner's focused fixes/workflow checks are accepted; do not impose a new
  full ASR/LLM/reinstall campaign because a historical plan still says pending.
- Local GPU ASR, mixed local/cloud queue, cloud word timing/routing, fresh upload consent,
  manual source/translation review and exports, status/progress and saved-work recovery fixes
  have existing evidence. Keep their security/data safeguards intact.
- Application EN/PL terminology was reviewed by the owner and integrated; interface accepted
  2026-11-22. Maintained reference: `docs/ui-language/en-pl.csv`, matching XLSX and integration
  notes. It has 2219 stable IDs. Never regenerate IDs from newly edited English strings.
- English user manuals updated; complete Polish manuals and bilingual offline help delivered
  2026-11-22. Entry points: `docs/gui/README.md`, `docs/gui/pl/README.md`; packaged guides under
  `src/ewp_transcripts/web_assets/guides`. Keep source/manual mirrors consistent.
- A NEW artist frontend reference was delivered 2026-11-22 after terminology/docs. Both the
  original and later ZIP are frozen; no further rebuild is currently requested.
- Full profile exchange remains provisionally accepted, not completely owner-tested. Actual
  browser zoom 200% remains optional/unchecked. Do not turn either into a new completion gate.

## Distribution work delivered

- 0.21.0 establishes the version baseline after accumulated 0.20.0 changes.
- 0.22.0 adds shared managed install/update/repair/rollback/launch/uninstall, exact ownership
  inventory, Windows/Ubuntu terminal packages without cloning the repository, standalone WPF
  Windows EXE, desktop shortcut and registered matching graphical uninstall.
- Real Ubuntu 26.04 VM lifecycle checks passed without new local models or paid ASR. Consult
  `docs/checkpoints/2026-11-23-distribution-execution.md` for exact qualification limits.
- 0.22.0 wizard appearance/flow was rejected before installation. 0.22.1 fixed pages, icon,
  subtitle, disk gates, host rows, masked checked credentials and footer/help controls.
- 0.22.2 addresses the next owner feedback: see below. **Owner has not yet accepted its GUI
  or qualified the new native managed-install lifecycle.** CI is not that acceptance.
- Terminal update/removal procedures and EN/PL instructions already exist. They are not future
  unimplemented tasks. Public online bootstrap activation is still pending matching publication.

## What 0.22.2 changed

1. Radio cards explicitly center glyph/text; modern rounded fields/buttons/step markers. Existing
   framed logo/EXE icon/subtitle retained. Native tests measure radio center alignment.
2. Correct arbitrary minimum path depth that rejected a fresh `D:\Transcripts-test-01`.
   Dedicated drive-child folders and Program Files children are supported; drive/home roots,
   unrelated data, symlink/junction paths and unowned installations remain protected.
3. Step 2 is Location and checks / Lokalizacja i test. Duplicate check caption removed.
   VC documentation link appears only after missing/inconclusive host results.
4. All maintenance actions autodetect registered/default managed installations and display the
   location; ask only when none is found, with an explicit alternate-installation link.
5. Changing operation clears later folder defaults, logs, results/errors, credentials, terms and
   removal choices; invalidates stale delayed callbacks. Install state no longer leaks forward.
6. Host OS label reads actual registry DisplayVersion (e.g. Windows 11 26H2); older/unknown
   versions get a warning, not an invented release name or silent guarantee. Includes 24H2/Win10.
7. HF help uses a real accessible vector info icon; credits TXT is reflowed into paragraphs and
   logical lines, preserving all original words/assets.
8. Host checks remain unprivileged. Mutations needing protected-folder write access request
   same-account Windows elevation; normal launch activity locks live outside the install root.

Program Files implementation: `OperationRunner.cs` uses a same-SID ACL named pipe with kernel
peer-PID, parent/image and server-PID validation. Credentials go through pipe/stdin, never argv or
plaintext files. A trusted system PowerShell bootstrap sets protected single-file extraction
BEFORE starting the elevated EXE; embedded payload extraction is protected too. Running EXE is
held read-locked. Different-account elevation is rejected to preserve user/cache/key identity.
No normal-user Modify grant is added to Program Files. Existing old root locks are observed.
Missing-model downloads while elevated require nonlinked locations inside the same user's profile;
complete existing custom caches can be reused. Custom external caches should be prepared normally.

Autodetection intentionally recognizes MANAGED installations, not the owner's old Git checkout.
Since the owner had not completed the new wizard installation, a missing managed-install result
can be correct. Do not adopt/delete a checkout or scan whole drives to manufacture a match.

## Verification already recorded — do not rerun just for this handoff

- `make check`: 1127 passed, 2 native-only skips on Linux; mypy 116 source files; lint/format pass.
- Installer Python suite: 46 passed. Integration suite: 17 passed.
- Native Windows Actions run: `45238109373` for source `d51b106...`, PASS:
  <https://github.com/Polikles/ewp-transcripts/actions/runs/45238109373>.
- 20 named WPF coverage groups include state/discovery/gating/alignment/localization/credits
  and actual authenticated PowerShell/EXE broker transport using synthetic credentials.
- 2 actual native filesystem cases PASS, no skip: empty D: child host check and a small
  stdlib-only Program Files launcher using an external profile lock.
- All 19 native PNGs visually inspected. All six local installer artifact SHA256 values match
  the native-tested CI build exactly. This proves artifact identity, not real-model installation.
- Actual medium-account interactive UAC, full new managed Windows installation/local models,
  and installer lifecycle acceptance on owner's PC remain pending. The owner tests Win11 x64;
  their reported Windows release is 26H2. Do not infer this from CI's Windows build.
- No real HF/OR key or provider audio used for this installer task; no paid calls/model campaign.

Evidence: `docs/checkpoints/2026-11-23-installer-location-state.md` and
`docs/checkpoints/2026-11-23-installer-location-evidence.json`.

## Local deliveries — outside Git, preserve bytes

Directory: `/home/linuch/project-ewp/deliveries/ewp-0.22.2-installers/`.

- `EwP-Setup-0.22.2.exe` (~150 MiB), Windows ZIP, Ubuntu ZIP/tar.gz.
- `EwP-Setup-0.22.2-preview.zip` (~793 KiB), `preview.html`, `previews/` (19 PNGs).
- `START-HERE-PL.txt`, `INSTALLER_ACCEPTANCE.md`, `windows-self-test.json`.
- `DELIVERY.json`, `SHA256SUMS.txt`, installer-only EN/PL CSV (118 paired entries).
- `Install-EwP-0.22.2.ps1` / `.sh` are generated ONLINE templates and cannot fetch an unpublished
  matching release. Downloaded offline bundle entry scripts are usable separately as documented.

EXE SHA256: `efd99684b69fa5c90d6741471bd5c638cab8483c0e3803d9f106cf46151570b5`.
Preview ZIP SHA256: `5ff0a05027c740bd410344db592c03d6619358a322d0686af25bfebc3f9d3252`.
All other exact hashes are in the evidence JSON; avoid hand-copying or changing old manifests.
Preserve `deliveries/ewp-0.22.0-installers` and `ewp-0.22.1-installers` too.

Frozen artist archives under `/home/linuch/project-ewp/deliveries/`:

- `ewp-gui-artist-review-2026-11-19.zip`:
  `1265a795495f37dd0e18b88d57a80bee502dbb707e55289a55551f17b451f6f1`.
- `ewp-gui-artist-review-2026-11-22.zip`:
  `634b399903d31e2b970f6fbc9a85889ff1d67fda9bd511985e6815aea267ef3b`.

Both were reverified unchanged at the 0.22.2 handoff. Artist icons/feedback have no deadline and
block neither the installer nor documentation text. Documentation screenshots await final artwork.

## Next work / actual remaining TODO, in order

1. Wait for owner's 0.22.2 review in the new session. Record each new issue and implement the
   resulting scoped GUI/behavior corrections. Deliver a NEW version for any changed test build
   (likely 0.22.3 for compatible fixes; decide from actual scope, do not bump for this document).
2. Complete installer GUI approval. Full installer descriptions EN/PL are expressly deferred
   until that GUI is finished; do not ask the owner to correct the current CSV prematurely.
3. Then consolidate the complete installer EN/PL label/message reference for owner review,
   apply both-language corrections and keep the maintained reference synchronized. The existing
   application-language approval remains accepted; this is installer-specific work.
4. Finish actual focused native Win11 managed-install/UAC/local-model/lifecycle acceptance after
   appearance approval, using `Instructions/INSTALLER_ACCEPTANCE.md` and qualification plan.
   Owner may review language and actual installation in the order they prefer. Do not impose
   old full transcription/paid-provider tests or pointless repeated installations by default.
5. Incorporate any resulting fixes; update affected EN/PL installation/update/removal docs,
   packaged mirrors, README and version/evidence. Existing complete app manuals need maintenance,
   not another rewrite from scratch.
6. After acceptance, prepare deliberate versioned release/tag/assets and matching checksums so
   short online terminal commands actually work. PUBLICATION HAS NOT HAPPENED. Signing is a
   separate decision requiring a suitable certificate; current EXE is unsigned. No certificate
   or publication decision is needed to continue the current GUI-review loop.
7. Parallel: integrate new artist icons when supplied; update screenshots after final custom
   artwork. No deadline. Do not overwrite/rebuild sent artist packages as part of installer fixes.

Nice-to-have only, not blockers: Ollama/further local models, word/phrase playback highlighting,
alignment refinements, nontechnical instruction review, non-speech authoring/advanced channels,
audio repair/comparison, extra subtitle formats, dataset/model/dictionary research and broad
hardware/performance benchmarks. No precise progress/ETA calibration study. RTX3090 24GB is
tested; >=8GB VRAM on other NVIDIA machines remains an unqualified expectation.
Excluded: Docker, general model catalog/favorites/loading manager, manual timing overrides,
alternative translation chunking, whole-block audio-follow highlighting, editorial LLM modes,
bilingual HTML and other declined broad-platform features. Do not revive old roadmap options.

## Implementation map and repeatable checks

- `installer/manager.py`: shared lifecycle/ownership/paths, OS checks, locks and model safeguards.
- `installer/Install-EwP.ps1`, `.sh`, removal wrappers: terminal adapters; `bootstrap.*.in`: online
  fixed-version/hash templates. `installer/models.json`: fixed pinned model set, not a new catalog.
- `installer/windows/Wizard.cs`: pages/host/result/navigation; `WizardState.cs`: reset/discovery;
  `InstallationDiscovery.cs`: registered/owned state; `OperationRunner.cs`: normal/elevated worker;
  `Symbols.cs`, `ModernTheme.cs`, `Branding.cs`: appearance; `Credits.cs`: readable attribution;
  `Credentials.cs`: masked dialogs/checks. `WizardTests.cs`: native fixtures/previews/transport.
- `tests/unit/test_distribution.py`, `test_distribution_windows.py`: installer/path regressions.
- `.github/workflows/distribution.yml`: verified cross-build, native WPF + path/launcher cases,
  artifacts/previews. GitHub connector supports workflow jobs/logs/artifacts/downloads.
- `tools/prepare_distribution_tools.py`, `build_distribution.py`, `build_setup.py`: verified
  tools, clean deterministic bundles and EXE. Pins: .NET SDK10.0.404/runtime10.0.15, uv0.13.9.
- Local gate after substantive changes: `uv sync --locked`, `make check`; filesystem/media
  changes also `make test-integration`. Native layout changes need actual rendered Windows
  previews, not C# compile alone. No tests are necessary for this handoff-only edit.
- Final artifacts must come from a clean committed source. Build into a NEW output directory;
  `--allow-dirty` is disposable-prototype-only. Every new delivered build gets a distinct version,
  changelog/current docs update and exact source/hash evidence; see `docs/VERSIONING.md`.
- SDK/tools/temp outputs were removed after 0.22.2. `/tmp/ewp-installer-location.FeRwQy` no longer
  exists; no task server/build worker remains. Create a new dedicated temp root if needed.
  Tools+intermediates need about3GiB; retaining several publish/prototype folders hit tmp quota
  before. Remove only your own obsolete candidates; keep final delivery and frozen archives.

## Persistent collaboration/privacy rules

Start each task by consulting TODO/policy/status and leave a dated checkpoint. Communicate
progress in Polish; act through the authorized scope, do not repeatedly ask for permission.
Keep original media, canonical results, workspace/profile data and shared models safe. HF token
is transient for install; OR OS-store save is explicit; neither grants audio-upload consent.
No secrets in logs/Git/args/profile/export/plaintext fallback. Private benchmark data is local
under the workspace's `private benchmark` directory; it is not needed for installer GUI work.
Do not open a secret file merely because the path was mentioned in an old conversation.
Historical cloud pilot total: USD `0.0291461230985028369` within the original USD2 authorization.
No new paid tests are needed or implied by installer feedback; preserve that evidence.
No agent delegation unless the owner or applicable instructions request it.

This handoff reconciles stale TODO boxes for already completed terminology/manual/artist and
installer implementation work. It does NOT claim new owner installer acceptance. Local edits
from this handoff may remain uncommitted at next-session startup: preserve them, inspect status,
and do not treat them as unrelated product changes or reset them away. No push is requested now.
