# Managed distribution

User instructions: [EN](../docs/gui/installation.md), [PL](../docs/gui/pl/installation.md).
Build identity: [version policy](../docs/VERSIONING.md). Native acceptance:
[focused checklist](../Instructions/INSTALLER_ACCEPTANCE.md).

`manager.py` is the standard-library-only lifecycle engine. PowerShell, shell and the WPF wizard
call the same install/update/repair/rollback/launch/uninstall operations. `check` is host readiness;
model/credential deletion and cloud usage always require separate choices. The format1 owner
marker records this exact installation root, release directories and model snapshots. The atomic
active pointer is changed only after runtime/version verification. Each candidate keeps its final
venv path. Failed preparation preserves the prior active runtime; known-dead locks recover, live
or unverifiable ownership remains blocked. User-added files are retained during prune/removal.

Build on Linux with network and enough temporary space (about3GiB for tools and intermediates):

```bash
python3 tools/prepare_distribution_tools.py --directory /path/to/private-temporary-tools
python3 tools/build_setup.py --tools /path/to/private-temporary-tools --output /path/to/NEW-artifacts
```

Use dedicated disposable directories. The normal build refuses dirty source or an existing output
folder. `--allow-dirty` is solely for disposable prototypes, never final handoff. Only tracked
application/scripts plus explicit control/metadata assets are bundled; models/media/private input
are excluded. The pinned toolchain manifest gives upstream URLs/digests and license sources.
The Windows EXE is self-contained and carries the Windows bundle; the Ubuntu tar includes its
bootstrap and checked ZIP. Online templates embed exact payload hashes, with fixed versioned
release URLs; do not advertise those URLs before publication. Artifacts remain outside Git.

The CI workflow cross-builds, checks hashes, and runs the EXE's `--self-test` on Windows without
installing the speech app or sending network/audio requests. This checks native WPF/vector/text
startup, not the actual Win11 install/GPU/model lifecycle. Owner acceptance is separate. An unsigned
acceptance build is identified as such; code signing requires a suitable certificate.

`ui-en-pl.csv` covers wizard-specific paired copy. It does not replace or regenerate the already
approved application terminology workbook. Technical child-process output remains original for
diagnostics; normal wizard controls/stages have both languages. The original vector brand assets
are embedded directly; no replacement artwork is generated.


0.22.1 uses operation-specific pages and separate masked credential dialogs. `WizardTests.cs`
exercises navigation/disk/host-language/model/credential gates with synthetic data and no worker
or network invocation; `--preview-dir` renders native WPF screenshots, including the shell-extracted
EXE icon. `EwP.ico` is derived from the accepted framed SVG at seven sizes. Optional regeneration
uses `tools/build_installer_icon.py` with system librsvg/cairo; normal builds need neither because
the derived ICO is committed. Public pinned-model file sizes/revisions are in `installer/models.json`;
this is a fixed default set, not a model catalog expansion. Cancel uses a transient marker read by
the common manager; child work stops while prior active installation and downloaded cache remain.

0.22.2 adds aligned radio cards, operation-state reset and validated managed-install discovery.
Windows accepts dedicated drive-child and Program Files locations. Host checks stay unprivileged;
mutations needing access use a same-account UAC worker with SID/PID-authenticated named-pipe
transport. Tokens never appear in arguments or files. The elevated single-file runtime/payload
extracts into an admin-only session; normal launch locks live in separate per-user state.
Native tests include authenticated bootstrap/transport, real D: host validation and a tiny
stdlib-only Program Files launcher fixture. These do not qualify an interactive UAC prompt,
full application installation, GPU/model preparation or provider workflow. Full installer EN/PL
copy approval waits until the GUI is accepted.

0.23.0 separates program-only maintenance from selective model recovery, adds pinned upstream
file hashes to models.json, measured model/FFmpeg progress and timestamped reports, and fixes
readonly-file Windows removal. Root uninstall.exe/registered maintenance restrict actions.
Automatic workspace recovery starts with the app; writable installs use work-state, protected
installs use per-user state. Synthetic lifecycle/queue tests do not require downloaded models.

0.24.0 adds two explicitly selected, unchecked local ASR models to the four baseline models.
Optional metadata is mirrored to packaged local-asr-models.json; tests verify exact correspondence.
Base pins remain unchanged. Updates never select new optional models automatically; missing
unselected optional snapshots are not repair failures. Byte events use single writes; backend
notices remain in technical details. The header reuses web-pattern-dark.svg beneath a dark veil.


0.25.0 adds `desktop/windows/EwP.Desktop.csproj` and the packaged `control/EwP.Transcripts.exe`.
`build_setup.py` builds it before composing the Windows bundle. Its exact WebView2 SDK is locked
in `desktop/windows/packages.lock.json`; the original SDK license ships in `licenses/`.
The installed shortcut and wizard launch this EXE directly, without PowerShell. Explicit
`launch.ps1 -Browser` remains available and retained pre-desktop releases use browser mode.
The Evergreen WebView2 Runtime must exist on the target; the host checks before starting Python.
Architecture and security: [native application](../docs/NATIVE_WINDOWS_APP.md).
CI also installs only tiny non-ML GUI dependencies in an isolated fixture and tests the real
window/renderer, pending-file recovery, save refusal, focus and child-process cleanup after crash.
These tests never download models or send audio; they do not qualify GPU/provider inference.

CI usage, free/public runner rules, artifact storage,7-day retention and owner billing controls are
documented in [GitHub Actions](../docs/GITHUB_ACTIONS.md). Public-only job guards prevent automatic
private-repository execution; same-ref runs cancel superseded work. This does not publish releases.
