# Transcript Revisions

Status: implemented on `main` for v0.2.0; single-episode and 24-episode batch operator
validation passed.

Machine-readable revision schema: [`../schemas/revision.schema.json`](../schemas/revision.schema.json).
Human review format: [`../schemas/ewp-review.schema.md`](../schemas/ewp-review.schema.md).

## 1. Purpose

The revision layer permits manual correction of transcript text and speaker attribution
without modifying or recreating the canonical ASR result. All corrected exports are
regenerated from one immutable revision snapshot.

`results.json` remains the immutable record of what the transcription pipeline produced.
A revision records what is currently accepted as corrected editorial text.

## 2. Source-of-truth hierarchy

Persisted authoritative artifacts are:

```text
canonical ASR result:  *_results.json
corrected snapshot:    *_revision_NNN.json
```

A review file is an editable interchange artifact, not an authoritative transcript.
`EffectiveTranscript` is a runtime view, not a persisted third source of truth.

The original canonical result MUST NOT be modified by prepare, preview, apply, edit,
audit, or revision-aware export.

## 3. Revision identity

Every revision MUST contain:

- `schema_version`;
- `application_version`;
- a UUID `revision_id`;
- a positive sequential `revision_number` allocated for the exact base result;
- `job_id`;
- creation timestamp;
- base-result metadata including exact SHA-256;
- optional parent-revision metadata;
- provenance;
- corrected transcript snapshot;
- alignment metadata;
- summary statistics;
- structured warnings.

A parent reference records lineage only. A complete child revision MUST remain exportable
without replaying or loading its parent.

## 4. Base-result verification

A revision is valid for a canonical result only when all required base identity fields
match and the SHA-256 of the exact canonical file bytes equals `base_result.sha256`.

Filename/path metadata is a discovery hint and MUST NOT replace hash verification.

A revision created from one result version MUST NOT be applied to another result version
merely because `job_id` is the same.

## 5. Corrected token model

The revision transcript is a sequence of corrected text tokens. Punctuation remains in
normal token text and is not represented as independent punctuation words.

Each token contains:

- stable token ID within the revision;
- exact corrected `text`;
- corrected `speaker_id`;
- zero, one, or many canonical `source_word_ids`;
- an insertion anchor when `source_word_ids` is empty.

Examples:

```text
1 -> 1    ordinary correction or punctuation-only change
N -> 1    source "Open" "AI" -> corrected "OpenAI"
1 -> N    one source token split into multiple corrected tokens
0 -> 1    explicit insertion between canonical words
N -> 0    represented by absence of corrected tokens for deleted source words
```

The full revision stores the final corrected state. It does not store a patch stream as
the reconstruction mechanism.

It also does not duplicate canonical segment objects. Segment text and boundaries are a
derived projection of the corrected tokens, speaker assignments, punctuation, and
canonical timing. Persisting both corrected tokens and corrected canonical-style
segments in one revision would create two editable representations that could disagree.

## 6. Speaker attribution

Every corrected token MUST reference a speaker that exists in the base canonical result.
The revision MAY assign a different `speaker_id` from the canonical word mapping.

This supports correction of short interjections assigned to the surrounding speaker.

An optional immutable revision-scoped display-name map may override the rendered name for a
known speaker ID or introduce a new, revision-local `speaker_NNN` ID for text manually separated
from an incorrectly attributed turn. It is intended for manual review when diarization supplies
anonymous or wrong names, misses a participant, or multiple people share one source channel. The
map travels through child review preparation and applies only to exports resolved from that
revision; it never changes the canonical ASR result or creates a cross-recording identity.

## 7. Sentence boundaries and punctuation

Reviewers edit ordinary punctuation in text. They do not maintain a parallel sentence
boundary structure.

TXT sentenceization MUST run on the selected effective transcript after revision
resolution. Therefore changing:

```text
No dobra wiesz co chyba tak.
```

to:

```text
No dobra. Wiesz co? Chyba tak.
```

is sufficient to regenerate three sentence lines in TXT.

Ordinary line breaks in an `EWP-REVIEW 1` file are presentation aids and MUST NOT override
punctuation-based sentenceization.

## 8. Timing inheritance

Canonical word timing remains immutable in normal revision work.

Revision JSON does not require reviewers or future LLMs to invent word timestamps.
`EffectiveTranscript` resolves timing from canonical source mappings:

- one-to-one tokens inherit the source word range;
- merged tokens use the envelope of all mapped source words;
- split corrected tokens mapped to one source word share one timing group;
- inserted tokens are attached to an adjacent effective timing group for subtitle
  planning and retain explicit insertion provenance rather than an invented canonical
  timestamp;
- deleted source words produce no corrected token.

An insertion across a configured long source gap MUST produce a warning because subtitle
placement is potentially ambiguous.

Manual timestamp overrides are outside the normal v0.2.0 contract and remain backlog
work.

## 9. Repetitions and faithful wording

The revision engine MUST NOT automatically remove repetitions, fillers, or
self-corrections. Alignment normalizations may assist matching but MUST NOT rewrite the
accepted review text.

A deletion is present only when the edited text actually removes source content.

## 10. Review preparation

`transcriber revise prepare` renders canonical content into `EWP-REVIEW 1`.

It MUST:

- accept one completed result or a directory of completed results;
- use deterministic natural ordering for batch input;
- ignore unrelated files rather than interpreting them as review sources;
- ignore subdirectories unless recursion is explicitly enabled;
- include base-result identity and SHA-256 in every review file;
- divide the source word timeline into ordered, non-overlapping anchors;
- prefer human-readable sentence-oriented rendering inside anchors;
- emit speaker directives at source speaker changes;
- avoid modifying the canonical result.

The initial target anchor size is configuration-driven and defaults to approximately 200
source words.

For a directory input, the default review output directory SHOULD be a dedicated child
such as `review-ewp-transcripts/`, while `--output-dir` permits an explicit destination.

## 11. Review apply and preview

`transcriber revise apply REVIEW` parses, verifies, aligns, validates, and, unless disabled,
persists a new full revision.

The following are equivalent non-mutating operations:

```text
transcriber revise preview REVIEW
transcriber revise apply REVIEW --no-apply
```

Both MUST perform the same parse/alignment/validation path and MUST NOT write a revision or
derived export.

Preview SHOULD expose a human-readable summary and MAY expose a structured JSON outcome
for tooling. The application layer returns typed preview data so a future GUI does not
need to invoke the CLI.

## 12. External editor workflow

`transcriber revise edit RESULTS_JSON` is a convenience wrapper over prepare and apply.

The command:

1. prepares a review file;
2. starts an external editor and waits for termination;
3. treats editor exit status zero as approval to apply the saved review;
4. creates a revision after successful validation.

Saving and closing the editor therefore creates a revision automatically unless
`--no-apply` was supplied. This behavior MUST be stated in command help.

The editor command MUST be executed without a shell. Configuration or environment text
is parsed into an argument vector before process creation.

## 13. Anchored alignment

Review anchors constrain alignment to bounded canonical word ranges. An anchor is an
alignment boundary, not a sentence or canonical-segment boundary.

Generated anchors MUST:

- appear in canonical word order;
- be non-overlapping;
- collectively cover all canonical words once;
- remain unchanged through normal review.

Apply MUST reject modified/missing/duplicate/out-of-order anchor metadata rather than
silently attempt a global repair.

Within each anchor the implementation may use dynamic programming, matching n-grams, or
another deterministic algorithm. The persisted alignment metadata records a stable
strategy/version identifier.

The aligner MUST support substitutions, punctuation changes, merge/split, insertions,
deletions, and speaker reassignment. Ambiguous mappings MUST be surfaced instead of being
silently resolved arbitrarily.

## 14. Insertions

A corrected token with no canonical source word stores an insertion anchor containing an
adjacent `after_word_id`, `before_word_id`, or both.

The insertion anchor records textual position. It is not an invented timestamp.

For subtitle rendering an inserted token is grouped with a neighboring timed unit. If the
neighboring canonical words are separated by a long configured gap, a structured warning
is emitted for review.

## 15. Revision snapshots and lineage

Revision files are immutable complete snapshots. Creating another edit allocates another
revision.

Possible history:

```text
results.json
  -> revision_001.json
       -> revision_002.json
```

Possible benchmark siblings:

```text
results.json
  -> revision_001.json   manual gold
  -> revision_002.json   model A
  -> revision_003.json   model B
```

The sequential number is file allocation identity, not proof of parentage. Parentage is
explicit in `parent_revision`.

## 16. Filename convention

Recommended revision artifact naming:

```text
<job_id>_revision_001.json
<job_id>_revision_002.json
```

When the base canonical result is itself an additional result version, include its result
version so two base results cannot allocate colliding revision names:

```text
<job_id>_v002_revision_001.json
```

The exact base SHA-256 in the artifact remains authoritative regardless of filename.

Review work files SHOULD use `.review.txt`, for example:

```text
<job_id>.review.txt
```

and SHOULD include revision identity in the work filename when prepared from an existing
revision in a later workflow.

## 17. Atomicity and concurrency

Final revisions MUST use the existing safe-output principles:

- strict schema validation before publication;
- no overwrite of existing final artifacts;
- output-directory locking during number allocation and finalization;
- temporary file in the destination filesystem;
- flush/fsync where available;
- atomic publication;
- failure of one batch item does not corrupt or replace another item.

A preview never reserves a permanent revision number.

## 18. Provenance

Every revision stores compact provenance.

Manual v0.2.0 provenance includes at least:

- `method = "manual"`;
- interface (`cli` for current implementation);
- application version;
- creation timestamp.

The schema reserves structured LLM provenance for later automated correction, including
provider/model, local/cloud endpoint class, prompt hash/version, and non-secret parameters.
Secrets, authentication headers, complete environment dumps, and transcript contents MUST
NOT be copied into provenance fields unnecessarily.

## 19. Statistics and warnings

Every revision stores summary counts sufficient for diagnostics and benchmark indexing,
including:

- source/corrected token counts;
- substitutions;
- merges;
- splits;
- insertions;
- deletions;
- punctuation-only changes;
- speaker changes;
- ambiguous regions;
- warning count.

Structured warnings use stable codes. Suggested v0.2.0 revision codes include:

```text
REVISION_ALIGNMENT_AMBIGUOUS
REVISION_BASE_HASH_MISMATCH
REVISION_ANCHOR_INVALID
REVISION_INSERT_ACROSS_LONG_GAP
REVISION_SOURCE_WORD_MISSING
REVISION_SPEAKER_INVALID
```

## 20. Detailed audit

A detailed edit list is diagnostic output, not the reconstruction mechanism.

`--audit` MAY persist a separate audit JSON during apply/edit. The audit can contain
before/after text, mapped word IDs, classifications, and speaker changes.

A base-relative audit MUST be reconstructable later from the immutable base result and
full revision snapshot. Parent-relative changes require the parent revision to be
available.

## 21. EffectiveTranscript

The export layer resolves one effective transcript:

```text
results.json                         -> raw EffectiveTranscript
results.json + selected revision     -> revised EffectiveTranscript
```

This runtime model provides corrected text/speaker identity and resolved timing to all
exporters. It removes the need for TXT to trust `segment.text` while subtitles trust
`word.text`.

The canonical v0.1 model and `results.schema.json` remain unchanged.

## 22. Revision-aware export

`transcriber export` adds:

```text
--revision none
--revision latest
--revision PATH
```

Omitting the option is backward-compatible with `--revision none`.

`latest` resolves the highest allocated revision number whose base hash matches the
selected result. Explicit revision paths are recommended for benchmark branches.

Revision export MUST validate base hashes before rendering and MUST remain independent of
audio and ML models.

All existing TXT/SRT/VTT/segments rules continue to apply to the selected effective
transcript.

Consequently, applying a revision writes revision state, while `transcriber export
--revision ... --format segments` materializes corrected segments as replaceable derived
output.

## 23. Batch behavior

`prepare` and `apply` MUST support directory input in v0.2.0.

Batch semantics follow existing project principles:

- deterministic natural order;
- no recursion unless explicit;
- warning/error isolation per item;
- continue according to the existing runtime batch policy;
- non-zero batch exit code when at least one item fails;
- structured batch summary.

Review-to-result resolution may use an explicit `--results-dir`. Any path hint stored in a
review file is secondary to hash verification.

## 24. Configuration

The revision feature participates in normal configuration precedence.

Initial planned keys:

```toml
[revision]
anchor_target_words = 200
long_gap_warning_ms = 2000
generate_audit = false
editor = ""
```

`editor = ""` means use the normal environment fallback (`VISUAL`, then `EDITOR`) or fail
with actionable guidance when `revise edit` cannot identify an editor.

## 25. Compatibility with future automated correction

Automated correction is the next major correction milestone after manual v0.2.0.
It MUST produce input for the same alignment and revision materialization path rather than
creating a second corrected data model.

LLM chunking will be configurable in TOML and CLI. Overlap is read-only context: every
editable source range belongs to exactly one chunk.

The LLM does not receive audio and does not author authoritative word timestamps.

## 26. Compatibility with future translation

Translation is a separate pipeline and its schema is deliberately deferred.

The future translation pipeline must be able to select either:

- raw canonical transcript (`--source raw`); or
- a selected corrected revision.

Translation mapping is sentence-level rather than word-level. A future immutable
translation artifact will preserve source identity, sentence mapping, and inherited time
spans so translated TXT/SRT/VTT/HTML can be regenerated from one structured artifact.

The first translation contract supports `pl -> en` and `en -> pl` through the same
pipeline. It defaults to preserving the source's style and records optional independent
register (`preserve`, `formal`, `informal`) and discourse (`preserve`, `academic`,
`general`) guidance in provenance. Guidance affects translation choices only; it cannot
authorize changed facts, omissions, summaries, speaker reassignment, or broken source
sentence lineage.

The preferred translation source is the latest manually verified compatible transcript
revision. Selecting raw ASR or an automated-correction candidate must be explicit and is
primarily retained for controlled comparisons. Local translation models are benchmarked
independently from local correction models because their relative quality is not assumed
to transfer between tasks.

Manual translation precedes automated translation for benchmark purposes.

## 27. Acceptance criteria

v0.2.0 revision behavior is accepted when automated tests cover at least:

- raw review round-trip;
- punctuation-only change;
- proper-name correction;
- sentence-boundary correction;
- one-to-one substitution;
- merge;
- split;
- insertion;
- deletion;
- preserved repetition;
- speaker reassignment;
- invalid/missing/out-of-order anchors;
- base hash mismatch;
- invalid speaker ID;
- ambiguous alignment reporting;
- long-gap insertion warning;
- preview and `apply --no-apply` equivalence;
- external-editor `--no-apply` behavior;
- single and batch prepare/apply;
- batch failure isolation;
- parent/sibling revision metadata;
- standalone full-snapshot export;
- revision-aware TXT/SRT/VTT/segments generation;
- unchanged raw export behavior;
- model-free/audio-free revision and export paths;
- mandatory provenance/statistics;
- optional and reconstructable audit.
