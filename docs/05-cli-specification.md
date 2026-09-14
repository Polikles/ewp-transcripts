# CLI Specification

Working command name: `transcriber`.

## 1. General rules

- Every command supports `--config PATH`.
- CLI flags override TOML values.
- `transcribe --non-interactive` disables all prompts.
- `doctor`, `inspect`, and `dry-run` support `--json-output`; structured transcription
  logging is selected through configuration.
- Secrets are never printed.

## 1.1 `gui`

```text
transcriber gui [--port PORT] [--search-root PATH]... [--no-open-browser]
```

Starts the local browser adapter on `127.0.0.1`. Port `8765` is the default and `0` requests
an ephemeral port. User-space paths are available without a launch-time allowlist. Repeated
`--search-root` options add locations to the browser-selected-file lookup; the older
`--allow-root` spelling remains a compatibility alias. Operating-system directories and
symlinks are rejected. The command serves bundled assets and the
versioned `/api/v1` interface without loading ML models. The v0.9 interface provides
inspect/dry-run, readable output-plan tables, bundled help, and an explicitly confirmed queue.
Each direct-file plan is staged without execution; distinct job IDs sharing one output
directory begin serially only after the operator selects **Start queue**.
It also provides model-free structured transcript review, save/preview/apply gates, and
verified-revision export through the same application services as the CLI.

## 2. `doctor`

Checks the environment without running transcription.

```text
transcriber doctor [--config PATH] [--json-output]
```

Checks include:

- WSL2 and distribution;
- GPU visibility through `nvidia-smi`;
- CUDA availability in PyTorch;
- FFmpeg and ffprobe;
- supported Python version;
- ASR, alignment, and diarization models;
- `HF_TOKEN` presence reported only as `present` or `missing`;
- local model readiness for offline transcription.

The CUDA check runs in a short child Python process. No transcription model is loaded.

## 3. `inspect`

```text
transcriber inspect [INPUT] [OPTIONS]
```

Does not run ASR. Returns:

- discovered files;
- media streams;
- detected groups;
- audio parameters;
- channel classification;
- hashes;
- structured warning-only audio-quality diagnostics;
- existing results and the skip/process decision.

Options:

```text
--recursive
--language pl|en|auto
--config PATH
--channel-mode auto|mono|dual-mono|split-speakers|mixed-stereo
--speaker-count auto|N
--allow-duration-mismatch
--json-output
--group PATH                    # repeatable; alternative to INPUT
--group-id ID                   # required with --group
```

## 4. `dry-run`

```text
transcriber dry-run [INPUT] [OPTIONS]
```

Performs discovery, probing, grouping, hashing, existing-result lookup, and export planning. It does not load ASR models or create final files.

Options are `--group`, `--group-id`, `--output-dir`, `--recursive`, `--language`,
`--config`, `--channel-mode`, `--speaker-count`, `--force`,
`--allow-duration-mismatch`, and `--json-output`.

For every job, output must include:

```text
PROCESS / SKIP / ERROR
job_id
sources
speakers
channel decision
language
result version
planned output paths
warnings
```

## 5. `transcribe`

```text
transcriber transcribe [INPUT] [OPTIONS]
```

Primary options:

```text
--output-dir PATH
--group PATH                   # repeatable; alternative to INPUT
--group-id ID                  # required with --group
--recursive
--config PATH
--language pl|en|auto
--speaker-count auto|N
--speaker NAME                 # single-speaker input
--speaker-map SOURCE=NAME      # repeatable
--channel-mode auto|mono|dual-mono|split-speakers|mixed-stereo
--preset accurate
--format txt                   # repeatable
--format srt
--format vtt
--format ytt
--format html
--segments
--force
--allow-duration-mismatch
--keep-temp
--non-interactive
```

Default post-transcription exports are defined in TOML. `results.json` is always created and does not require a flag.

`--speaker NAME` applies only to a single, non-split source and implies the
single-speaker use case. `--speaker-map SOURCE=NAME` may be repeated; `SOURCE`
is the exact input filename including its extension, not a path, stem, or
pattern. Unknown, repeated, ambiguous, and split-source mappings are rejected.
The two options cannot be combined. Explicit labels are applied before
duplicate/version planning, recorded with `speaker_source = "explicit"`, and
participate in the episode signature.

### Output directory

- single file without `--output-dir`: source directory;
- directory batch without `--output-dir`: `<input>/output-ewp-transcripts`;
- explicit `--output-dir`: selected directory with a safe output naming structure.

## 6. Explicit file group

Contract:

```text
transcriber transcribe \
    --group FILE1 \
    --group FILE2 \
    [--group FILE3 ...] \
    --group-id JOB_ID
```

`--group` is repeatable and creates exactly one job from at least two regular files.
`--group-id` is mandatory and supplies the collision-safe output identity; it is never
guessed from unrelated filenames. A positional `INPUT` cannot be combined with
`--group`. Speaker labels may come from each filename's final suffix or
`--speaker-map`.

`inspect` and `dry-run` accept the same explicit-group options. Without `--output-dir`,
outputs are written beside the first listed source. Explicit source order is preserved
in identity and provenance.

## 7. `export`

```text
transcriber export RESULTS_OR_DIRECTORY [OPTIONS]
```

Options:

```text
--format txt
--format srt
--format vtt
--format ytt
--format html
--format segments
--segments
--output-dir PATH
--force
--config PATH
--subtitle-preset youtube
--speaker-labels on-change|always|never
--revision none|latest|PATH_OR_DIRECTORY
--recursive
--json-output
```

The command does not open audio or load models. An existing export is skipped without `--force`; with `--force`, the next version number is created.

### Revision selection

For a single result, `export` additionally accepts:

```text
--revision none|latest|PATH
```

Omitting `--revision` is equivalent to `--revision none` and preserves the v0.1 raw
canonical export path. `latest` means the highest allocated revision number whose exact
base-result SHA-256 matches `RESULTS_JSON`. Explicit paths are recommended for benchmark
branches. Revision-aware export remains audio-free and model-free.

When the positional input is a directory, canonical results are discovered in natural
order and non-recursively unless `--recursive` is supplied. `--revision` may be `none`,
`latest`, or a revision directory. A revision directory selects the highest compatible
revision for each exact canonical base and ignores audit files. A single explicit
revision file is invalid for directory input.

Batch jobs are isolated according to the configured continue/stop policy. Any failure
produces exit code 5 after reporting per-result outcomes; `--json-output` emits the same
outcome as structured JSON. Duplicate replay without `--force` skips existing exports.

## 7a. `revise`

```text
transcriber revise prepare INPUT [OPTIONS]
transcriber revise apply INPUT [OPTIONS]
transcriber revise preview INPUT [OPTIONS]
transcriber revise edit INPUT [OPTIONS]
transcriber revise audit REVISION [OPTIONS]
transcriber revise correct RESULTS_JSON [OPTIONS]
```

`prepare` accepts a completed `results.json` or a directory containing completed results.
`apply` and `preview` accept an `EWP-REVIEW 1` file or a directory of review files.

`correct` accepts one completed canonical result and optionally one exact compatible
parent revision. Without `--revision`, it creates a base-relative revision. With an
explicit revision JSON, correction starts from that effective text and publishes a
complete standalone child snapshot with exact parent ID, number, and SHA-256. It supports
explicitly configured LM Studio and OpenRouter providers. Loopback is the local default;
remote or cloud use requires the corresponding separate opt-in.

```text
--model EXACT_MODEL_ID
--endpoint HTTP_OR_HTTPS_V1_URL
--allow-remote-endpoint
--output-mode json-schema|json-text
--revision PATH
--output-dir PATH
--resume-dir PATH
--preview
--consent reject|once|persist
--config PATH
```

`--preview` performs provider calls and may write private validated resume state, but
does not publish a revision. Consent is enforced before request serialization. Stored
consent is exact-scope only; otherwise interactive execution prompts and non-interactive
execution fails unless `--consent once|persist` is explicit. `reject` makes zero calls.
Non-loopback HTTP(S) requires `--allow-remote-endpoint`, emits an additional network
warning, and remains bound to the exact endpoint in persisted consent.
`--output-mode json-text` is an explicit compatibility fallback for LM Studio model builds
whose chat-template control tokens conflict with grammar-constrained JSON. It never falls
back automatically and does not relax local response validation.
Directory operations use deterministic natural ordering and do not recurse unless
`--recursive` is supplied.

Common options:

```text
--output-dir PATH
--recursive
--config PATH
--results-dir PATH             # resolve base results for review files
--revisions-dir PATH           # resolve an exact parent revision for prepared reviews
--json-output                  # preview/batch structured outcome where supported
```

### `revise prepare`

Creates human-readable `.review.txt` work files with immutable base metadata, stable word
anchors, speaker directives, and editable transcript text. It never modifies the base
result. Batch prepare is part of v0.2.0, not a later convenience feature.
For one canonical result, `--revision PATH` prefills text from an exact compatible manual
or automated revision and records its ID, number, and hash as protected parent lineage.
Preview/apply then use `--revisions-dir` when that parent is stored separately from results.

### `revise apply`

```text
transcriber revise apply REVIEW_OR_DIRECTORY [--no-apply] [--audit] [OPTIONS]
```

Normal apply parses the review, verifies the exact base-result SHA-256, runs deterministic
anchored alignment, validates the complete revision snapshot, and publishes a new
`*_revision_NNN.json` atomically. `--audit` additionally writes detailed diagnostic change
data.

`--no-apply` performs the complete parse/alignment/validation and preview computation but
does not publish a revision or derived exports.

### `revise preview`

```text
transcriber revise preview REVIEW_OR_DIRECTORY [OPTIONS]
```

This is the user-facing alias for the non-mutating apply path. It is semantically
equivalent to:

```text
transcriber revise apply REVIEW --no-apply
```

The equivalence MUST appear in `--help`. Both CLI forms call the same application
operation.

### `revise edit`

```text
transcriber revise edit RESULTS_JSON [--no-apply] [OPTIONS]
```

The command prepares a review file, starts the configured external editor, and waits for
it to close. **Saving the file and closing the editor with exit status zero is treated as
approval to create a revision automatically.** Supplying `--no-apply` keeps the edited
review file but suppresses automatic apply. A non-zero editor exit does not create a
revision.

The editor is executed as an argument vector, never through `shell=True`.
Automatic apply also requires the review file contents to change while the editor is
open. A zero-status launcher that makes no change retains the review and creates no
revision.

Options include `--review-output-dir`, `--output-dir`, `--editor`, `--config`, `--audit`,
and `--no-apply`. `--editor` overrides `[revision].editor`; an empty configuration falls
back to the `VISUAL` and then `EDITOR` environment-variable value. Each value is an
editor command, not the literal environment-variable name.

### `revise audit`

Reconstructs a detailed base-relative audit from a full revision and its immutable base
result. Parent-relative reconstruction additionally requires the parent revision artifact.
Audit data is diagnostic and is not needed to export the revision.

`--results-dir` locates the exact base, `--output-dir` selects publication, `--no-write`
keeps the operation non-mutating, and `--json-output` prints the reconstructed document.

## 7b. `translate`

```text
transcriber translate prepare RESULT_JSON --target-language pl|en [OPTIONS]
transcriber translate preview REVIEW --results RESULT_JSON [OPTIONS]
transcriber translate apply REVIEW --results RESULT_JSON [OPTIONS]
transcriber translate export TRANSLATION_OR_DIRECTORY [OPTIONS]
transcriber translate audit TRANSLATION --results-dir DIRECTORY [OPTIONS]
```

The initial model-free workflow prepares the strict `EWP-TRANSLATION 1`
format, validates completed target lines against the exact canonical and optional
`--revision` source, and atomically publishes a complete language-qualified immutable
translation snapshot. `prepare` accepts `--register preserve|formal|informal` and
`--discourse preserve|academic|general`; both default to `preserve` and remain
source-faithful.

Only target lines are editable. Metadata, source lines, unit and token IDs, speakers,
timing, hashes, direction, and style are reconstructed at preview/apply and fail closed
on drift. All target units must be non-empty. A manually verified transcript revision is
the preferred source; omitting `--revision` explicitly records raw source verification.
Directory prepare/preview/apply is deterministic and isolates failures per file. A
revision directory selects the latest exact compatible revision for each canonical
result; validation later resolves the exact canonical and revision filenames, hashes,
IDs, numbers, and method stored in each review. Batch partial failure returns exit code 5.
`translate export` derives repeatable `--format txt|srt|vtt` output from one immutable
snapshot or a deterministic directory. TXT presents stable speaker IDs. Subtitle text
uses inherited unit timing and may split only inside that interval to meet configured line
limits; it does not claim target-word alignment. Multi-format collision checks run before
publication, identical output skips, and batch failures are isolated.

`translate audit` requires the directory containing the exact canonical result and, for
revision-backed sources, the exact revision directory. It reconstructs and verifies every
source unit before pairing source/target text in a deterministic JSON report. `--no-write`
keeps the operation non-mutating. Automated providers are a later v0.4 slice.

## 8. `clean`

```text
transcriber clean all-workdirs
```

Safety options:

```text
--dry-run
--older-than DAYS
--yes
--config PATH
```

Exactly one of `--dry-run` or `--yes` is required. The command considers only valid
application-owned workspace markers immediately below the configured work root. Unknown
directories, symbolic links, invalid markers, final results, exports, models, tokens, and
configuration are never removed. `--older-than` currently uses the ownership marker's
modification time; changing diagnostic content therefore cannot make a workspace eligible
earlier.

Filtering retained workspaces by `failed`, `cancelled`, or deliberately retained after
success is deferred until a versioned marker records the terminal retention reason and an
immutable creation timestamp. Model-cache deletion remains a separately named operation
outside the MVP and requires separate confirmation.

## 9. Exit codes

| Code | Meaning |
|---:|---|
| 0 | all jobs completed or were validly skipped |
| 1 | general or unexpected error |
| 2 | invalid arguments or configuration |
| 3 | missing dependency, model, or environment capability |
| 4 | input error or no supported media stream |
| 5 | at least one batch job failed |
| 6 | interrupted by the user |
| 7 | lock or concurrent-write conflict |
| 8 | data-schema mismatch |

## 10. Interactive mode

A prompt is allowed only when stdin and stderr are TTYs. MVP decisions should have a deterministic default or require a flag.

In non-interactive mode, a missing required decision fails the affected job instead of blocking the process.
