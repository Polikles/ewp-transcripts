# Window personalization and review player — 2026-11-26

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

Scratch path is in
/tmp/ewp-current-window-task. Only documented public standard Actions for final Windows checks;
no paid audio/model/provider campaigns. Old0.25.0 remains immutable.
