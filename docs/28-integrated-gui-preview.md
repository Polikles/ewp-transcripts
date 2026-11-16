# Integrated GUI preview 0.20.0

Base: `3ce1caa5f73eb89fa0f2e6e831f90ededf43ea17` on `main`, clean before work.
This is an untagged internal preview for one consolidated owner session, not a public release.
Start with [the WSL launch guide](../Instructions/GUI_QUICKSTART.md) and use
[the consolidated test plan](../Instructions/GUI_PREVIEW_TEST_PLAN.md).

## Adoption and working boundaries

The approved private UI handoff 0.1.0 / brandbook 0.4.0 supplied workflow, visual boards,
responsive/WSL verification, tokens, production fonts/icons, asset notices, provider copy and
palette migration rules. Its prototype was not used as backend code or test evidence. Only approved
local distribution assets and notices were copied; no private bundle, reference snapshot, planning
history, prototype or transcript examples were committed.

The shell keeps the existing forms and event-bound controls mounted. Stage navigation changes
visibility; it does not create another transcript model or replace application services. A separate
recording list and active-stage/draft context distinguish the active editor from batch checkboxes.
Handoffs reveal their destination stage. Dictionaries, saved work/cleanup and Settings/About remain
independent entry points. PL/EN and system/light/dark preferences are browser-local and independent
of transcription language/translation direction. User text, paths, IDs, model names and payloads
are excluded from UI translation. Stable diagnostic codes and some technical/provider details retain
their original English; bundled/repository documentation remains English.

Multi-file audio selection uploads actual contents to the existing local selection cache, with
per-file failures isolated. It selects files for the unchanged inspect/exact-plan/stage/start
contract. No ASR starts merely because files were picked. Staging retains durable source copies.
Direct server paths, native output-folder adapters and multi-result/versioned imports remain.

Cursor split and selection isolation are distinct commands. A cursor split requires a collapsed
caret inside a block, a word boundary and nonempty text on both sides. It checkpoints a dirty draft,
creates adjacent blocks in the same protected anchor, preserves speaker IDs and requires Preview
before Apply. It does not generate timestamps. Displayed anchor times come from canonical words;
unsupported/missing timing is visibly unavailable. Existing alignment/ownership services still
validate the immutable revision. Undo/Redo and selection isolation remain independent.

Speaker rows derive from canonical and revision-local IDs; additional speakers beyond six are
supported in review. The initial ASR count/auto setting remains separate. Color is a marker beside
readable identity, not transcript text or a cross-recording voice identity. Custom/configured colors
are retained. Explicit adoption of the six brand roles can reset the current recording's colors;
additional roles use a repeated baseline marker until customized, with no six-speaker review cap.

Source approval/export remains useful before translation. Direct manual translation is available
without an LLM; assisted paths still require exact readiness, disclosure and scoped consent.
Semantic approval/export is separate. An older/raw open translation is visibly marked when the
queue has a newer verified source. Existing output artifacts are retained rather than overwritten.

## Compatibility changes

| Boundary | Additive behavior | Compatibility |
| --- | --- | --- |
| `/api/v1/reviews/export` | Optional `speaker_colors` map keyed by known speaker ID, validated as `#RRGGBB` | Omitting/null preserves configured production YTT. Explicit maps create new export versions through the existing service; prior exports remain intact. |
| Review document | `configured_speaker_colors` and canonical anchor `start_ms`/`end_ms` | Protected word anchors/text/save contracts remain unchanged. No canonical/revision schema migration. |
| Workspace v2 fields | Allowlisted semantic-review/result/revision/parent/applied paths, direction and active-record color/profile preferences | Existing workspaces remain readable. Paths are validated, then exact document lineage is checked through existing load services. Older application versions cannot read new fields; use the delivered version to restore a new preview workspace. |
| Workspace loading | Save dirty drafts first; restore exact per-result source session and exact semantic review | No transcript text, credentials, human consent or omission confirmation is serialized as preferences. Server queue history is revalidated before restoration. |
| Static assets / CSP | Fixed local asset manifest and `font-src 'self'` | Unknown/traversal resource names remain rejected; no CDN, remote font allowance or public-listen mode. |

Palette migration is explicit in this preview: configured production remains available until the
owner qualifies new YTT files. Brand colors are `#F5F7FA`, `#00AEEF`, `#F2C55B`, `#BF734D`, `#8CFFB3`,
`#64D8D0`. A custom map changes only the new export operation, not configuration, canonical timing,
speaker identity, saved legacy overrides or previous files. GUI preview colors are not evidence that
YouTube accepts/readably renders the new palette. Translated formats retain their existing service
contract (TXT/SRT/VTT/HTML); no new translated YTT renderer is introduced.

## Verification record

All disposable tooling, screenshots, candidates, workspaces, exports and build outputs use a dedicated
`mktemp -d` root under `/tmp`. Only reviewed content-free results belong here; remove temporary data
when verification is complete. Commands used the unchanged ML lock, offline checks and temporary
uv/Ruff/mypy caches where appropriate. Development tool installation and loopback browser/server
execution needed sandbox approval; no desktop or system packages were installed.

Tool versions: Ubuntu 26.04.1, Python 3.12.13, uv 0.12.1, Ruff 0.16.1, mypy 2.3.0, pytest 9.1.1,
Playwright 1.65.2, Chromium Headless Shell 159.0.8154.6 (revision 1255), Hatchling 1.33.0,
FFmpeg/ffprobe 8.0.1. Playwright stable metadata and official
[installation](https://playwright.dev/python/docs/intro) / [browser](https://playwright.dev/python/docs/browsers)
documentation were consulted. Hatchling was resolved by the existing build-system requirement;
no application/ML dependency version changed. `uv.lock` changes only the project version to 0.20.0.

The reusable `tools/check_gui_layout.py` now checks all principal sizes in PL/EN and light/dark,
real font loading, geometry, keyboard access, dirty text and selection preservation, mixed states,
local multi-audio copying/inspect/plan/staging without Start, cursor split/isolation/Undo,
additional speakers/custom colors, real source Preview/Apply/export and manual semantic approval/export.
It also checks stale-source warnings and canonical input hashes. Providers are not called.

Recovery is observable: after saving distinct source/target drafts, the check clears server queue
rows and all browser pointers, reloads, asserts zero rows/no open documents/empty path fields, then
loads the saved workspace and checks successful load status, exact result/review/translation paths,
source and target values, and absent confirmations. `--recover CHECKPOINT` repeats that proof in a
new browser after the test server is actually stopped/restarted. This is model-free Linux evidence;
actual Windows/WSL recovery remains in owner test P14.

The build check uses `uv build --out-dir "$test_root/dist"`, compares each packaged frontend file's
bytes with source and imports/serves assets from the wheel itself, without ML imports. Original
branding/font/icon bytes retain their supplied notices. Two original OFL notice files are narrowly
exempted from Git whitespace checking so their supplied bytes remain unchanged. A failed pre-final font check exposed the
missing local CSP permission; a pre-final restart assertion also exposed a stale *test expectation*
after the test had intentionally edited the saved semantic draft. Final verification uses the latest
explicitly saved known target value. These earlier failures are not new production acceptance results.

Executed outcomes: `make check` PASS (769 tests), `make test-integration` PASS (2 passed,
4 deselected), browser-tool lint/format and JavaScript syntax PASS. The rendered matrix passed
72 combinations (three stages × six sizes × two languages × two themes). Multi-audio copy/inspect/
plan/staging, cursor/isolation/Undo, seven-speaker editing, source and manual semantic approval/
export, mixed annotations and stale-source checks passed. Observable recovery passed both after
clearing browser/server state and after an actual Linux server-process restart in a fresh browser,
including exact draft values and the previously applied translation identity. Wheel/source builds
passed, 33 frontend files matched source bytes, both owner guides were found in the source archive,
and zipped-wheel resource serving succeeded with no heavy ML imports.

See WORK_STATUS.md for the final executed outcomes and the delivery report for the full pushed SHA.
No screenshots containing transcript fixtures or runtime state are committed.

## Owner qualification and exclusions

One owner session covers GUI-34a plus this preview. Windows 11/WSL Ubuntu 26.04, actual browser zoom
to 200%, real GPU/provider execution, deployment picker/dialog behavior, restart recovery and newly
generated brand-palette YouTube files require their own observed results. Published Polish episodes
are sufficient; no English audio or full corpus is assumed. GUI-55 remains closed.

Deferred: synchronized playback in the review editor, audio repair, new cloud ASR providers, model
benchmarks, native Windows porting, Docker and bare-metal qualification. The exported HTML player is
a separate existing capability. Waveform progress is not a dependency. Creator URL remains an explicitly
unverified placeholder with a TODO in the bundled notice and Settings/About.
