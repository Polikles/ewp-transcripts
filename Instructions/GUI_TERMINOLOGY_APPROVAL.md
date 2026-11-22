# Interface terminology approval

Latest follow-up: the owner accepts the interface generally. Complete the small
[Windows startup/live-queue retest](GUI_WINDOWS_REFRESH_RETEST.md) after the startup correction;
preserve passed wording checks rather than repeat the entire language review below.

Owner corrections are integrated from the returned EN/PL workbook. This step approves the updated
interface wording before the English-documentation review and full Polish manuals. It does not
require reinstalling, downloading models, rerunning paid ASR or repeating the full workflow.

1. Stop the old GUI server, `git pull`, run `uv run --locked transcriber gui`, then Ctrl+F5.
2. In Polish, review the main workflow stages, Dictionaries, Saved work and Settings & About.
   Check the shorter messages, descriptions/tooltips and the key dialog. Dictionary quick steps
   and numbered headings now share `Wyświetl i porównaj wersje`; queue legends use `Opis:`.
3. If you have saved results, open source/translation review to inspect speaker labels, statuses
   and hints. Existing review/export operations and data formats are unchanged. There is no need
   to create a new cloud candidate or repeat ASR merely for copy approval.
4. Switch to English and back. The edited English wording should appear immediately; keys,
   recording/target languages, filenames and transcript text must remain unchanged.
5. Open a Full instructions link from Polish. Navigation chrome follows Polish, while the full
   article is still English and identified as such. The full manuals come after interface approval.
6. Review the few [integration adjustments](../docs/ui-language/README.md#integration-adjustments-for-approval).
   Approve the interface or return further corrections using the stable IDs in the committed
   [workbook](../docs/ui-language/ewp-ui-en-pl-review-2026-11-22.xlsx) / [CSV](../docs/ui-language/en-pl.csv).

After approval the order is EN documentation review/update → complete PL user documentation →
NEW updated artist package. The already-sent archive remains unchanged during this review.
