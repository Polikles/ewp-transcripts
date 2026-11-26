# Native Windows application — delivered0.25.0

Final source9b8da316fc0a87fceebaf824f0342dc43788f004; run45811242398 PASS. Delivery:
/home/linuch/project-ewp/deliveries/ewp-0.25.0-installers. See native-windows-app-evidence.json.
1201 local tests/17 integrations,46 installer groups/18 Windows filesystem cases and4 desktop
cycles pass.65 previews reviewed,4 full-size desktop/dialog views; complete opaque native dialog,
all buttons within bounds. Both CI archives, six product hashes,446 packaged source files verified;
final desktop host byte-identical to independent local compile.68 earlier delivery hashes preserved.
EXE SHA25665ce4c0754d0297ae089ccbcb5a7579725844f5a02dc22b3355f1d86f7c4abdc.

Implemented own WPF/WebView2 window and identity, direct shortcut, no console, focus-on-relaunch,
suspended-before-job-owned Python tree, authenticated narrow lifecycle bridge, safe close/wait/stop,
save-failure refusal/confirmed discard, autosave-off explicit flush, live-metric tolerance, durable
pending media with Windows TEMP alias handling, and maintenance/reset-race coordination. Updated
paired native copy and EN/PL bundled help. .NET self-contained; WebView2 Evergreen checked at startup.

Agent work complete. Next is owner focused native-window feedback. Preserve prior application,
mixed-model and installer passes; no repeated full inference/paid campaign. Actual owner Win11/GPU
qualification is not implied by model-free Server2025 CI. Original web UI remains inside the native
host. Public release/signing and AMD research/experimental adapter remain later. Exact cumulative
cloud spend unchanged at USD0.0291461230985028369. Unsent candidates are disposable and not deliveries.

Implementation log follows.


Owner authorizes moving from delivered installer0.24.4 to native Windows interface/lifetime.
Baseline5676d1d; preserve approved app workflow, owner EN/PL terminology/assets, model pins,
credentials/consent, recovery and original deliveries. No paid/model campaign or public release.
Goal: own Windows window/identity without console/browser lifetime ambiguity; safe autosave/close/
active-work handling, single-instance focus, managed launch/install/update/removal integration.
First desktop implementation preserves the approved UI in a native Windows host; architecture,
implementation, tests and immutable build delivery pending. Follow opening TODO.

Implemented first slice (not yet delivered): WPF/WebView2 own window/identity; authenticated private
backend, single-instance focus, kill-on-close owned Python/worker job, local-only renderer bridge,
close choices/save refusal, installer shortcut/launch/control payload and uninstall coordination.
First cross-build succeeded with pinned.NET10.0.404/runtime10.0.15 and WebView2 SDK1.0.4370.26.
175 focused Python tests PASS; Windows lifecycle/evidence test added but not yet run. Full gate,
version/docs, Windows CI/visual review and delivery verification are outstanding.
Scratch /tmp/ewp-native-app-hqog5fvc; final target0.25.0; no paid/model/provider tests.

Full local gate PASS1192 tests/19 Windows skips, Ruff/format306/mypy120;17 integrations PASS.
Updated EN/PL managed-launch/installation documentation and mirrored bundled guides. Desktop package
uses a content-hashed NuGet lock and original SDK license. Cross-build PASS after security/cancellation
changes. Added actual renderer external-fetch blocking, download and maintenance handshake checks
for Windows CI (pending). Source version0.25.0; approved app/installer workbooks unchanged.

Native run45804521730: installer46 WPF groups/18 filesystem cases PASS; desktop FAIL because
hidden restore dialog's permanent aria-busy was counted as active work. Actual renderer and backend
started, pending media/no-auto-start/close choices/locales/security checks passed before timeout.
Fix uses busy action buttons/generation flags, not hidden dialog metadata. Added explicit save with
autosave off, confirmed discard recovery, and suspended-start job assignment before Python redirector
spawn (eliminates assignment race). Cross-compile passes; qualification rerun pending.

Native run45805338977: installer and18 Windows cases PASS; desktop advanced through startup,
media/save failure and durable close-save but found activateWorkspace re-enabling disabled autosave.
Preserve that preference after the explicit close flush. Also retain cancel-Wait after a prior
save failure and remove its button before actual shutdown; native regression covers this sequence.
Cross-build passes; rerun pending. Existing68 delivery SHA256 entries verified unchanged.

Native run45805850072: first full desktop save/close, all19 in-window checks and descendant cleanup
PASS; restart phase timed out before recovery-ready. No product delivery yet. Investigating recovery
with explicit synthetic-state diagnostics/screenshots. Test media is now a valid generated PCM WAV,
not arbitrary bytes. Full local gate remains1192 PASS; no models/provider/GPU qualification implied.

Native run45806882034 reproduces restart failure: recovery record/catalog present but pending source
is unavailable after shutdown. Root cause: Windows TEMP 8.3 alias differs from resolve_allowed_path's
long path, bypassing temporary-picker preservation. Canonicalize GuiSelectionCache.root before its
ownership comparisons; add alias regression and assert post-close pending files lie under outputs.
This is a real Windows recovery bug, independent of model/media decoding; valid WAV alone did not fix it.

Native run45807984303 from49fda8b PASS:46 installer WPF groups,18 Windows filesystem cases and
all4 complete desktop cycles (save, restore, crash/focus, maintenance). Recovery alias fix confirmed:
pending media persist under outputs, both restarts idle, owned descendants gone on close/crash.
Final hardening additionally applies CREATE_NO_WINDOW to media/diagnostic/picker subprocess adapters
only in desktop sessions; CLI remains unchanged. Qualification adds actual worker/grandchild console
handle checks through that shared adapter. New full gate/native build and final artifact verification
remain pending before delivery. No new inference/GPU/provider qualification or paid spending.

Native run45808741094: all four in-window cycles/console checks passed, but the external maintenance
caller hit ConnectionResetError while polling a server that had just exited. Treat transport EOF/reset
as an unavailable response, then confirm process/host identities have exited; never skip that check.
Add deterministic transport-reset regressions. This fixes a real shutdown/maintenance race, not an
inference failure. Final gate/native rerun pending; freeze scope to resolving this final qualification.

Native run45809460119 fromcfb0f60 PASS all46 WPF groups/18 Windows cases and4 desktop cycles,
including actual helper/grandchild console handles0 and clean maintenance exit. Final code review
also covers changing queue timestamps during close: ignore only queue metrics in the editable-state
comparison (backend checkpoints latest jobs on shutdown), retry durable path adoption up to3 times,
and retain strict review/pending-media/form checks. Added model-free native live-metric regression;
last qualification pending. Full local gate1201 PASS/19 skips;17 integrations PASS, no paid calls.

Native run45810181669 from9153d77 PASS; archive digests/six product hashes/446 packaged source files
verified, desktop host byte-identical to the independent local build.65 images inspected in overview.
Visual review found close-dialog captures omitted the window background and clipped content margins.
Use an opaque padded dialog root; native checks now assert background alpha and complete button bounds.
Unsent9153d77 candidate moved to task scratch without overwriting it; final source/build will differ.
All68 prior owner-delivery hashes remain untouched. Final fresh candidate/native render review pending.
