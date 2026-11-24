# Installer lifecycle and startup feedback — 2026-11-24

Baseline: installer 0.22.2, source d51b106; last pushed docs f696f30. Preserve preexisting
local handoff documentation edits and immutable delivered installers/artist archives.

Owner confirms successful Windows install, desktop launch and one episode transcription.
New scope is recorded exhaustively in the opening TODO. Finish installer behavior first,
then automatic startup workspace recovery/autosave. Native Windows interface is a later
stage after installer closure. No new paid provider/model campaign is required.

## Investigation

- Owner reports Windows removal removes shortcut/registry but leaves 15.5 GB installation.
- Root Remove-EwP.ps1 currently exposes mandatory internal Plan parameter; reproduce with
  native synthetic lifecycle rather than deleting owner material.
- Owner reports idle Ctrl+C traceback from manager.launch subprocess.run.
- Supplied report read locally at /home/linuch/EwP-setup-report.txt. It confirms successful
  CUDA/speech runtime and four pinned model availability checks, not a removal diagnosis.
- Old deferred removal aborts on first IO error and uses Directory.Delete on read-only uv
  dependency files; native synthetic readonly/uninstall regression now added to qualify this
  failure mechanism without claiming it reproduces every detail of the owner's machine.

## Implementation in progress

Operation-specific WPF model screens, automatic diagnostics, selective offline upstream-hash
verification, public/gated download separation, measured model-file progress, timestamp reports,
registration icons/size and restricted uninstall entry points implemented. C# build passes.
Model catalogue includes metadata-only upstream pinned SHA256/git-blob digests (no model download).
Native Windows helper test executes the direct PS entry point and deferred readonly-tree cleanup.
Elevated deferred code/plans have admin/system-only ACLs at creation, outside user temp.

Startup autosave/recovery implemented using existing version3 workspace/draft contracts. Automatic
queue checkpointing continues without a browser; interrupted work restores staged, never autoruns.
Writable installed roots use work-state; Program Files uses per-user state. Uninstall preserves it.
Task temporary root: /tmp/ewp-installer-lifecycle.yUxrhL. No paid calls/private media/model campaign.

## Verification / delivery

Pending implementation and focused automated/native checks. Never claim owner UAC/model
acceptance from CI. Record exact new source, artifact hashes and native previews before handoff.
