# Current plan — 2026-11-27

<a id="current-next-actions--2026-11-26"></a>
<a id="owner-scope-and-current-status--2026-11-20"></a>
<a id="accepted-package-sequence--package-a-authorized"></a>

This is the authoritative selected scope and backlog. TODO contains immediate actions; WORK_STATUS
and the active checkpoint contain evidence/resume state. The previous complete roadmap and all
status records are preserved byte-for-byte in [historical inventory](../archive/project-status/inventory.json).
Historical proposals are not requirements to implement, and old NEXT gates do not override this plan.

## Current correction and next sequence

Owner accepts0.26.1 theme/Snap and compressed142MB EXE. Active target0.26.2 finishes NVIDIA
architecture/driver/VRAM guidance and full documentation reconciliation.12GB+ VRAM is approximate
full-local guidance; smaller compatible cards may work but are untested/unguaranteed, probably
will fail and should use cloud ASR. Unsupported architectures cannot use the locked local pipeline.
See [hardware policy](HARDWARE.md) and [active checkpoint](checkpoints/2026-11-27-nvidia-docs-audit.md).

| Order | Selected next action |
| --- | --- |
| 1 | Finish/qualify the current diagnostic and documentation changes, preserving accepted UI/lifecycle/model behavior. |
| 2 | Plan the signing and first public release approach with the owner, before any other backlog. Signing is mandatory before public release; procedure, private instructions, keys and credentials stay outside Git. No purchase/sign/publication today. |
| 3 | Settle standalone EXE storage in the requested repository releases/ location, public assets, source/version/notes and final signed-artifact/checksum contracts. The compressed installer size is accepted; stop further slimming/minimal-downloader work. |
| 4 | Execute only the deliberate first-public-release step, then verify actual downloads/checksums and Windows/Ubuntu bootstrap URLs. Current internal artifacts are unsigned and not public releases. |
| Parallel | Artist feedback/icons whenever available, then final screenshots; no deadline and no blocking dependency. |
| After public release | Prioritize optional enhancements below; no automatic implementation authorization or required benchmark campaign. |

## Delivered and accepted foundation

<a id="13-gui"></a>

- Canonical JSON, immutable revisions/translations, raw/verified subtitle and platform exports,
  dictionaries and source/model/provenance integrity remain the core contracts.
- Package A recovery/cancellation/workdir cleanup/downloads and package B native Windows, OS key
  storage, saved locations/profiles, media choices/cloud ASR and focused workflow were delivered.
- Owner EN/PL corrections and full bilingual/offline manuals are delivered. Do not regenerate or
  overwrite approved workbooks or sent artist archives.
- Managed installation/update/repair/model addition/rollback/uninstall, preflight/progress/report,
  icon/registration and work preservation have owner feedback and qualified fixes through0.24.4.
- Native WPF/WebView2 app0.25.0, Personalization/closing0.25.1, Snap and experimental AMD0.26.0,
  themed blank surfaces and compressed packaging0.26.1 are delivered. Owner accepts current theme,
  left/right placement and size. The source player stays in the LEFT sidebar.
- Local/cloud ASR, three-local-model mixed queue, source/translation review/exports and restart
  recovery retain their reported passes. Full profile exchange remains provisional; browser200%
  zoom is optional. These qualification limits do not reopen completed workflow acceptance.
- AMD Windows ASR is experimental and physically untested; alignment/diarization use CPU. Keep
  explicit Install/Update warning and automatic diagnostics. Do not generalize DLL import to GPU
  inference or every AMD card. Preserve pinned NVIDIA/model/AMD dependencies.

## Optional backlog — strictly AFTER public release

| Topic | Retained scope / boundary |
| --- | --- |
| Ollama/further local API adapters | Consider after release; existing LM Studio/OpenRouter workflows remain delivered. |
| Playback highlighting | Optional word/phrase highlighting only; whole-block automatic following is removed. |
| Alignment/timing/instructions | Optional refinements and less-technical-reader review; no manual timing override editor or new mandatory quality campaign. |
| Generic directory discovery | Retain FR-A05/ADR-0017: core CLI directory scanning still uses configured suffixes. Later generic ffprobe discovery must safely skip non-media and reuse probes. Existing GUI selected-media inspection does not erase this deferral. |
| Advanced audio | Crosstalk/deduplication, channel topology/surround, separate non-destructive audio repair and original/repaired transcript comparison. Preserve repetitions, original bytes and separate identities. |
| Subtitle/non-speech authoring | Optional extra formats and styling/authoring; existing TXT/SRT/VTT/YTT/HTML/timed-event foundation stays delivered. No bilingual HTML requirement. |
| Research | Private/public corpus comparisons, translation-quality suites, universal dictionaries, model/preset/hardware matrices and quality trends only if separately chosen. No ETA accuracy study or new baseline test is required for release. |
| Public project website | Link it once owner supplies a ready address; no website publication is scheduled. |

## Cancelled, removed or outside selected scope

- GTX1070/8GB/32GB/i5-10400F test campaign, telemetry collectors and legacy runtime profile:
  CANCELLED by owner2026-11-27. Do not leave a promise to test8GB or adapt Pascal.
- Further EXE slimming/minimal online installer: CLOSED; compression and current size are accepted.
- Local Scribe/MAI: REMOVED; no public weights. Keep the existing cloud choices unchanged.
- Docker, bilingual HTML, extra editorial/LLM punctuation modes, speaker-count research, whole-block
  playback following, full model catalog/favorites/loading management, manual timing overrides,
  alternate translation chunking, owned input snapshots and unselected scheduling/auto-maintenance
  are outside selected delivery. Do not resurrect them from historical requirement/proposal prose.

## Historical identifier reconciliation

R/E identifiers retain previous discussions without losing the owner decisions:
R01/R03→delivered B7; R02/R08→delivered B8 with narrow FR-A05 deferral above; R04→delivered cloud ASR;
R05/R06 removed; R07/R09/R10 optional audio/subtitles; R11 existing export foundation plus optional
non-speech authoring (bilingual HTML removed); R12 native Windows delivered; R13 distribution delivered,
public release pending and Docker removed; R14 selected cleanup/aliases delivered (other scheduling
removed); R15 artist/website non-blocking. E01/E02/E06/E09 delivered cancellation/downloads/keys/cleanup;
E03/E04 outside scope; E05 optional Ollama after release; E07 outside scope; E08/E10 removed;
E11/E12 optional alignment/instructions; E13 word/phrase-only optional, whole-block removed.

All earlier detailed proposals, preset candidate lists, original numbering and acceptance records
remain in the [complete prior roadmap snapshot](../archive/project-status/2026-11-27-99-roadmap-v2.txt).
Dataset-dependent quality limits remain in ADR-0014 and the traceability matrix; no missing physical
hardware or representative English/three-speaker dataset is silently claimed as qualified.
