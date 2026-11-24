# Reviewed interface copy

2026-11-24 maintenance: four existing IDs now describe automatic startup recovery rather than
opt-in 60-second saving; two explicit startup diagnostics added. CSV/workbook/runtime agree;
original hidden owner baselines and all other IDs remain unchanged. See integration.json.

Status: owner corrections integrated and the resulting interface approved on 2026-11-22 (focused checklist 1–5 PASS).
The source workbook returned on 2026-11-22 contains 2218 stable IDs and 106 changed rows
(18 English changes and 105 Polish changes; some rows change both).
The maintained reference now has2219 IDs: the owner-requested transcription-tool subtitle keeps
its existing ID, and a new `GUI_INITIALIZATION_FAILED` diagnostic distinguishes browser setup from
server reachability. `post_review_changes` records this startup follow-up.

- `ewp-ui-en-pl-review-2026-11-22.xlsx`: integrated review workbook, including original hidden
  baselines and integration notes; author metadata is normalized to EwP Transcripts.
- `en-pl.csv`: the same current EN/PL values, IDs, context and notes in UTF-8 for readable Git diffs.
- `integration.json`: submitted/applied values and provenance for each changed row, plus the derived
  quick-guide title synchronization. It records the returned workbook's digest without private paths.

The original returned workbook and the delivered initial workbook remain unchanged outside Git.
This directory contains language copy only, never media, API keys, provider payloads or transcript data.

## Integration adjustments for approval

| ID | Adjustment |
|---|---|
| `ui.cc74177199108e70` | Correct `tłuamczeń` to `tłumaczeń`; the return instruction names the transcription queue because that is the existing button target. |
| `ui.7f1d67f77e37fa4e` | Name the transcription queue in the return instruction, consistent with its English text and actual navigation. |
| `ui.bfc9393f9c5c5658` | Correct `podksatu` to `podkastu`. |
| `guide.dictionary.steps.1.title` | Use `Wyświetl i porównaj wersje` in quick-guide metadata, matching the reviewed numbered heading. Otherwise late metadata loading overwrote the correction. |

These adjustments preserve behavior. Other submitted edits are applied as supplied, including
English revisions. Full-message translations take precedence over generic error-code descriptions;
unknown variants retain the existing diagnostic fallback. Placeholder values and codes stay intact.

## Approval boundary and next work

Use [the focused language approval checklist](../../Instructions/GUI_TERMINOLOGY_APPROVAL.md).
This is an interface-language approval, not another installation, GPU or paid-provider benchmark.
The application carries the current UI language into help navigation. The documentation stage now supplies complete EN/PL help.

Interface approval is complete. Current sequence: review/update English documentation, prepare complete Polish user
manuals, then create a NEW updated artist package. Keep the already-sent original artist archive
unchanged. Retain stable IDs in future corrections; update this maintained reference and actual
copy together rather than regenerating IDs from edited English text.

Documentation availability update: `ui.1fce95c06b54480e` now reads Full instructions / Pełne instrukcje because full EN/PL manuals are bundled. The stable ID is unchanged; the maintained workbook, CSV and integration note agree. Original owner workbooks remain untouched.
