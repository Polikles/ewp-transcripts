# Managed distribution — current contract, 2026-11-27

The agreed EXE/terminal implementation is delivered; compressed ~142 MB size is accepted and
further slimming/minimal downloaders are closed. Early public releases may be unsigned; mandatory
pre-release signing is withdrawn. Later free OSS/owner-approved Actions signing keeps actual
procedure/private keys outside Git. Follow [release policy](RELEASE_POLICY.md),
[checklist](RELEASE_CHECKLIST.md) and [revised roadmap](99-roadmap-v2.md).

Prioritize production attestations early. Plan startup Quick update/Repair/reinstall/Download newer
installer plus Other actions based on detected version. The proposed releases/ metadata plus Release
assets design awaits owner agreement because current EXE exceeds ordinary Git's100 MiB file limit.
Required GH Pages follows first release under the latest sequencing statement. MSIX/Store is a
separate [post-release channel research task](MSIX_STORE_PLAN.md), not an EXE replacement. Preserve
usable installed CLI and review pipeline documentation when discovery/packaging changes.

## Delivered behavior to preserve

1. **Versioning:** one dynamic application version, unique immutable build per handoff, compatible
   schema/model identities kept separate, clean-source manifests/checksums and recorded provenance.
   [Version policy](VERSIONING.md) remains authoritative; never overwrite a published version/tag.
2. **Managed lifecycle:** verified fixed bundles, safe roots/ownership, prepare/verify before atomic
   activation, retained usable previous release/rollback, explicit update/repair and no silent work.
3. **Preservation:** source recordings, publications, drafts/workspaces/dictionaries/profiles,
   OS keys and unchanged model snapshots survive ordinary updates/removal defaults. Unknown added
   files/shared caches are protected; optional model/key removal targets exact recorded assets.
4. **Preflight:** supported x64 OS, CPU/disk/runtime/permissions plus [GPU/driver/VRAM policy](HARDWARE.md).
   Existing-install detection happens before download/mutation. Required checks are automatic;
   folder changes refresh disk while preserving other results. Unsupported local hardware gets
   cloud guidance; unqualified smaller compatible GPUs get a warning, not a silent readiness claim.
5. **Explicit downloads:** pinned app/native dependencies and deliberately selected model versions,
   visible progress/cancellation/recovery, gated HF terms/transient token only where needed. Optional
   OR key uses the same deliberate OS store; this never grants audio/text upload consent.
6. **Windows wizard:** operation-specific pages, EN/PL reviewed copy, native accessibility, staged
   and measured download progress, persistent technical log, dated reports, icon/shortcut/registry
   size, restricted installed maintenance, selective model repair/addition and actual older rollback.
7. **Windows desktop:** owned WPF/WebView2 window without console, repeat launch focuses it,
   durable save/close and busy choices, safe-save refusal, process-job cleanup, theme/placement.
   Update/removal requests safe close; only the running uninstaller cleans itself after closure.
8. **Terminal packages:** Windows and Ubuntu24.04/26.04 no-checkout install/update/repair/removal;
   private Python/uv/native tools as needed. Online entry scripts have fixed hashes but require a
   matching PUBLIC release. Current internal files are unsigned and do not make guessed URLs valid.

## Qualification boundary

Owner Windows install/update/models/removal and application passes are retained separately from
model-free CI filesystem/UI tests. Ubuntu VM lifecycle evidence does not itself qualify bare-metal
GPU inference; WSL/RTX3090 and native Windows owner evidence retain exact scopes. No new broad
manual/model/provider campaign is required. Current [checkpoint](checkpoints/2026-11-27-nvidia-docs-audit.md)
and preceding qualification files state tested versions and unavailable hardware honestly.

Artist availability is non-blocking; complete illustrated docs follow artwork integration and interface tests. Local Scribe/MAI,
GTX1070/legacy tests/collectors, more installer slimming and Docker are not current obligations.
Ollama and remaining optional enhancements are AFTER the first public release. All original plan
clauses/numbering are preserved in [verbatim historical plan](../archive/project-status/2026-11-27-DISTRIBUTION_PLAN.txt).
