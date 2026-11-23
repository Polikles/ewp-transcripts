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
