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
