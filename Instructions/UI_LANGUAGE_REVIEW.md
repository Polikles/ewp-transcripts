# Interface-language review (task 10)

Owner authorized this handoff on 2026-11-22 after accepting the focused workflow checks. Final
unique-save-name and short key-dialog feedback corrections need automatic verification only;
no further owner manual retest. This review precedes the full manual rewrite.

The initial editable file is local, outside Git:
`/home/linuch/project-ewp/deliveries/ewp-ui-en-pl-review-2026-11-22.xlsx`.
The first sheet contains Polish editing instructions. Edit EN and/or PL; use Notes for removals,
context-specific alternatives or broader requests. Preserve IDs, sheet/header names, placeholders
such as `{value_1}` and diagnostic codes. Do not delete rows or edit the hidden `_baseline` sheet.

The workbook groups current UI, dynamic Templates, Diagnostics and Quick guides. Other catalog
keeps entries not found in current literal usage, including rare/history copy. Backend details
keeps deeper technical text often displayed only in JSON. Context lists source files/line numbers
and DOM fields where available. A shared text ID can cover several occurrences; the source-review
Apply button has a separate field ID because its Polish copy overrides the global Apply label.
External OS/provider response text and user transcripts have no fixed built-in caption to edit.

The exporter records the base Git commit and a SHA256 of the actual Python/JS/guide source snapshot.
IDs and hidden originals bind owner edits to that snapshot, including the final polish. The draft
covers all 984 effective exact catalog entries plus source literals, dynamic formatter rules,
error-code fallbacks and quick-guide metadata. It preserves missing/same-language copy for review;
it does not invent translations before owner approval. Historical/technical entries are separate.

## Optional extraction and validation tools

`tools/export_ui_review.py` requires optional openpyxl, tree-sitter, tree-sitter-javascript and Node.
Install these in a disposable tool environment, not the application environment; runtime dependency
pins do not change. A Playwright tool environment can supply its driver Node executable.

```text
<tool-python> tools/export_ui_review.py --node <node-executable> --output <outside-repo-new-file.xlsx>
<tool-python> tools/check_ui_review.py <edited-file.xlsx> --diff-output <local-changes.json>
```

Extraction reads repository copy only and executes the existing formatter in an isolated Node
context, without app startup, credentials, private media or provider calls. It refuses to overwrite
an existing file. The validator checks row identity, placeholders/codes and formula-free text;
it reports changes without modifying the program. It accepts owner corrections in either language.
Keep returned changes and the original workbook together until the corrections are applied.

## Agreed next steps

1. Owner edits the local workbook and returns the corrected file.
2. Apply EN/PL corrections to the program and validate affected workflows/copy. Commit the approved
   table as the maintained reference for later revisions/translations.
3. Owner approves the resulting interface wording.
4. Review/update English documentation.
5. Review/prepare full Polish user documentation.
6. Create a NEW artist review package reflecting the approved GUI and language changes. The original
   already-sent ZIP stays unchanged now; this later new-package step is explicitly authorized.

Screenshots still wait for the final custom icons. Uninstall/installer work remains deferred.
Do not rerun paid ASR pilots, installation or model preparation for this terminology review.
