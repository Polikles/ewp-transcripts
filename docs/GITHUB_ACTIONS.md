# GitHub Actions: builds, Windows checks and costs

Last checked: 2026-11-26. Workflow: [distribution.yml](../.github/workflows/distribution.yml).
Repository visibility was verified through GitHub's repository API: **public**.
Public source visibility is separate from publishing the first versioned product release.

## Why the project uses Actions

Actions has been part of managed installer development since commit `2ece817` on2026-11-23.
The Linux development VM can cross-compile Windows executables but cannot establish that WPF,
WebView2, Windows paths, shortcuts or process-lifetime handling actually work on Windows.
GitHub-hosted Windows machines provide those checks. This external service and its resource use
should have been explained to the owner before use; this page records the missing explanation.

There is one workflow, **Installer build and Windows startup**:

| Job | Runner | Purpose | Timeout |
| --- | --- | --- | --- |
| `build` | Standard `ubuntu-latest` | Prepare pinned tools; run installer transaction tests; build versioned Windows/Ubuntu bundles and the Windows installer/desktop EXE | 25 minutes |
| `windows-startup` | Standard `windows-latest` | Verify hashes; launch the actual WPF installer; check Windows filesystem/lifecycle behavior and the actual desktop window/renderer | 10 minutes |

It starts on manual `workflow_dispatch` or a push to `main` matching the paths listed in the YAML:
installer/desktop sources, their build/tests, selected GUI/runtime/model-setup files and the version.
It has no scheduled trigger, automatic public release, deployment, tag creation or publishing step.
The token has `contents: read`; referenced GitHub actions are pinned by full commit SHA.

The CI checks use synthetic data and small non-ML GUI dependencies. They do not download speech
models, run GPU inference, send recordings to a provider or replace the owner's Windows acceptance.
Installer/desktop test builds and reports are temporary Actions artifacts, not public release assets.

## What is free and what must be checked separately

Standard GitHub-hosted runner compute is free in public repositories and does not consume the
private-repository compute allowance. Our two runner labels select that category. Larger runners
can be billed even for public repositories. Private/internal repository compute has different
allowances and overage rules. See [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

Artifact storage is a separate resource from runner compute. GitHub documents plan-dependent
storage allowances, sharing with Packages, and hourly storage accounting. Free compute alone is
not evidence of unlimited storage or of an owner's final invoice. This audit cannot inspect the
owner's plan, payment method, other repositories' consumption or account-level budgets. No account
billing settings were changed. Review actual charges and applicable allowances in
[account Billing](https://github.com/settings/billing), using the Actions/storage breakdown.

To prevent paid overages, review an Actions budget with a zero paid-spend allowance and enable
**Stop usage when budget limit is reached**, where available. An alert-only budget does not stop
usage. This is an owner-account setting, not something enforced by a workflow YAML. Follow
[GitHub's budget instructions](https://docs.github.com/en/billing/how-tos/set-up-budgets).

## Artifact footprint and retention

A read-only API inventory on2026-11-26 covered all37 workflow runs:74 non-expired artifact archives,
with a summed reported size of6,644,097,972 bytes (about6.64 GB /6.19 GiB). No runs were active.
This includes failed/superseded development candidates. It is an archive-size snapshot, not a
billing report, accrued GB-hours or proof that this amount is chargeable.
The [content-free audit snapshot](evidence/2026-11-26-actions-cost-audit.json) records archive IDs,
reported sizes and existing expiry dates.

| Artifact | Contents | New uploads retained |
| --- | --- | --- |
| `installer-test-package` | Versioned bundles, installer, bootstrap scripts, README and SHA256SUMS | 7 days |
| `native-windows-startup-evidence` | Installer report, synthetic desktop reports and rendered previews | 7 days |

Before this change, packages requested14 days and evidence used the account/repository default;
the latest evidence archive had a90-day expiry. Setting7 days applies to **new uploads**; it does
not retroactively change or delete the74 existing archives. No remote artifacts were deleted.
Accepted owner deliveries remain separately preserved on the project VM with their checksums.
Actions artifact expiry must not remove that handoff copy. Retention follows
[GitHub's artifact documentation](https://docs.github.com/en/actions/tutorials/store-and-share-data).

The workflow does not configure `actions/cache`, a larger runner, a GPU runner, custom VM images
or a paid marketplace service. An Ubuntu job's temporary NuGet/uv files are job-local; they are not
an Actions cache retained between runs.

## Controls and future changes

- Both jobs run only when the event identifies a public repository. If visibility becomes private,
  the jobs are skipped until the owner reviews billing and explicitly authorizes a different policy.
- One run per workflow/ref is allowed; a newer run cancels an older in-progress run for that ref.
- Both artifact uploads explicitly request7-day retention. Existing archives keep their old expiry.
- No payment method, paid budget, cache quota or repository-level billing setting is enabled by code.
- Explain a new external CI service or runner/storage billing change before using it; obtain approval
  before enabling potentially billable execution or increasing a paid allowance.
- For documentation/CI-administration-only commits that need no cloud execution, `[skip ci]` can
  suppress push-triggered runs. It must not replace required runtime qualification. See
  [skipping runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs).
- If the owner wants all automatic runs stopped, remove the `push` trigger and retain manual dispatch,
  or disable the workflow in repository settings. That is not the current configuration.

The initial documentation/guardrail change did not rebuild or replace0.25.0. That application package is
still sourced from `9b8da316fc0a87fceebaf824f0342dc43788f004`, qualified by run `45811242398`.
The owner subsequently reviewed it and requested window/personalization/player corrections for0.25.1.
The owner reports $0.89 consumed usage minus $0.89 discounts = $0 billable, with spending limits set0;
this is owner-supplied account information, not an API billing audit. The documented public standard
workflow is used for actual Windows qualification of the corrections. Next: focused review/fixes, then AMD support marked
**(experimental)** without a claim of physical AMD validation, remaining release tasks, and only
then the first public product release.

## Window/personalization follow-up builds — 2026-11-26

Three standard public runs were used for0.25.1, with7-day retention and the existing zero-budget
owner controls unchanged. No model/provider jobs or paid runner were introduced.

| Run | Result and purpose |
| --- | --- |
| [45883926205](https://github.com/Polikles/ewp-transcripts/actions/runs/45883926205) | New native test incorrectly attempted a DWM setter-only property getter; installer/filesystem and initial geometry checks passed. |
| [45884667195](https://github.com/Polikles/ewp-transcripts/actions/runs/45884667195) | Passed corrected API checks and full-window captures; visual review found the thin color-input swatch. |
| [45885593097](https://github.com/Polikles/ewp-transcripts/actions/runs/45885593097) | Final readable swatch, full native regressions and delivered0.25.1. |

Matching content-verified installer/evidence copies are preserved on the VM independently of Actions
expiry. The initial two candidates were not handed to the owner. Final source and artifact hashes
are recorded in the [qualification evidence](checkpoints/2026-11-26-window-personalization-evidence.json).
These job results do not establish any new account-level invoice total.
