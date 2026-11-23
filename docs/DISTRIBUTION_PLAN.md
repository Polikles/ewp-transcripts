# Installation, updates, removal and versioning plan

Implementation update: managed0.22.0 and EN/PL instructions are ready for focused installer acceptance. See [execution checkpoint](checkpoints/2026-11-23-distribution-execution.md); native Windows acceptance/publication remain separate. The original planning wording below is retained as the agreed contract.

Status: planned, 2026-11-23. Owner requests the next-step plan and expands distribution scope.
This document does not announce an installer, change the application version or publish a release.
Current baseline is main `438f91e`, still reporting `0.20.0`. Current EN/PL manuals, terminology,
GUI acceptance and both artist-reference deliveries remain complete. Artist icons are independent.

## 1. Correct versioning and establish a release procedure

- Audit changes after the 2026-11-16 `0.20.0` checkpoint and the accumulated Unreleased section.
  The proposed next baseline is `0.21.0`: this interval includes functionality additions, not only
  bug fixes. Do not fabricate intervening releases, rewrite old tags or relabel an old archive.
- Apply [Semantic Versioning](https://semver.org/spec/v2.0.0.html). While developing `0.y.z`, use an
  explicit project convention: increment MINOR for a delivered feature set or incompatible change,
  PATCH for compatible fixes; document every compatibility change. After `1.0.0`, incompatible
  public-contract changes increment MAJOR. A development Git commit alone need not be a release.
- Every new identifiable build handed over for installation/manual testing gets a distinct version;
  do not distribute changing application contents under an already delivered version number.
  Candidate builds may use a consistent prerelease convention, with Python package normalization
  accounted for. A commit hash supplements the version; it does not replace it.
- Synchronize package metadata/lock entry, installed CLI `--version`, GUI/About, diagnostic reports,
  installer/release metadata and the necessary current docs. Audit the stale package-version fallback
  separately; avoid maintaining competing literal versions. Historical evidence retains its original
  version. Schema/API/model/dictionary versions are separate identities, not automatic app bumps.
- Add automated consistency checks, versioned release notes, reproducible source/installer artifacts
  and digests. Use version tags for installer download targets. Public release/tag publication remains
  a deliberate delivery step; planning this work does not publish anything.

## 2. Shared installation and update foundation

Retain reusable work in `scripts/setup-windows.ps1`, `scripts/install-fresh-ubuntu.sh`, model setup,
platform runtime preparation and doctor. They are checkout-based helpers today, not the promised
no-checkout bootstrap installers. Create a common documented operation contract for terminal and
GUI adapters rather than separate implementations with drifting dependency/model pins.

- Inventory installation location, installed application version, private Python/runtime ownership,
  selected pinned models and managed launchers. Separate application files from recordings, outputs,
  workspaces, profiles, dictionaries, OS credentials and shared model caches.
- Preflight: supported OS/architecture, available disk space, network, required permissions, NVIDIA
  driver/GPU/CUDA for local ASR and required native/media components. Explain actionable failures.
  Reference qualification is Windows 11 x64 and WSL2 Ubuntu 24.04/26.04 on RTX 3090. Other NVIDIA
  GPUs with at least 8 GB VRAM remain an unqualified expectation. Bare-metal Ubuntu execution must
  be reported honestly; existing WSL tests do not qualify it automatically.
- Offer deliberate local-ASR preparation or cloud-only/review usage. Download pinned local models
  only when selected and after the user accepts the relevant upstream gated-model terms. HF access
  cannot bypass those terms. Do not require an OpenRouter key for local work.
- Keep scripts repeatable: reuse valid application/model assets, validate downloads, tolerate paths
  with spaces/Polish characters, show stages/logs and retain useful failure diagnostics without secrets.
  Install for the current user by default; request elevation only for identified system prerequisites.

### Update procedure and commands

- Document the current manual update now as the existing stop/save/backup → git pull → locked sync →
  restart path. Replace it with the managed update entry point once implemented, retaining the manual
  development-checkout path separately. No new update script is claimed to exist yet.
- Check current/target versions and compatibility, including saved-work/profile/schema changes.
  Require stopping active work before replacement; do not update a running transcription process.
- Obtain a fixed versioned artifact and verify integrity. Prepare/verify the replacement before
  switching the active installation, with recovery to the previous usable application if it fails.
  Do not promise downgrade compatibility for a changed user-data schema; preserve pre-migration
  data separately when migration is necessary.
- Preserve recordings, results, drafts, publications, dictionaries, profiles, workspace catalogs,
  OS key-store entries and unchanged model snapshots. Fetch only missing/changed required assets.
- Post-update version/readiness checks, clear success/failure summary and instructions for relaunch.
  Basic update verification must not trigger paid transcription or redownload every model.
- Add dedicated EN/PL update/recovery instructions and short main-README commands. Decide explicit
  user-triggered update UX; no silent background update during work is authorized by this plan.

## 3. Scripted uninstall with explicit model removal

- Provide Windows and Ubuntu removal entry points alongside installation/update commands.
- Preview paths, owned components and reclaimable size before confirmation. Stop/refuse active
  application work safely. Remove application-owned runtime/private FFmpeg/launchers as selected.
- Preserve original media and publications. User profiles, saved work, dictionaries and credentials
  have independent deliberate removal choices; default to preserving user work.
- Offer optional removal of the exact downloaded model editions. Do not delete the entire Hugging
  Face cache or unrelated/shared snapshots, global Python/uv or system drivers. Explain shared use;
  cache ownership alone cannot prove no other application depends on a snapshot.
- Provide a readable result/log. Reuse this removal operation in the later graphical uninstaller.

## 4. Short terminal installers for Windows and Ubuntu

Owner-facing target: one or a few copy/paste lines per operating system in the main README, with
short prerequisites, estimated disk/download needs and launch instructions. A user must not first
clone a repository, find script paths or choose compatible package versions manually.

- Windows: PowerShell bootstrap that obtains a fixed verified application bundle and invokes the
  shared installer. Use supported Windows 11 x64 behavior; prerequisites are checked and explained.
- Ubuntu: shell bootstrap for 24.04/26.04, including WSL detection, obtaining the same fixed release
  and invoking the shared installer. Test and state actual native-Ubuntu coverage separately.
- Bootstrap scripts may download dependencies/models during installation. A standalone installer
  means no manual checkout requirement; it does not imply that multi-GB models are bundled/offline.
- Expose consistent install, update, repair and uninstall entry points. Bootstrap code/artifacts and
  checksums must correspond to the selected version, not an arbitrary changing main-branch payload.
- Document prompts for HF access and optional OR configuration without putting secrets in command
  arguments, shell history, URLs or logs. Do not add fictional download commands to README before
  their target artifacts actually exist.

## 5. Installation lifecycle acceptance before the graphical wrapper

Deliver a focused checklist for clean install → launch → update → retained work → repair → uninstall
(with models kept and explicitly removed) → reinstall. Cover interruption/download failure, invalid
HF token or missing model access, low space, existing caches and credential preservation/removal.
Verify that failed update leaves a usable prior installation and retained data. Cloud connectivity
checks do not upload user recordings or require a paid pilot.

Agent implements/verifies available paths in the Linux VM. Owner performs actual Windows 11 x64
acceptance from supplied artifacts. Reuse prior application workflow acceptance; this is the new
installation lifecycle test, not a request to repeat every old manual workflow checklist. Where a
fresh Ubuntu environment is unavailable, record that limitation and provide the remaining test.

## 6. Graphical installer and uninstaller

First graphical delivery targets Windows, distributed as EXE/MSI or an equivalent chosen after a
small packaging feasibility check. Ubuntu already has the terminal installer in this sequence;
this plan does not presume a second native graphical package. Framework/package/signing choices
are implementation decisions to evaluate, not a newly fixed dependency today.

Wizard flow:

1. Choose language and location; run host tests and show what is ready, what needs action and why.
2. Select local model preparation or cloud/review operation; show download/disk needs.
3. For local gated downloads, explain/link HF terms and accept a token in a masked field. Use the
   token transiently for the explicit download, without saving it by default or logging it.
4. Optionally enter/check an OpenRouter key in a masked field. Explain that it serves cloud ASR,
   correction and translation; save it deliberately in the OS credential store through the same
   mechanism the program uses. Never write plaintext fallback credentials. This setup choice is
   not audio-upload/paid-usage consent; the application still asks for each required scope.
5. Install pinned application/native dependencies and selected models with progress, retry/recovery
   instructions and a clear completion report; run readiness checks and offer launch.
6. Create a desktop shortcut and Windows Add/Remove Programs entry. Supply a matching graphical
   uninstaller with explicit optional model/credential/data removal choices and preserve defaults.

Use the application's logo, typography, colors, light/dark conventions and custom gear/status
language where the installer framework supports them. Keep native accessibility/keyboard behavior
and readable progress/errors. Share tested operation logic with terminal scripts. EN/PL wizard copy
and manuals are maintained together; new wizard-only labels need review, not regeneration of the
already approved full application terminology workbook. Custom icon feedback is non-blocking.

## Completion and boundaries

Each slice gets a checkpoint, version/changelog when delivering a build, targeted tests and EN/PL
docs. The final README must offer runnable terminal install/update/uninstall instructions, actual
versioned download links and the optional graphical installer. New paid tests, extra ASR engines,
Docker, universal dictionaries and hardware research are outside this distribution plan.
