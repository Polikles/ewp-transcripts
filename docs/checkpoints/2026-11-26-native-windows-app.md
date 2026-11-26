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
