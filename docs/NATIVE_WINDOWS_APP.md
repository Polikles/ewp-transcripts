# Windows application interface and lifetime

Owner authorization: 2026-11-26; first target0.25.0. Preserve the approved HTML/CSS/JS workflow
inside a native WPF Windows window using WebView2. The app has its own icon/process/taskbar identity,
no PowerShell console and one window per installation/user. CLI/browser mode stays explicit. New native-only wording is paired in [EN/PL copy](desktop-ui-en-pl.csv);
the approved application and installer workbooks are unchanged.
A full rewrite of the approved editors as WPF controls is outside this implementation.

## Ownership and closing

The native host validates the managed installation and starts private Python without a console.
Python retains the existing OS-lifetime installation lock. The host owns Python and its descendants
in a Windows kill-on-close Job Object, including inference/media/provider workers. The initial
process is created suspended and assigned before its venv redirector can spawn the real interpreter.
Media, diagnostic and picker subprocess adapters use CREATE_NO_WINDOW only in desktop sessions;
explicit CLI/browser behavior is preserved. Repeated launch
uses a current-user named pipe to focus the existing window; no second backend is created.

The native management credential travels only through child environment/loopback HTTP headers.
It never enters JavaScript, arguments, workspaces, URLs or diagnostics. Only the exact loopback
origin is embedded; external user links open outside it. Web messages are narrow lifecycle replies
with request IDs and origin validation, not generic native file/process commands. Password saving
and autofill are disabled. Browser profile/preferences stay in private user state across updates.

On close, save pending media/workflow state and source/translation drafts before shutdown. Paused
staged tasks remain paused after restart. Active work offers Keep working / Wait and close / Stop
and close. Save failures keep the window open. Explicit close also saves if periodic autosave was disabled;
it does not re-enable that preference. A separate discard action requires confirmation. Graceful cancellation is attempted before the owned
process job is closed, preventing invisible background work. Uninstall requests the same flush;
if the UI refuses because saving failed, removal stops without deleting application files.
The application window remains until its owned backend has exited (or durable-save cancellation
hits its bounded grace period). Killing/crashing the host also closes its Job Object; existing
creation-identity and OS-mutex recovery handles abandoned metadata at next start.

## Packaging and runtime

### Window preferences (0.25.1)

Persist the Win32 normal rectangle and maximized state atomically before HWND destruction and
after a short geometry debounce. Minimized windows retain their normal/maximized restore state.
Missing, old width/height-only or invalid records use the centered default; SetWindowPlacement
recovers off-screen rectangles when displays change. Repeated launch restores a minimized window
without losing its maximized state. Geometry is per-installation local state, not a portable profile.

Settings & About → User profile → Personalization shares language/theme, default palette, playback
speed, review layouts and ETA with browser mode. Portable profiles include these preferences;
custom palette conflicts are remapped without changing existing colors. Native-only title-bar modes
are system (default), application theme and custom RGB color. A narrow appearance WebView message
updates DWM caption/text attributes with contrasting text; system preference changes are observed.
Cache resolved appearance locally for the next window before the renderer is ready.

Save/shutdown progress is an owned, centered native popup with the opposite app theme. This avoids
WebView2 child-window airspace hiding a WPF overlay. Save refusal still keeps the window/backend
open; busy decisions and owned-worker lifetime remain unchanged. Source audio stays in the left
sidebar, bounded to its normal column, with the Chromium additional-controls menu preserved.

Microsoft references checked 2026-11-26:
[window placement](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowplacement),
[DWM attributes](https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute).

### Startup and closing surfaces (0.26.1)

Resolve the first blank window from Windows app theme; thereafter use the cached application
preference, preserving explicit light/dark versus system. Legacy appearance records retain their
resolved theme. Apply the same opaque background to WPF shell and WebView before controller
creation; use controller options for early browser background and reveal the document after load.
The document resolves its stored/system theme synchronously before styles/deferred application JS,
also improving browser first paint. After successful save, hide the renderer while stopping owned
work so its disposal exposes the same themed shell. Save refusal restores the live interface.
The existing centered contrasting progress popup remains unchanged.

Both Windows single-file executables compress their embedded .NET payloads. The bundle still
contains the native app and pinned runtime; ML/model dependencies remain explicit online downloads.
No unsupported assembly trimming or new system runtime prerequisite is introduced.

### Snapped geometry and AMD qualification (0.26.0)

GetWindowPlacement may retain pre-Snap normal bounds. Normal windows now save GetWindowRect screen
coordinates with an explicit marker, and restore them with SetWindowPos. Legacy workspace records
and maximized normal rectangles retain SetWindowPlacement behavior; unavailable displays fall back
safely. Debounced saves observe actual geometry immediately, retaining it through minimization.
Minimum width480 permits half-screen use on smaller displays. A saved record wins on1080p too;
without one, the centered default is bounded by the current work area. After updating, position or
snap once and close to replace incomplete pre0.26.0 records.

Native run45892474997 verifies real Win+Left and full process restart, all five desktop lifecycle
cycles, accepted Personalization/closing/sidebar behavior and actual AMD DLL import without models.
AMD ASR runs in a private HIP process owned by the native job; alignment/diarization use CPU.
See [AMD scope and limits](AMD_EXPERIMENTAL.md) and [evidence](checkpoints/2026-11-26-snap-amd-evidence.json).
No physical AMD inference qualification is implied.

### Build and dependencies

Use the existing pinned.NET10 WPF toolchain and exact stable WebView2 SDK1.0.4370.26. Ship the
SDK's actual license with existing.NET/uv notices; retain all owner-reviewed project/legal prose.
Use the shared Evergreen WebView2 Runtime. Check before launching Python; if unavailable, show
an actionable native error and Microsoft's runtime page. No silent browser fallback or audio upload.
Install/update copies the host and registers a direct desktop shortcut. Legacy rollback chooses
browser launch when that retained version lacks desktop support. Removal accounts for the host
and waits for the window to release files. No public release/signing/model downloads in this stage.

Sources checked 2026-11-26:

- [Microsoft WebView2 distribution](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution)
- [Microsoft secure hosting guidance](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/security)
- [Stable SDK package](https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.4370.26)

## Verification boundary

Use model-free backend/JS lifecycle tests and real native WPF/WebView2/child-process tests. Verify
restart recovery, file selection, no implicit queue start, save failure, busy decisions, focus,
blocked external resources and absence of descendants after close/crash/removal. GPU/provider
inference is not requalified by these tests. Existing owner passes and exact cloud spend remain.
First public release and AMD research remain after native app delivery/qualification.


## Delivered qualification — 0.25.0

Source9b8da316fc0a87fceebaf824f0342dc43788f004, native run45811242398 PASS. All four actual
window cycles, real process/console checks, native close controls/bounds, renderer download/origin
checks and restart/maintenance behavior pass with synthetic media.1201 local tests and17 integrations
pass;65 previews reviewed. See [evidence](checkpoints/2026-11-26-native-windows-app-evidence.json).
This qualifies the host/lifetime without repeating GPU/provider inference. Owner desktop review
is the next boundary; first publication and AMD research remain later.

## Delivered follow-up — 0.25.1

Source1a665b33b24772f93c8c8aa7ec22c5a83a0aad08, Windows45885593097 PASS: four actual desktop
cycles, saved normal/maximized bounds, off-screen/invalid fallback, minimized-instance activation,
DWM setter results and16 exact caption-pixel comparisons from full-window captures. Shared browser
preferences/player pass62 checks; local1205 tests and17 integrations pass. Centered opposite-theme
shutdown cards preserve safe-save and worker lifetime.105 native previews reviewed; see
[evidence](checkpoints/2026-11-26-window-personalization-evidence.json). Owner focused review follows;
AMD(experimental), remaining release work and first public release stay after interface closure.
