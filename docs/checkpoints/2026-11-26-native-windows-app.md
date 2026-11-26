# Native Windows application — 2026-11-26

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
