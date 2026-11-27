# Independent MSIX / Microsoft Store channel — post-release research plan

STORE-01 is research/planning AFTER first public EXE release, not a completed package or Store
submission. EXE distribution continues independently. Owner is a solo developer/natural person
seeking an Individual account; validate account/category/country/identity and current eligibility
with Microsoft rather than assume approval or submit personal data on the owner's behalf.

## Intended path and feasibility work

1. Assess full desktop MSIX for WPF/WebView2/Python/native GPU dependencies. Inventory all executable
   dependencies versus downloadable model/data assets; check current Store rules on dynamic code,
   permissions/capabilities, writable package paths and offline behavior. Do not simply wrap the
   EXE installer and assume its runtime/bootstrap/model mechanisms are Store-compliant.
2. Define Store package identity/publisher/version/build, signing and certification path. Microsoft
   documents Store signing/hosting/updates for MSIX, unlike publisher-managed EXE/MSI submissions.
   A directly downloaded standalone MSIX is a separate trust/update path; Store signing is not
   a promise that an arbitrary unsigned sideloaded MSIX installs or auto-updates.
3. Package the app without requiring models in the initial Store download, subject to clarification
   of the owner's phrase "local version only": does cloud ASR remain available before model setup?
   Store listing must separately state cloud-mode and fully local hardware/network/disk requirements.
4. Add a Settings-accessible optional local-model wizard: detect capability, explain tiers,
   explicit download/model/terms/token choice, measured progress/retry/cancel, verified revisions,
   diagnostics, repair/removal and safe cache locations. No silent downloads or upload consent.
5. Store updates own the app package; separate writable state/models/outputs so updates/removal,
   rollback/version compatibility and offline snapshots retain deliberate behavior. Research
   what Store uninstall removes versus intentionally external user files and credential entries.
6. Preserve usable CLI in the installed distribution for the planned tool pipeline. Research
   execution aliases/terminal invocation, subprocess/runtime paths, exit codes and headless use;
   review CLI/docs after implementation. GUI-only packaging is not acceptable.
7. Plan EXE/Store coexistence or explicit migration: duplicate installs/identity, shortcut/port/lock
   ownership, workspaces, OS keys, cache sharing and separation, safe transition/rollback. Store and
   standalone updaters must not modify one another's managed app files.
8. Prototype/build validation, Store certification checklist and user scenarios; release/update
   delivery and version migration tests. No automated Store submission or account creation here.

## Proposed FUTURE model-wizard tiers — not current installer behavior

| Owner category | Proposed scope |
| --- | --- |
| Does not meet requirements | Too old/unsupported architecture or less than6 GB VRAM. Exact compatible6–8 GB behavior is unresolved. |
| Experimental | Compatible AMD with8+ GB VRAM; compatible NVIDIA RTX30xx or newer with8 to less than12 GB VRAM. No physical qualification promise. |
| Expected to work | Compatible NVIDIA RTX30xx or newer with12+ GB VRAM. Exactly12 GB goes here to remove the overlapping boundary. Guidance, not universal guarantee. |

All capacity tiers must also intersect actual supported architectures/drivers/runtimes/models.
8 GB AMD alone is not proof that the HIP backend supports that card. Older NVIDIA generations,
6–8 GB, missing metadata, multiple cards and whether the same tiers should replace EXE preflight
need owner decisions. Unknowns must not be fabricated as supported; never sum VRAM across GPUs.
The current0.26.2 CUDA/CC preflight and12 GB recommendation remain unchanged by this plan.

## Deliverables

Feasibility/gaps report; Individual-account route; architecture/data-location/update/channel design;
hardware decision table; Store policy/license/privacy assessment; prototype/validation plan;
proposed CI and owner approval flow; effort/risks and go/no-go decision. No promise of Store
acceptance, free direct-EXE signing or autoupdate simply from producing an MSIX file.

Primary sources checked2026-11-27 (recheck at implementation):

- [Distribution/signing/update paths](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/choose-distribution-path)
- [Store accounts and MSIX publishing](https://learn.microsoft.com/en-us/windows/apps/publish/get-started)
- [Individual developer account](https://learn.microsoft.com/en-us/windows/apps/publish/partner-center/partner-center-developer-account?pivots=store-installer-msix)
- [Store policies/privacy/dynamic code](https://learn.microsoft.com/en-us/windows/apps/publish/store-policies-and-code-of-conduct)
- [Direct MSIX/App Installer updates](https://learn.microsoft.com/en-us/windows/msix/app-installer/app-installer-file-overview)
