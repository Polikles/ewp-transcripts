# AMD documentation and remaining-plan review — 2026-11-26

Request: document implemented AMD support, then review TODO, backlog and roadmap and report the
next action plan. Baseline4583991; product0.26.0/source6c5fbcd remains immutable. No product changes,
new installer/build/Actions run, provider/model/GPU campaign or public release in this task.

Initial findings: AMD_EXPERIMENTAL.md and native guides already describe the implementation,
but README still advertises0.23.0, installation examples0.25.0 and the documentation index omits
AMD/native/CI guidance. Older TODO boxes still describe delivered native/AMD/copy work as pending.
Backlog is integrated into99-roadmap-v2.md, not a separate authoritative backlog file. Preserve
owner scope classifications: no Docker, editorial modes, catalogs or timing overrides as new gates;
optional benchmarks/hardware/artist work stay outside required delivery.

## Completed

- [x] Expanded AMD implementation map, exact Polish acknowledgement, terminal switch, profile
      precedence and source procedure with --no-sync to preserve the HIP dependency overlay.
- [x] Linked AMD/native/CI/version guidance from the docs index and README; current README and
      EN/PL artifact examples use0.26.0. Four installation/native help mirrors stay byte-identical.
- [x] Configuration documents models.accelerator and the lower-priority managed environment default.
- [x] Reconciled historical open native/AMD/copy TODO items; preserved exact qualification rather
      than inventing missing owner/UAC/GPU passes. Distribution plan links current status.
- [x] Existing roadmap now starts with the actual next-action table, later optional backlog,
      conditional local Scribe/MAI parity and removed scope. No separate competing plan created.

## Verification and limits

285 relative file links in changed Markdown resolve; four EN/PL installation/native mirror pairs
match byte-for-byte; current artifact versions match0.26.0. git diff --check PASS. No executable,
configuration defaults, runtime/model pins, approved workbook, original legal/brand asset, earlier
checkpoint evidence or immutable installer changed. Documentation-only: no new product build,
Actions execution, model download, paid/API call or public publication. Existing0.26.0 runtime
qualification remains unchanged; physical AMD inference is still unperformed. No application
quality/inference suite rerun is needed for prose/navigation changes. Later builds will include the
updated bundled help; the already delivered0.26.0 installer retains its verified original bytes.

## Next steps

Use the opening table in docs/99-roadmap-v2.md and immediate TODO: handle concrete new Snap/update
feedback if supplied; final release consistency review (docs/notices/credits/licenses/metadata),
final source/version/notes/artifacts/SHA256 and large-EXE storage at requested releases/ location,
then deliberate public tag/release/assets and actual download/bootstrap verification. Signing and
artist work are parallel/non-blocking; screenshots wait for artwork. Physical AMD, profile/zoom,
research and feature nice-to-haves are not new completion gates. No first-public-release version
or publication date is promised by this documentation task.
