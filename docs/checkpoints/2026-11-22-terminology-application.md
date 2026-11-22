# Apply owner EN/PL corrections and prepare interface approval

2026-11-22. Baseline clean maince9ddfc. Owner returned the original-named workbook in private
benchmark and explicitly requests integration, interface update/approval, then EN docs review,
full PL documentation and updated artist package. Preserve this gate; current work is integration.

Initial scan:2218 rows,106 changed rows, mostly UI plus two dynamic templates, quick guides and
catalog entries. Validate entire workbook/originals and inspect untruncated diffs before editing.
Do not read unrelated private files. Returned/initial workbooks remain unchanged. Commit corrected
language reference as requested, without private paths/runtime transcripts or credentials.

Temporary root /tmp/ewp-terminology-apply.RogGT6 for tool environment/browser/outputs; remove after
content-free evidence. No paid ASR/model/reinstall. Prior cumulative spend USD0.0291461230985028369.
Next: validate and classify changes; apply exact source/translation edits, verify coverage and
browser behavior, update plans/evidence/checkpoint, push main for owner interface approval.

## Integration and verification

- Returned2218 IDs/hidden originals exactly match delivered baseline. Validator accepts106 owner
  rows (18 EN /105 PL edits), with no changed placeholders/codes/formulas and no notes.
- English literals updated in runtime source, including template HTML. Reviewed static translations
  retain legacy English aliases; exact full coded messages precede generic code descriptions.
  Two dynamic captions and two quick-guide edits are applied. The dictionary quick-guide title
  also needed synchronization because its asynchronous metadata overwrote the reviewed heading.
- Two typos and two actual-queue-target hints across three rows are adjusted with explicit notes;
  navigation behavior is unchanged. See docs/ui-language/README.md for exact IDs/reasons.
- Reference XLSX/CSV contains2218 stable IDs; integration.json preserves original/submitted/applied
  values. Sanitized XLSX/CSV match. Applied workbook107 changed rows includes the derived title.
  Initial and returned local workbooks remain untouched. No private paths/media/keys in the reference.
- Help chrome now uses selected EN/PL, safely propagating an allowlisted locale through fixed help
  routes. Full English manuals stay unchanged for the next gate; no executable help scripts added.

Final make check:1050 tests, Ruff/format, mypy115 pass. Integration17 pass/4 deselected.
Full Chromium216 layouts pass at nine widths390–3840, EN/PL/light/dark. Focused browser coverage
passes all102 static reviewed messages,2 templates,2 reviewed quick guides,1 derived guide and4
help labels; four locale transitions and36 dictionary/saved/settings layouts pass with zero page
errors/external requests. Five changed JS syntax checks and helper Ruff/format pass. Polish
Dictionary screenshot inspected. No new native/GPU/provider qualification implied.

Optional copy scanner now uses actual JS string AST nodes: regex-only scanning falsely split
apostrophes/template HTML into fake untranslated copy. Browser tool environment needs tree-sitter
and tree-sitter-javascript, with no runtime dependency changes. Full-message/browser checks caught
the metadata overwrite; final checks pass after correction.

## Handoff

[Content-free evidence](../evidence/2026-11-22-terminology-application.json).
Next: owner pulls/restarts/refreshes and reviews interface copy with
[focused instructions](../../Instructions/GUI_TERMINOLOGY_APPROVAL.md). No reinstall/paid ASR needed.
Only after interface approval: EN documentation review/update, complete PL user documentation,
then NEW artist package. Original artist ZIP stays unchanged. Prior cloud spend is unchanged.
Disposable server stopped and `/tmp/ewp-terminology-apply.RogGT6` removed after evidence capture.
Original/returned workbooks and frozen artist archive are unchanged; reference workbook retained in
repo. No paid calls; cumulative spend USD0.0291461230985028369. Delivery targets main.
