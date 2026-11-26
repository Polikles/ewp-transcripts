# Actions costs and product sequence — 2026-11-26

Owner asks why Actions was used without prior explanation, whether paid limits apply, and requests
project documentation. Desktop0.25.0 is not yet owner-tested. Baseline54feda7; product stays0.25.0.

Verified GitHub API: repository public;37 runs,74 non-expired artifacts,6,644,097,972 reported bytes;
no active runs, no failed inventory reads. Standard ubuntu-latest/windows-latest jobs, no larger/GPU
runner or Actions cache configured. Actions introduced2ece817 on2026-11-23. Package retention14 days,
evidence default (latest90 days). Invoice, plan/payment method and budgets are not accessible.
Official GitHub billing, budgets, retention, concurrency and skip-run docs checked; see linked guide.

Added docs/GITHUB_ACTIONS.md, README links and authoritative sequence in TODO/status/policy/roadmap.
Added public-only guards,7-day retention to both future uploads, same-ref cancellation. No old remote
artifacts removed, account budgets changed, private models/audio processed or cloud builds requested.
Use [skip ci] for this administrative commit, verify latest Actions run remains45811242398 afterwards.
Static YAML/guard/retention/concurrency/trigger/token and documentation checks PASS. Audit snapshot:
docs/evidence/2026-11-26-actions-cost-audit.json. No runtime changes or product rebuild needed.

Next: owner native-interface test → fixes → AMD implementation labelled (experimental), with no
physical AMD hardware available → remaining release tasks → first public release. Do not start AMD
or publication now. Preserve source9b8da31/0.25.0 delivery and all original hashes/accepted tests.
