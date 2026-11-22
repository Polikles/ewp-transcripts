# Reviewed interface copy

Status: owner corrections integrated; the resulting interface awaits owner approval.
The source workbook returned on 2026-11-22 contains 2218 stable IDs and 106 changed rows
(18 English changes and 105 Polish changes; some rows change both).

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
The application carries the current UI language into help navigation; full help content remains
English until the documentation stages.

After interface approval: review/update English documentation, prepare complete Polish user
manuals, then create a NEW updated artist package. Keep the already-sent original artist archive
unchanged. Retain stable IDs in future corrections; update this maintained reference and actual
copy together rather than regenerating IDs from edited English text.
