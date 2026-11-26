# Hardware guidance, blank-window theme and installer size — 2026-11-26

Owner request: document recommended NVIDIA/VRAM hardware; queue future GTX1070/8GB,32GB RAM,
i5-10400F tests with possible measurement scripts. Owner accepts both left/right Snap restoration.
Fix initial/closing white or light-dark-light flashes using Windows theme on first launch and
saved app theme thereafter. Artist work remains independent. Signing is REQUIRED before first
public release; its procedure and all keys/credentials MUST stay outside Git. Prepare private
owner instructions in the VM home, without purchasing/generating certificates. Audit installer
bloat and evaluate a smaller online delivery. Remove local Scribe/MAI from the plan entirely;
Ollama and other enhancements follow public release.

Baseline ac50c57, product0.26.0/source6c5fbcd. Target0.26.1 if packaging/theme changes are delivered.
No physical GTX1070/AMD card available now; no inference or paid/provider campaign. Preserve prior
immutable packages, approved assets/copy/model pins and cumulative provider spend.
Implementation/research, actual size audit and qualification pending.

## Implemented candidate and local evidence

First blank surface follows Windows; cached explicit/system theme choice survives restart. WPF
shell and opaque WebView controller background are set before creation, renderer stays hidden
until the document loads, and successful shutdown hides it over the same themed shell. Existing
contrasting centered progress, safe-save refusal and worker ownership remain. Synchronous local
head script resolves stored/system theme before styles/deferred code in native and browser modes.
Native tests add startup/empty/closing captures and a sixth explicit-light restart.

Both self-contained .NET projects now compress assemblies. Actual baseline inventories show
0.24.4 EXE157323320bytes,0.26.0 EXE216719416bytes; desktop host accounts for59371920bytes in ZIP.
No model/ML wheel/cache/private corpus is embedded. Dirty local compressed candidate142183758bytes
(34.39% smaller) and desktop65419679bytes cross-build successfully; candidate discarded, not delivered.
See installer-size evidence and INSTALLER_SIZE.md for measured limits and bootstrap tradeoffs.

Hardware recommendations are in README, Settings & About and EN/PL manuals; current8GB target
remains unqualified. GTX1070 Pascal is incompatible with current torch2.8/cu128 binaries per
upstream policy; future tests first establish compatible kernels, then measure stages/peaks.
Physical PC unavailable; no dependency/model pin changed. All six touched help mirrors match.
Private owner signing instructions are in /home/linuch/EwP-podpisywanie-EXE-instrukcja.md (0600),
not tracked or copied into repository/delivery. No key/certificate purchased/generated or signing
procedure added to Git. Public release requires signing; artist non-blocking; local Scribe/MAI
removed; other optional enhancements after release.

After refreshing editable package metadata offline for0.26.1, full gate1223 passed/20 Windows skips,
including17 integrations; Ruff/format310/mypy122 PASS. Initial gate caught stale0.26.0 editable
metadata, not a runtime failure. Native clean-source qualification/delivery still pending.
