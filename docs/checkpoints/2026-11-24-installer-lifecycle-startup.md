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

## Final verification and delivery

Delivered0.23.0 from clean source `5edfc1d2b3b9f49eaea85f036942ba6dd143bff4`.
Final Windows run [45372295246](https://github.com/Polikles/ewp-transcripts/actions/runs/45372295246)
passes25 WPF coverage groups and5 actual Windows filesystem cases with no skip. These include
direct user-facing PS removal with read-only dependencies, preservation of a user file and
removal after losing the application's Python. Native broker/permissions, compact un-clipped
path input, restricted maintenance and real information-focus feedback also pass.

Local full gate:1135 passed,5 Windows-only skips; mypy117, lint/format pass. Integration17 pass.
The new byte-progress test exercises the pinned HF `http_get` with an8-byte synthetic response:
snapshot file-count progress alone is insufficient, so the isolated setup child also instruments
the hub's actual HTTP/Xet byte bars. No model or provider request is made by that test.
The full gate reports two ordinary POSIX fork/deprecation warnings after library imports; no
test failure. Local .NET audit lookup can warn under the network sandbox; the online native CI
build passes and its six artifact hashes match local bytes exactly.

Browser checks pass: initial private automatic save before output selection, output association,
pending-media persistence, fresh-browser and actual server restart, preserved unavailable
checkpoint/manual recovery/rearmed autosave, no restored cloud consent or automatic ASR.
An async catalog refresh no longer replaces a name being typed. Approved EN/PL copy checks pass
2221 reference rows/36 layout cases;5 prior IDs updated (including the guide),2 diagnostics added,
original hidden owner baselines retained. Full installer-only language approval stays deferred.

All27 final native PNGs visually inspected. Six local artifact SHA256 values equal CI. Actual
source/hashes/qualifications are in `2026-11-24-installer-lifecycle-evidence.json` and DELIVERY.json.
Verified delivery: `/home/linuch/project-ewp/deliveries/ewp-0.23.0-installers/`, including EXE,
terminal packages, preview.html/preview ZIP, native report, focused checklist, START-HERE-PL and
131 preliminary paired installer strings. Earlier unshipped0.23 candidates are moved to the
hidden `.ewp-0.23.0-internal-candidates` directory; previous0.22 owner deliveries/artist ZIPs
remain unchanged.

EXE SHA256: `36a7e064d060ba556b4b2bc228fdab5fe976fd641148b02788b7d2b9cd1f5520`.
No new paid tests, audio uploads or model downloads. The supplied report was read locally and
not committed. Metadata-only HF hash lookup and disposable build/stdlib/browser tools are separate.

## Next owner step and boundaries

Owner reviews0.23.0 appearance and operation-specific flow, then focused update/removal and
startup recovery on the existing Windows PC. Preserve the already accepted0.22.2 installation,
desktop launch and episode transcription; no full paid/model/reinstall campaign is required.
If old removal erased registration, choose the remaining managed folder manually in the NEW
EXE (for example D:\\Transcripts-test-01). The new external installer can prepare its stdlib
runtime if the old installation interpreter is unavailable. Owner data/shared models are kept
by default. Do not use the old0.22.2 removal helper for the new test.

After installer GUI approval: full installer EN/PL reference correction, focused lifecycle
acceptance/docs maintenance and deliberate release/online-bootstrap activation. The EXE remains
unsigned; nothing has been published as a release. Native Windows application interface is a
later task after installer closure. Closing a browser still leaves the server active; idle
Ctrl+C no longer produces the manager traceback or a nested batch-job prompt.

No further product changes/builds are requested until owner feedback. Do not regenerate artist
archives or reopen old application gates. Cleanup complete: all task GUI servers and MSBuild/C#
servers stopped; `/tmp/ewp-installer-lifecycle.yUxrhL` removed after evidence was copied. Reverified
six hashes in each0.22.0/.1/.2 delivery and both frozen artist archives unchanged. The owner report
remains in its original home-directory location. Preserve final deliveries and the owner report.
