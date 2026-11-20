# Immediate work queue

Updated: 2026-11-20. Start here after a context reset.

Policy: [WORK_POLICY.md](WORK_POLICY.md). Product sequencing and the complete retained inventory:
[roadmap — owner scope](docs/99-roadmap-v2.md#owner-scope-and-current-status--2026-11-20).
The owner is building a podcast/recording workflow tool. Optional research does not block delivery.

## Delivered: summary footnotes and scope reconciliation

Checkpoint: [current work](docs/checkpoints/2026-11-20-scope-and-summary-polish.md).

- [x] Make language (*) and speaker-count (**) footnotes span the summary width and remain below Inspect and Dry-run tables.
- [x] Rename the queue confirmation to reviewed plan / add jobs in EN/PL; vertically center the source section counter between navigation buttons.
- [x] Record owner acceptance: current GUI accepted with profile exchange untested; workflow passed except restart recovery; browsers/palette passed; actual 200% zoom not established.
- [x] Remove accurate percentage/ETA calibration as a delivery requirement; retain simple activity feedback and existing optional estimates.
- [x] Defer a complete editable EN–PL string-pair file until feature completion, then owner approval, then Polish docs; screenshots wait for final custom GUI/icons.
- [x] Mark artist delivery waiting without a deadline or blocking other work; leave sent ZIP/demo untouched.
- [x] Move research benchmarks, private/public universal-corpus work, translation model sweeps, model benchmark automation and hardware presets into an optional nice-to-have list outside delivery gates.
- [x] Document RTX 3090 owner-tested hardware and an unqualified expectation of at least 8 GB VRAM; retain native Windows as planned convenience work.
- [x] Audit roadmap, requirements, plans, ADRs and operator docs for other open items; reconcile statuses and report retained versus optional work without inventing priorities.
- [x] Verify the small UI changes, update changelog/checkpoints, and deliver application/planning updates.

## Owner acceptance and remaining checks

- [x] Owner accepts recent GUI/workflow changes, subject to the small fixes above.
- [x] Owner accepts the complete workflow except restart recovery; retain earlier accepted
  recovery evidence as history rather than claiming a current restart test.
- [x] Owner confirms browsers and palette work.
- [ ] Owner check still open: recover the latest workflow after a full program/VM restart.
- [ ] Optional owner check: complete user-profile import/export transfer. Provisionally accepted
  as implemented; the owner has not fully tested exchange. Automated coverage already passes.
- [ ] Optional display check: actual browser zoom 200% (page magnification, not window resizing).
  Not established by the owner's report and not a newly imposed blocking gate.
- Precise percentage/ETA calibration is removed from required work. Keep elapsed/activity feedback
  and the existing optional approximate ETA; no accuracy study is scheduled.

## Retained product work — ordering not yet agreed

- [ ] Prioritize roadmap R01–R15 and recovered proposals E01–E13 with the owner; do not implement
  the whole inventory automatically. Native Windows build/installer remains planned (R12).
- [ ] At feature completion, produce a complete editable EN–PL string-pair file for all labels,
  messages, errors, states, hints, tooltips and dynamic templates; preserve original error codes.
- [ ] After the owner corrects and approves that file, finalize terminology and full Polish docs.
- [ ] Screenshots are deferred until the final custom GUI/icon set is integrated.
- [ ] Integrate artist feedback/icons when supplied. No deadline; does not block other work.
  Leave the already sent frontend ZIP/demo unchanged.

## Nice-to-have — outside required project scope

Previous summary references 10/11/12/14: private-corpus benchmark expansion, comparative correction
and translation studies, public datasets/universal dictionary research, automated model benchmark
matrices. Previous item 13: hardware presets and GTX 1070/CPU-only/Apple Silicon qualification.
No such campaign is required for current completion. Ordinary regression/security/packaging checks
remain required. See the authoritative roadmap for details rather than a duplicate research queue.

## Delivered history

- [Batch planning, sentence-aware review and portable profiles](docs/checkpoints/2026-11-20-batch-sentences-profiles.md)
- [Mixed playback, progress and artist reference](docs/checkpoints/2026-11-19-review-mix-progress-artist.md)
- [Artist package sent for review](docs/checkpoints/2026-11-19-artist-review-package.md)
- [Playback and video](docs/checkpoints/2026-11-19-playback-video-progress.md)
- [Brand/palette and feedback](docs/checkpoints/2026-11-19-gui-review-and-brand-feedback.md)
- [Polish UI and recovery fixes](docs/checkpoints/2026-11-18-gui-localization-and-recovery.md)
- [Workflow polish](docs/checkpoints/2026-11-18-gui-workflow-polish.md)
- [Guided workflow](docs/checkpoints/2026-11-18-guided-workflow.md)
- [Native dependency repair](docs/checkpoints/2026-11-18-gui-dependency-repair.md)
- [Resolved launch diagnosis](docs/checkpoints/2026-11-18-gui-launch.md)

The repaired local-only ASR/source-export path on WSL/RTX 3090 and the later MP4/mixed playback
owner successes remain accepted. GUI-55 stays closed. Do not tag/publish a release as part of this
planning update. Do not reopen delivered work merely because a historical plan calls it future.
