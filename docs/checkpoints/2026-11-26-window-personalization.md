# Window personalization and review player — 2026-11-26

Status: delivered0.25.1 from1a665b33b24772f93c8c8aa7ec22c5a83a0aad08; final native45885593097
PASS. See Final delivery and matching evidence JSON below. Earlier paragraphs record intermediate
findings/candidates, not outstanding work. Await focused owner review; AMD/public release follow.

Baseline156a712, owner broadly accepts0.25.0 and requests four focused fixes (opening TODO).
Target0.25.1, preserve earlier workflow/model/notices/workbooks/delivery hashes and exact spend.
Owner billing confirmation: $0.89 consumed minus$0.89 discounts=$0 billable; all limits set0.
Implement before AMD experimental stage; no AMD or public release in this task.

Initial findings: desktop saves width/height only and forces CenterScreen; title bar is defaultDWM;
save/close message is top banner. Shared preferences exist in header/profile snapshots; no dedicated
personalization menu. Review CSS forcibly expands sidebar to22.5rem to fit audio controls, causing
stage layout shift. Reuse existing controls/palettes while keeping explicit per-recording application.

Owner clarification: the audio player MUST stay in the left recording sidebar. Limit its width
and retain the additional-options menu; do not relocate it into the main review section.

Implemented actual Win32 placement (position/normal dimensions/maximization, safe fallback), DWM
system/application/custom title bar, shared Personalization menu, portable-preference compatibility
and palette-conflict remapping, centered opposite-theme native shutdown popup. Audio stays after
the recording list; remove22.5rem review expansion, cap player and preserve the overflow menu.
ETA preference no longer gets cleared by workspace recovery's consent reset.

Browser qualification PASS62 checks: five widths390–1600, both themes, actual Chromium UA-shadow
overflow-button bounds and menu opening, no horizontal overflow or main-column shift, preference
reload/profile save-load, palette protection, system-theme changes and EN/PL. Inspected three
focused screenshots. See window-personalization-browser.json. Local C# cross-build passes.
Initial local gate1205/19skips passes; after0.25.1 bump refresh editable package metadata before
final gate. Actual Windows/native qualification and immutable delivery remain pending.

First Windows run45883926205: installer46 groups and18 filesystem cases PASS; desktop stops at
the new caption-color getter assertion. Microsoft documents caption/text color as DwmSetWindowAttribute
options, not readable DwmGetWindowAttribute properties. Geometry/default/off-screen recovery and
existing keep-working/wait tests passed before that test error. Replace the unsupported getter
with actual setter HRESULT checks and whole-window PrintWindow previews (including native caption),
then rerun the Windows qualification. No product delivery from the failed run.

Second run45884667195 PASS (a806fe7):46 wizard groups,18 filesystem cases and4 desktop cycles
(49/50/50/50 assertions),105 previews. Bundle hashes/source and independent native EXE match.
Whole-window images show actual custom/application caption colors; shutdown cards are opaque and
opposite-themed. Visual inspection found the HTML color input rendered as a thin swatch because
of generic padding; give it an explicit44px height and4px padding. Final delivery remains pending
this small visual correction's build. Earlier0.25.1 candidate was not delivered to the owner.

Scratch path is in
/tmp/ewp-current-window-task. Only documented public standard Actions for final Windows checks;
no paid audio/model/provider campaigns. Old0.25.0 remains immutable.

## Final delivery

Source1a665b33b24772f93c8c8aa7ec22c5a83a0aad08, final Windows45885593097 PASS.46 wizard groups,
18 filesystem cases and4 actual desktop cycles pass, with49/50/50/50 checks. Local1205 tests/
19 Windows skips plus17 included integrations, Ruff/format306/mypy120 PASS; browser62 checks PASS.
105 native previews inspected in overview and10 affected full-size views. Sixteen full-window
captures have exact expected caption pixels (custom91/25/63, dark18/48/63, light245/242/233);
color input now shows a readable swatch. Save cards are centered/opaque and opposite-themed.
Native geometry is24/28–984/684 in the isolated fixture; normal restart and subsequent maximized
restarts pass, as do recovery from unavailable monitor positions, invalid/old records and repeat
launch after minimize. Durable-save refusal, paused work recovery, real descendants/console and
maintenance/crash cleanup remain covered. No GPU/provider inference is claimed.

Both CI archive digests, six product hashes, all bundle-manifest files and227 committed source/control
files per bundle verified (Ubuntu tar carries the exact verified nested ZIP). Desktop EXE matches
an independent build of the same source byte for byte. All74 earlier product hashes unchanged.
Final immutable delivery: /home/linuch/project-ewp/deliveries/ewp-0.25.1-installers.
EXE SHA256 516613e77b114ba60b2b5bc5b7513c487c239098bf87ba4e2d1b64c44e470f96; 216707128 bytes.
No candidate from earlier runs was delivered. See final evidence JSON for all six hashes.

Owner Actions billing report remains $0.89 consumed-$0.89 discounts=$0 billable, limits0. This task
used three standard public workflow runs with7-day retention; no budget/paid-runner changes.
Removed only completed task browser downloads/SDK archive to recover temporary quota. Earlier
owner installer/artist deliveries, approved copy/notices/assets/model pins and exact cloud spend
USD0.0291461230985028369 remain. Task scratch was removed after evidence was copied; the test backend was stopped.

NEXT: owner focused review, then AMD support marked(experimental), remaining release tasks and
first public release. No repeated full inference campaign, AMD work, public publication or signing
in this task. Final documentation may follow product source; do not rebuild merely for doc HEAD.
