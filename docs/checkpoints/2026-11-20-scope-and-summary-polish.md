# Summary footnotes and owner scope reconciliation

Date: 2026-11-20. Baseline: clean main 8b64329.

## Current task

See the active checklist in ../../TODO.md. Fix full-width persistent Inspect/Dry-run
footnotes (* language, ** speakers), plural plan confirmation and vertically centered section
counter. Reconcile all retained work against owner scope: a practical podcast workflow tool.

## Owner decisions

- Current UI accepted with the reported small fixes. Full profile exchange was not tested by owner.
- Full workflow tested except restart recovery. Browsers and palette accepted. Owner did not
  identify what actual 200% browser zoom means; do not claim that specific check was performed.
- Accurate percent/ETA calibration is no longer needed; progress primarily proves activity.
- At feature completion produce one editable complete EN–PL string-pair file for labels/messages;
  owner correction/approval precedes full Polish manuals. Do not generate a changing approval
  package now. Screenshots wait for final custom GUI/icons.
- Wait for artist without a deadline; this does not block other work. Do not change sent package.
- Previous summary items 10/11/12/14 (research/evaluation) and 13 (hardware presets) are optional
  nice-to-haves outside this project's required delivery. No general transcription research or
  universal Polish dictionary program. Native Windows remains planned convenience work.
- Docs: RTX 3090 tested; >=8 GB VRAM is an expectation without a compatibility guarantee.

## Evidence and next steps

Policies/current pointers read, baseline clean. Summary grid currently puts its explanatory p
in a single auto-fit column and only emits it for Inspect; batch settings keep * during Dry-run.
Top source navigation actions lack align-items:center. Next: implement small display fixes,
audit all plan sources, reconcile required/optional statuses, verify and deliver.

## Changes and recovered plan inventory

- Inspect/Dry-run render two full-width notes below all tables; * refers to selected language,
  ** to speaker count. Native single/batch views share notes. Plural confirmation and matching
  English error guidance retain exact-plan/hash/consent semantics. Source top/bottom counter
  alignment removes navigation feedback-wrapper padding without changing workflow behavior.
- TODO is reduced to current work/acceptance, retained backlog references and completed checkpoint
  links. The roadmap opening is authoritative: R01–R15 retain product proposals without assigning
  implementation order; E01–E13 record additional items found in other plans. Earlier milestone
  text/evidence remains historical, rather than silently discarded.
- Audit read/search covered docs/01/02/09/12/17/18/20/21/22/23/24/26/30/99, ADR-0014/17/20/21,
  development handoff/testing policy, operator/WSL setup and feedback plans. Recovered proposals:
  explicit cancellation; verified export downloads; searchable model catalog/favorites; opt-in
  model loading controls; Ollama adapter; OS credential store; conditional manual timing overrides;
  conditional speaker-chunk translation; workdir immutable creation/retention reasons; optional
  owned input snapshots; residual alignment spill; plain-language instruction review; optional
  audio-follow/current-block highlighting in the app editor. Feedback-guide questions such as
  bulk replacement are not automatically promoted to accepted implementation requirements.
- Owner decisions recorded consistently at current entry points and work policies: recent UI and
  workflow accepted with current restart/profile exchange caveats, browsers/palette accepted,
  actual 200% zoom optional/unchecked, accurate ETA study removed, research/presets outside required
  delivery, Windows native planned, feature-freeze → complete EN–PL file → owner approval → PL docs.
  Screenshots await custom GUI; artist is non-blocking/no-deadline, sent package untouched.
- Hardware docs say RTX 3090 24 GB was tested and >=8 GB VRAM is an unqualified expectation,
  not a proven minimum or compatibility/performance guarantee. No model/pin/runtime change.

## Verification checkpoint

make check PASS: 896 tests, Ruff/format/mypy (102 source files). Optional browser helper lint PASS.
Chromium 159 / Playwright 1.65.2 PASS for 24 summary variants (Inspect/Dry-run × EN/PL × themes ×
1440/960/390 widths): both notes span the grid and remain below every table; zero page overflow,
page errors or external requests. Eight top/bottom section-counter alignment cases PASS at
1440/960 widths in EN/PL. Tests use synchronized synthetic WAV inputs and public example results;
no ASR or external provider is invoked. Temporary verification root: /tmp/ewp-scope-summary.d3btur.
Wheel/sdist build passed offline; final resource identity and cleanup follow before delivery.

Final package gate PASS offline: wheel and source archive build; all 56 bundled resources match
source, nine guide routes work from the extracted wheel and no eager speech-model imports occur.
Final make check remains 896 passing tests; no new unit tests were added for these reversible
copy/layout changes. Dedicated browser geometry/actual Inspect/Dry-run checks verify the reported
symptoms. Artist ZIP SHA256 remains 1265a795495f37dd0e18b88d57a80bee502dbb707e55289a55551f17b451f6f1.

## Delivery and resume

Delivered to origin/main in 159cb1f (fix(gui): align summary notes and reconcile owner scope).
All authorized UI fixes, plan reconciliation and verification are complete. The dedicated
/tmp/ewp-scope-summary.d3btur directory (browser environment, synthetic media, states, reports,
screenshot and package builds) was removed after recording content-free evidence. Test servers
were closed. The sent artist ZIP remained unchanged; no demo/builder was edited.

Next user decision is the order/subset of retained roadmap proposals R01–R15 and E01–E13.
No other feature implementation is automatically authorized by this planning update. At feature
completion prepare the complete editable EN–PL string-pair file, then owner approval and Polish
manuals; screenshots additionally wait for custom GUI/icons. Do not generate the approval file
prematurely or reinstate optional research/ETA accuracy as a completion gate. Latest owner restart
recovery remains unchecked; full profile exchange is provisionally accepted without a full owner
transfer test. Native Windows is explicitly retained planned work.
