# Complete installer text table — 2026-11-25

## Request and boundary

Owner requests a complete editable correction table for installer EN/PL after waiving further
functional manual retests. Baseline `f36f1e87b5c871d760da1fc956e4c409513a3b3c`;
product **0.24.2**, source `7178bc7478897016e9663905739adb48afe73c00`.
This task inventories copy; no product wording/version/help changes, build, release, provider,
model downloads or transcription campaign. Prior mixed-model/uninstall/native acceptance remains.

## Delivered

- [x] Current UI strings from every installer operation, modal HF/OR instructions, tooltips,
  startup/errors, operation titles, progress/downloads/ETA, report save and folder/disk checks.
- [x] Complete composed sentences in addition to source fragments; variable names retained.
- [x] Own shared Python/PowerShell/shell installation/removal/doctor messages and report/log text.
- [x] Project notices/credits/asset terms with flags for internal or misleading prose; original
  third-party/legal text separately and 12 exact original files from the actual shipped ZIP.
- [x] XLSX with filters, frozen headings, wrapped EN/PL, edit colours, decision dropdowns,
  context/source/parameter columns, hidden original columns and a hidden original baseline.
- [x] UTF-8 BOM semicolon CSV with the same columns/data; complete read-only HTML preview,
  Polish instructions, coverage/verification JSON, checksums and ZIP.
- [x] Preserve all 179 historical IDs (163 active, 16 archive), legacy installer CSV and
  owner-approved application XLSX. Product and immutable installer packages unchanged.

Packet directory:
`/home/linuch/project-ewp/deliveries/ewp-installer-text-review-2026-11-25`.
Archive alongside: `EwP-instalator-teksty-do-korekty-2026-11-25.zip`.
Repository references: `docs/installer-copy-review/` (XLSX, CSV, README, full templates,
coverage and verification); generator `tools/build_installer_copy_review.py`.

| Sheet | Rows |
| --- | ---: |
| Interfejs | 179 |
| Pelne_komunikaty | 57 |
| Raport_i_terminal | 237 |
| Notices_projektu | 61 |
| Oryginalne_licencje | 569 |
| Linki | 15 |
| Dane_i_formaty | 14 |
| Archiwum_ID | 16 |
| **Total** | **1148** |

Unlocalized current messages have English in both columns, explicitly labelled as current reality,
not a proposed translation. Project flags include internal instructions/private brandbook references,
review-draft wording, creator-URL TODO and API post-processing wording omitting cloud ASR.
No author attribution, licensing permission or legal change has been invented/applied.

## Verification

- [x] Actual XLSX write/load and CSV round-trip: all 11 columns match for every row; all IDs unique.
- [x] Independent source count: all **175** direct T literal calls included, plus **5** credential
  result pairs. **1075** production C# literals classified with source/hash bindings.
- [x] Python message bindings: 153; shell/PowerShell prose bindings: 90 (deduplicated in table).
- [x] 57 full templates have matching EN/PL placeholder sets and unique template keys.
- [x] C# lexer fixture covers comments, escaped newline/comma, verbatim quotes and raw text.
- [x] Workbook has no formulas; filters, wrapping, hidden originals, freeze panes, row heights
  and merged instruction title checked. No Excel/LibreOffice available: **no native Excel render
  claimed**. Full HTML preview supplied; workbook layout metadata and data round-trip checked.
- [x] All 12 original notice files byte-identical to shipped ZIP and manifest SHA-256.
- [x] Approved app workbook byte-identical to HEAD. Legacy CSV Git content unchanged (checkout
  CRLF vs repository LF normalized for comparison); no product-source edits.
- [x] Generator Ruff check and format pass; review ZIP integrity check pass.

Reproduction: disposable Python environment with `openpyxl==3.1.5`, command in
`docs/installer-copy-review/README.md`. No product dependency changes. Detailed checks in
`verification.json`; literal classifications/input hashes in `coverage.json`.
No full product gate required for this documentation/inventory-only task; prior 0.24.2 gates retained.
Variable third-party stderr, remote responses and Windows dialog text are outside a finite project
copy inventory. Existing application copy workbook and full offline manual prose are separate.

Delivery hashes (SHA-256):

```text
7b6448a8d0eab3ab13452b4576e38303c1b2eaf083da715e90ad88f4d97ec440  EwP-instalator-EN-PL-do-korekty-2026-11-25.xlsx
e83e674f61570f4616e0ffec56cf92b620fd3f1638b25f327027217e4ee0edd0  EwP-instalator-EN-PL-do-korekty.csv
0fa9a3104234125fa87c30f350e5d348d66a322c36f66bb7cdbfd52337191e59  EwP-instalator-teksty-do-korekty-2026-11-25.zip
```

## Next

- [ ] Owner returns corrected workbook/CSV; keep this initial reference immutable.
- [ ] Compare by stable ID against original columns, resolve questions/full-template versus fragment
  conflicts, integrate approved EN and PL, synchronize affected offline help and verify layout.
- [ ] Native Windows app interface/lifetime after installer copy closure; public release/signing later.

Do not start these dependent steps, a new build or another manual/model/paid campaign on resume
without the returned copy or new owner instructions. Temporary review environment is removed after
delivery; no background server was started. Follow opening TODO and WORK_STATUS.
