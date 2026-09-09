# `EWP-REVIEW 1` Text Format

Status: accepted planned v0.2.0 format contract.

`EWP-REVIEW 1` is a UTF-8 plain-text interchange format for manual transcript correction.
It is intentionally not JSON. This document is the format schema: grammar, required
metadata, validation rules, and semantics.

## 1. Design goals

- readable and editable in ordinary text editors;
- deterministic mapping back to canonical words;
- bounded local alignment rather than whole-document alignment;
- editable speaker attribution without exposing a large JSON document;
- safe detection of stale or accidentally damaged review files;
- no manual timestamp maintenance;
- future GUI may hide all machine directives while using the same underlying semantics.

## 2. Encoding and newlines

- UTF-8 is required.
- Readers MUST accept LF and CRLF.
- Writers SHOULD emit LF.
- A final newline is recommended but not semantically significant.

## 3. File structure

```text
header
blank line
anchor section+
```

A generated review file contains one header followed by one or more anchor sections.

## 4. Header

The header begins at line 1 and ends at the first blank line.

Required fields:

```text
# EWP-REVIEW 1
# job_id: <job id>
# base_result_file: <filename or relative path hint>
# base_result_sha256: <64 lowercase hex characters>
# base_result_schema_version: <schema version>
# base_result_version: <positive integer>
# language: pl|en
# generated_at: <RFC 3339 timestamp>
# application_version: <application version>
```

Optional fields reserved for review files prepared from a previous revision:

```text
# source_revision_id: <UUID>
# source_revision_sha256: <64 lowercase hex characters>
# source_revision_number: <positive integer>
```

An optional revision-scoped display-name map may be added by the GUI:

```text
# speaker_labels: {"speaker_001":"Szymon","speaker_002":"Damian"}
```

The value is one compact JSON object. It may override a speaker already present in the canonical
result or introduce a revision-local `speaker_NNN` identifier for text manually reassigned during
review. It applies only to the editable review and any immutable revision created from it; it
never changes canonical speaker IDs or the canonical ASR artifact.

`base_result_file` is a resolution hint only. `base_result_sha256` is authoritative.

Unknown header keys beginning with `x_` MAY be preserved by readers. Unknown non-extension
keys SHOULD be rejected so accidental spelling errors do not silently disable validation.

## 5. Anchor sections

Each section begins with:

```text
@@ anchor <first_word_id>..<last_word_id>
```

and MUST contain at least one speaker directive:

```text
@@ speaker <speaker_id>
```

Editable transcript text follows the active speaker directive until another speaker or
anchor directive.

Example:

```text
@@ anchor word_000101..word_000180
@@ speaker speaker_001

This text belongs to the first speaker.
It may be rendered one sentence per line for readability.

@@ speaker speaker_002
Exactly.

@@ speaker speaker_001
Then the first speaker continues.
```

## 6. Simplified grammar

The grammar below is descriptive EBNF. Lexical constraints in the following sections are
normative.

```ebnf
review          = magic, newline,
                  header-field, { header-field },
                  newline,
                  anchor-section, { anchor-section } ;

magic           = "# EWP-REVIEW 1" ;

header-field    = "# ", header-key, ": ", header-value, newline ;
header-key      = identifier ;
header-value    = printable-text ;

anchor-section  = anchor-directive,
                  speaker-block,
                  { speaker-block } ;

anchor-directive = "@@ anchor ", word-id, "..", word-id, newline ;
speaker-block    = speaker-directive, { editable-line } ;
speaker-directive = "@@ speaker ", speaker-id, newline ;

editable-line   = text-line, newline ;
word-id         = "word_", digit, { digit } ;
speaker-id      = "speaker_", digit, { digit } ;
identifier      = letter | "_", { letter | digit | "_" } ;
```

## 7. Anchor invariants

For a review generated from one canonical result, anchors MUST:

1. reference canonical `word_id` values from that exact base result;
2. be ordered by canonical word order;
3. have `first_word_id <= last_word_id` in canonical order;
4. not overlap;
5. not leave gaps between anchor ranges;
6. collectively cover every canonical word exactly once;
7. remain unchanged during normal manual correction.

A reader MUST reject a file when an anchor is missing, duplicated, modified, reordered,
overlapping, or references a nonexistent source word.

The anchor size is not a sentence or segment contract. Writers may place anchor boundaries
at convenient canonical segment, speaker-change, or pause boundaries near the configured
target size.

## 8. Speaker directives

A speaker directive sets the corrected speaker attribution for following editable text
until another speaker directive or anchor section begins.

The ID MUST exist in `base_result.speakers`.

Changing:

```text
@@ speaker speaker_001
Exactly.
```

to:

```text
@@ speaker speaker_002
Exactly.
```

is an intentional speaker reassignment.

v0.2.0 does not create new speaker identities through review syntax.

## 9. Editable text semantics

Only ordinary text is editorial content.

- punctuation remains part of ordinary text;
- ordinary line breaks are presentation whitespace, not explicit sentence boundaries;
- blank lines inside an anchor are presentation whitespace;
- sentence boundaries are inferred later from punctuation by transcript exporters;
- reviewers may change spelling, capitalization, punctuation, sentence boundaries, and
  words;
- reviewers may merge or split lexical words by editing spaces;
- reviewers may insert or delete words;
- meaningful repetitions are preserved unless explicitly edited.

When parsing one speaker block, ordinary whitespace between editable lines is normalized
to one separator for tokenization. The exact corrected token surface text, including
punctuation and capitalization, is preserved after tokenization.

## 10. Directive escaping

A literal transcript line beginning with `@@ ` is ambiguous with machine directives.
Writers MUST escape such a content line by prefixing one additional `@`:

```text
@@@ literal text beginning with two at signs
```

Readers remove one leading `@` from content lines beginning `@@@ `.

Any unrecognized line beginning exactly `@@ ` is an error rather than transcript text.

## 11. Review generation

A writer SHOULD:

- render corrected/current text in a sentence-oriented layout for human readability;
- keep anchor directives visually separated by blank lines;
- emit a new speaker directive whenever the source/effective speaker changes;
- target the configured approximate anchor word count;
- prefer nearby segment, pause, or speaker boundaries instead of splitting at an arbitrary
  position when this does not create excessively large anchors.

The writer MUST NOT derive authoritative correction timing or modify canonical data.

## 12. Source resolution

Apply/preview needs the canonical base result.

Resolution order SHOULD be:

1. explicit CLI/application path such as `--results-dir`;
2. the review file's relative `base_result_file` hint;
3. a same-directory exact filename match.

Regardless of discovery method, the candidate file MUST match `base_result_sha256` before
alignment begins.

## 13. Prepared-from-revision metadata

When a future workflow prepares review text from an existing revision, the header records
that revision's ID/hash/number. The editable text may therefore contain insertions or
corrections that were not present in raw ASR.

Anchors still refer to base canonical word ranges. A later full snapshot continues to map
corrected tokens to base words or insertion anchors, so the parent revision is not needed
to render the child.

When the source revision contains revision-scoped speaker labels, preparation carries them into
the child review header. A reviewer may replace them again in the GUI; a later immutable child
then records its own exact label map.

## 14. Alignment input

The review parser emits ordered units conceptually equivalent to:

```text
ReviewAnchor(
    first_word_id,
    last_word_id,
    speaker_blocks=[
        ReviewSpeakerBlock(speaker_id, text),
        ...
    ],
)
```

This parsed structure is the input to the common revision aligner used by manual review,
future LLM correction, and future GUI operations.

## 15. Validation failures

At minimum the parser/application must distinguish:

```text
REVISION_BASE_HASH_MISMATCH
REVISION_ANCHOR_INVALID
REVISION_SOURCE_WORD_MISSING
REVISION_SPEAKER_INVALID
```

A malformed review file MUST NOT produce a partial final revision.

## 16. Example

See [`../examples/review.example.txt`](../examples/review.example.txt).
