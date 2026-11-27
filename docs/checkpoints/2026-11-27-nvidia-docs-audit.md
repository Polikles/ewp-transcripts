# NVIDIA preflight and full documentation audit — 2026-11-27

Owner accepts0.26.1 background and compressed EXE size. Keep12GB+ VRAM as approximate full-local
recommendation; smaller compatible cards are untested, may work but likely fail and should use
cloud ASR. Determine exact pinned CUDA/library architecture boundary and show unsupported/low-VRAM
notices in Install/Update host checks. Unsupported local choice must not block cloud-only use.
Cancel GTX1070/legacy-profile/telemetry tests and further minimal-installer work. Audit all docs,
requirements, TODO/backlog/roadmap; signing and first-release approach will be planned NEXT, before
other backlog. Signing remains mandatory before public release, with procedure/keys outside Git.
Artist non-blocking; local Scribe/MAI removed; other optional improvements after public release.

Baseline b762505; product0.26.1 source d6dd924 immutable. Target0.26.2 for diagnostic behavior.
No physical new GPU or paid/model/inference campaign. Research/implementation/audit pending.

## Current implementation / audit findings

Pinned NVIDIA stack: torch2.8.0+cu128, CT24.8.1, CUDA12.8.90, cuDNN9.10.2.21. Official pinned CT2
build uses CUDA12.8.1; FP16 plus PyTorch architecture intersection begins at CC7.0 (Volta; common
GeForce Turing). Project full-Update1 driver policy Windows/WSL572.61, native Linux570.124.06;
this is deliberately distinct from NVIDIA's theoretical limited minor-version compatibility.
Host metadata checks no models/ML; unknown architecture/selection is not certified, per-card VRAM
never summed. Low/unknown memory warns but preserves deliberate compatible local choice; cloud
installation and app-only maintenance remain available. Early new-local guard prevents mutation.
Existing AMD profile/acknowledgement stays separate. Native UI adds7 states×2 locales, including
null VRAM, plus cloud/local/update gates. Candidate C# cross-build passed before null-VRAM extension;
current native clean-source qualification pending.

Whole Markdown inventory293 documents (147 maintained,146 historical),524 local file/anchor links:
zero maintained broken links, nine frozen relative links in archive/mvp-validation-runbooks whose
README explicitly preserves original path context. All148 original requirement IDs remain; five
new GPU requirements bring153, all covered by traceability with no undefined IDs. Seven complete
prior authority/handoff/distribution-plan snapshots retained byte-for-byte with hashes. Old native/
GUI/Docker/recovery/download/key/8GB claims corrected; core FR-A05 deferral kept separate from GUI
inspection. No model pins, approved workbooks, original licenses/brand assets or old qualified
checkpoint evidence changed. See DOCUMENTATION_AUDIT.md and final inventory evidence.

Full local gate1261 passed/20 native skips,17 included integrations; Ruff/format311/mypy122 PASS.
Initial new pin-policy test mishandled dynamic project lock entries, then was fixed to assert the
actual torch local-version pin; no runtime failure. Editable metadata refreshed with locked sync
(build hatchling absent from cache). No paid provider/model/physical-GPU campaign or signing/release.

Documentation freeze: all30 EN/PL guide pairs are identical;12 added installer diagnostic pairs in
hardware-ui-en-pl.csv. Seven source snapshots are exact. Full audit inventory covers293 Markdown,
147 maintained/146 historical,524 file/anchor links,153 traced IDs (148 retained +5 additive).
Nine legacy relative links are intentionally retained only in already-frozen MVP runbooks.
Latest local gate1261/20,311 formatting and122 mypy files passes; latest C# installer build0 warnings/
errors includes null-VRAM protection. First native run45969545192 stopped in the new assertion:
the test read only the short host summary, excluding the separate rendered GPU notice. Corrected
the assertion to read actual visible host controls. No production rendering change was needed.
Fresh clean-source/native CI/artifact and visual checks pending.
