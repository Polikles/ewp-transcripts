# EWP Transcriber — complete CLI runbook

This is the current operator entry point for the internal command-line application. It
covers every shipped command. The application is not yet a public release.

## 1. Install and prepare the machine

The supported environment is Ubuntu 24.04 under WSL2 with Python 3.12, FFmpeg, `uv`, and
an NVIDIA CUDA-capable GPU. Follow the detailed setup documents in order:

The current locked environment downloads approximately 4–4.5 GB before model setup.
The pinned ASR, Polish/English alignment, and diarization snapshots add approximately
8.5 GB, making the complete network transfer roughly 13 GB. Reserve at least 20 GB of
free space on the Linux filesystem, preferably on an SSD, plus space for source audio
and outputs. The recommended storage minimum is not expected to vary materially by
preset. RAM, VRAM, and runtime requirements will be characterized later per preset.

1. [`../WSL config/SYSTEM_REQUIREMENTS.md`](../WSL%20config/SYSTEM_REQUIREMENTS.md)
2. [`../WSL config/INSTALL_WSL.md`](../WSL%20config/INSTALL_WSL.md)
3. [`../WSL config/INSTALL_TOOLS.md`](../WSL%20config/INSTALL_TOOLS.md)
4. [`../WSL config/CUDA_SETUP.md`](../WSL%20config/CUDA_SETUP.md)
5. [`../WSL config/INSTALL_APPLICATION.md`](../WSL%20config/INSTALL_APPLICATION.md)
6. [`../WSL config/HUGGING_FACE_TOKEN.md`](../WSL%20config/HUGGING_FACE_TOKEN.md)
7. [`../WSL config/MODEL_SETUP.md`](../WSL%20config/MODEL_SETUP.md)
8. [`../WSL config/OFFLINE_MODE.md`](../WSL%20config/OFFLINE_MODE.md)

Normal source-checkout use begins in the repository:

```bash
cd "$HOME/transkrypcje/ewp-transcripts"
uv sync --locked
uv pip check
uv run --locked transcriber --version
uv run --locked transcriber --help
```

The local browser interface is available on loopback:

```bash
uv run --locked transcriber gui
```

Use `--no-open-browser` when launching from a terminal that cannot open the host browser.
The printed `http://127.0.0.1:PORT/` URL can then be opened manually. Only the explicitly
accessible user-space paths are accepted while system directories and symlinks are blocked.
Inspect/dry-run are non-mutating. The current queue accepts one
file per staged row and requires a reviewed dry-run plus explicit confirmation. Add distinct
episode files to one durable shared output directory, review/remove the staged
rows, then select **Start queue**. The bundled **GUI workflow** help page explains this without
requiring Internet access. Closing the browser does not stop a job; stopping the server waits
for active transcription.

The **Review and export** section accepts one completed canonical result. Keep its editable
review, immutable revision, and derived exports in separate allowed-root directories. Prepare
the draft, edit visible speaker/text blocks, save it, and run Preview. Apply remains locked
until the exact saved draft previews successfully and the manual-verification confirmation is
checked. Export then uses only the newly applied immutable revision. Automated candidates and
translation remain CLI workflows in this slice.

After cloning, a fresh Ubuntu 24.04 checkout can install the base packages, uv/Python,
locked environment, and run diagnostics through the reviewable script:

```bash
./scripts/install-fresh-ubuntu.sh --install
```

It asks before system changes, does not update Git, and never downloads gated models.
Use `./scripts/install-fresh-ubuntu.sh --verify-only` for a read-only recheck. Model setup
remains the separate explicit step in `WSL config/MODEL_SETUP.md`.

The top-level help lists commands. Every command has its own options:

```bash
uv run --locked transcriber COMMAND --help
uv run --locked transcriber revise COMMAND --help
```

The staged private-corpus procedure for v0.3 local LLM correction candidates is in
[`../WSL config/RUN_V03_LOCAL_LLM_BENCHMARK.md`](../WSL%20config/RUN_V03_LOCAL_LLM_BENCHMARK.md).
It requires a three-case pilot before any full-corpus run.

## 2. Configuration and paths

Configuration precedence, from lowest to highest, is:

1. packaged defaults;
2. selected preset;
3. `$HOME/.config/ewp-transcripts/config.toml`;
4. `transcriber.toml` in the terminal's current working directory;
5. the file supplied with `--config PATH`;
6. CLI options.

For the normal source checkout, the project file is exactly:

```text
/home/<user>/transkrypcje/ewp-transcripts/transcriber.toml
```

Run commands from that directory or pass `--config` explicitly. Paths containing spaces
are supported and preserved; quote the complete path. Windows paths such as
`C:\Users\name\recordings` and WSL paths such as `/mnt/c/Users/name/recordings` are both
accepted. Linux-side output/work directories are faster for large jobs.

## 3. Check readiness: `doctor`

```bash
uv run --locked transcriber doctor
uv run --locked transcriber doctor --json-output
```

`doctor` checks Python, WSL/Ubuntu, FFmpeg, GPU/CUDA, pinned local models, and whether
`HF_TOKEN` is present without printing the secret. On a fresh installation, missing model
messages point to `WSL config/MODEL_SETUP.md`. Do not transcribe until required checks
pass.

## 4. Inspect inputs: `inspect`

Always inspect unfamiliar material before transcription:

```bash
uv run --locked transcriber inspect "/path/to/episode.wav"
uv run --locked transcriber inspect "/path/to/season"
uv run --locked transcriber inspect "/path/to/season" --json-output
```

Inspection is model-free. It reports discovery/grouping, duration, streams, channel mode,
speaker-source hints, hashes, and warnings. Directory discovery is non-recursive unless
`--recursive` is supplied.

Preferred multi-speaker input order:

1. one synchronized mono file per speaker;
2. one two-channel file with an isolated speaker in each channel;
3. a mono/stereo program mix followed by diarization and manual attribution review.

Avoid 3+ channel sources in the current release: the warning fallback can use only
channel 0 and may omit dialogue. Ordinary two-speaker stereo is accepted, but inferred
speaker attribution is not guaranteed.

## 5. Group synchronized speaker files

Automatic filename grouping uses final suffixes such as:

```text
episode-Damian.wav
episode-Szymon.wav
```

For unrelated filenames, provide an explicit collision-safe group identity:

```bash
uv run --locked transcriber inspect \
  --group "/path/to/left.wav" \
  --group "/path/to/right.wav" \
  --group-id "episode-001"
```

Repeat `--group` for every source. Use `--speaker-map "left.wav=Damian"` and another
mapping for `right.wav` during `transcribe` when filename labels are unsuitable. Grouped
files must share a timeline and sample rate. `--allow-duration-mismatch` is the dedicated
override for differences above the normal limit; `--force` does not bypass input checks.

## 6. Plan safely: `dry-run`

```bash
uv run --locked transcriber dry-run "/path/to/season" \
  --speaker-count auto \
  --output-dir "/path/to/output"
```

Review every `PROCESS`, `SKIP`, source assignment, channel decision, warning, result
version, and output path. Dry-run creates no final output or work directory and loads no
model. Use `--speaker-count 1` only for a genuine one-speaker recording; use an exact
positive count when known, otherwise `auto`.

## 7. Transcribe: `transcribe`

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
uv run --locked transcriber transcribe "/path/to/season" \
  --speaker-count auto \
  --output-dir "/path/to/output" \
  --non-interactive
```

Polish is the default. `--language en` and `--language auto` are supported but not yet
quality-qualified on a representative English corpus. Useful options include:

- `--format txt|srt|vtt` (repeatable) and `--segments`;
- `--speaker NAME` for one known single-speaker source;
- repeatable `--speaker-map SOURCE=NAME` for grouped sources;
- `--channel-mode split-speakers` only with source knowledge;
- `--keep-temp` to retain an owned successful workspace;
- `--force` to create the next `_vNNN` result set without overwriting.

Every successful job creates immutable `*_results.json`. The review-first defaults also
create machine-readable segments and a TXT preview; the preview is not manually verified.
TXT/SRT/VTT/YTT/HTML/segments are all derived and regenerable with the model-free `export`
command. Raw subtitles may be exported explicitly for diagnosis or urgent use, but review
and apply corrections before publication and especially before translation. Duplicate
matching jobs skip safely. Never edit canonical JSON.

## 8. Export raw results: `export`

Single result:

```bash
uv run --locked transcriber export "/path/to/episode_results.json" \
  --format txt --format srt --format vtt --format ytt --format html --format segments \
  --output-dir "/path/to/exports"
```

Directory batch:

```bash
uv run --locked transcriber export "/path/to/results" \
  --format txt --format srt --format vtt --format ytt --format html --format segments \
  --output-dir "/path/to/exports"
```

Export is audio-free, model-free, and non-recursive unless `--recursive` is supplied.
Existing identical destinations skip; `--force` creates later export versions.
`--speaker-labels on-change|always|never` changes subtitle labels.
YTT uses the same planned cues and line wrapping as SRT/VTT, serialized as YouTube srv3
timed-text XML with deterministic speaker pens and bottom-center placement. Configure its
ordered fallback palette with `[subtitles].ytt_speaker_palette`. It is opt-in
(`--format ytt`) because it is a YouTube-specific export; its real Polish two-speaker
upload profile is qualified.
HTML is an embeddable, script-free fragment with sentence-level seek metadata and explicit
speaker turns. It contains no CSS or JavaScript; the consuming site supplies playback,
highlighting, and presentation enhancements. `examples/html-player/` demonstrates that
integration with a native audio player, keyboard activation, current-sentence following,
accessible focus, speaker colors, and light/dark presentation.
Sentence seek times inherit the exact word-alignment boundary. An occasional boundary
sound may acoustically belong to the adjacent sentence; do not compensate with arbitrary
timestamp offsets in the fragment or player.

## 9. Correct transcripts: `revise`

The recommended workflow is `prepare -> edit in Windows VS Code -> preview -> apply ->
export`. Keep canonical results, reviews, revisions, audits, and exports in separate
directories.

The planned production path first generates a non-final Gemini 2.5 Flash Polish correction
candidate, accepts or corrects it through manual revision, exports the verified Polish
transcript, and only then translates that accepted revision manually or with an LLM.
Project dictionaries for correction and translation are explicit and audited separately.
An operator may explicitly translate an unreviewed correction candidate. The CLI warns on
prepare, preview, apply, and automated translation; the artifact records the exact LLM
revision as `verification: automated_candidate`, not as manually verified source.

### Prepare one or many reviews

```bash
uv run --locked transcriber revise prepare "/path/to/results" \
  --output-dir "/path/to/reviews"
```

To manually review an automated correction candidate, prefill from its exact immutable
revision instead of starting over from raw ASR:

```bash
uv run --locked transcriber revise prepare "/path/to/episode_results.json" \
  --revision "/path/to/candidates/episode_revision_001.json" \
  --output-dir "/path/to/reviews"
```

The protected header records the candidate ID, number, SHA-256, and
`x_source_verification: automated_candidate`. Preview/apply use `--revisions-dir` to locate
that exact parent when candidates and accepted revisions are stored separately.

Edit `*.review.txt` in Windows VS Code. Its search and **Change All Occurrences** tools
are preferable for long transcripts. Preserve all `#` metadata, `@@ anchor`, and
`@@ speaker` directives. Edit only transcript text and existing speaker assignments.

### Preview without writing

```bash
uv run --locked transcriber revise preview "/path/to/reviews" \
  --results-dir "/path/to/results" \
  --revisions-dir "/path/to/candidates"
```

This is equivalent to `revise apply ... --no-apply`. A failed item in a continuing batch
does not invalidate successful items, but the command returns exit code 5.

### Apply and optionally audit

```bash
uv run --locked transcriber revise apply "/path/to/reviews" \
  --results-dir "/path/to/results" \
  --revisions-dir "/path/to/candidates" \
  --output-dir "/path/to/revisions" \
  --audit
```

Apply publishes immutable `*_revision_NNN.json`; `--audit` adds reconstructable detailed
diagnostics. If one review fails, repair and apply only that file—do not rerun the entire
directory unless additional revisions are intended.

### External-editor shortcut

```bash
uv run --locked transcriber revise edit "/path/to/episode_results.json" \
  --editor "nano" --audit
```

Successful editor close automatically applies only if the review changed, unless
`--no-apply` is supplied. GUI launchers can return before a file closes; the staged VS
Code workflow above is safer. `VISUAL` and `EDITOR` are environment-variable names whose
values must contain an installed editor command; they are not literal commands.

### Reconstruct an audit

```bash
uv run --locked transcriber revise audit "/path/to/episode_revision_001.json" \
  --results-dir "/path/to/results" \
  --output-dir "/path/to/revisions"
```

Use `--no-write --json-output` to inspect reconstructed diagnostics without publication.

The detailed revision guide is
[`../WSL config/REVISE_TRANSCRIPTS.md`](../WSL%20config/REVISE_TRANSCRIPTS.md).

### Automated correction with LM Studio or OpenRouter

This application is intentionally part of a wider toolchain. It orchestrates pinned models from
their upstream repositories and optional separately operated APIs rather than redistributing or
silently configuring every external dependency. Model terms and API credentials therefore remain
explicit operator-controlled setup steps.

The provider contract, local/cloud execution, manual-review boundary, and project-dictionary
path are acceptance-audited. Gemini 2.5 Flash through OpenRouter is the qualified project
workflow; evaluated local models remain useful for controlled experiments but did not improve
the measured ASR error rate. In LM Studio, load exactly the intended model and start its local
OpenAI-compatible server. Confirm the exact identifier without sending a transcript:

An automated revision is always a **review candidate**, never a final or accepted
transcript. WER/CER does not validate punctuation or quotation marks, and tested models
can miss ASR errors or introduce plausible-looking substitutions, deletions, paraphrases,
and improper names. Manually review wording, speaker attribution, punctuation, quotation
marks, and sentence boundaries before exporting it as accepted work. Only a manually
accepted revision may serve as final publication text or benchmark gold.

The current `faithful-correction-v11` provider contract is deliberately lexical: it may repair
only unmistakable ASR word/short-phrase errors and high-confidence proper-name spelling, aided by
an optional project dictionary. It must preserve punctuation, capitalization, sentence boundaries,
grammar, repetitions, fillers, and style. The revision engine and manual editor fully support
punctuation and sentence-boundary corrections, but the LLM is not currently authorized to make
them. This conservative boundary avoids presenting plausible editorial rewriting as recovered
speech; punctuation and sentence splitting remain part of required human review.

```bash
curl -fsS http://127.0.0.1:1234/v1/models | \
  uv run --locked python -c \
  'import json,sys; print("\n".join(item["id"] for item in json.load(sys.stdin)["data"]))'
```

Preview still calls the API and stores validated private resume responses; it only
avoids publishing a revision. The first call requires explicit consent:

```bash
uv run --locked transcriber revise correct "/path/to/episode_results.json" \
  --model "EXACT_MODEL_ID_FROM_LM_STUDIO" \
  --endpoint "http://127.0.0.1:1234/v1" \
  --consent once \
  --preview \
  --resume-dir "/private/path/lm-studio-model-name/resume"
```

After inspecting the preview, publish an immutable revision. Reusing the same resume
directory avoids repeating already validated chunks:

```bash
uv run --locked transcriber revise correct "/path/to/episode_results.json" \
  --model "EXACT_MODEL_ID_FROM_LM_STUDIO" \
  --consent once \
  --output-dir "/private/path/lm-studio-model-name/revisions" \
  --resume-dir "/private/path/lm-studio-model-name/resume"
```

To run automated correction on text that already has an immutable revision, keep the
canonical result as the first argument and select the exact parent explicitly:

```bash
uv run --locked transcriber revise correct "/path/to/episode_results.json" \
  --revision "/path/to/episode_revision_001.json" \
  --model "EXACT_MODEL_ID_FROM_LM_STUDIO" \
  --consent once \
  --output-dir "/private/path/model/revisions"
```

The output is a complete child revision rather than a patch. It retains the parent's
accepted text, records the parent's exact identity/hash/number, and can be exported even
if the parent file is later archived. An incompatible parent fails before transcript text
is sent to the provider.

Use `--consent persist` only to remember the exact LM Studio provider and endpoint scope;
model and prompt identity still participate in operation/resume hashes. `--consent reject`
guarantees no API request. Even a loopback server is a separate process that may log or
forward text, so EWP Transcriber displays its local-API warning. The endpoint must be an
uncredentialed HTTP(S) `/v1` URL. Loopback (`localhost`, `127.0.0.1`, or `::1`) is the
default. A LAN, VPN, or Tailscale-like address additionally requires
`--allow-remote-endpoint` and produces a stronger warning; plain HTTP confidentiality
then depends on the underlying network or overlay and is not verified by this program:

```bash
uv run --locked transcriber revise correct "/path/to/episode_results.json" \
  --model "qwen2.5-14b-instruct" \
  --endpoint "http://100.99.201.120:1234/v1" \
  --allow-remote-endpoint --consent once --preview
```

OpenRouter is a separate paid cloud path. Transcript text leaves the machine; audio is not
uploaded. Export the key in the shell, pin the exact current model slug, and use both the
cloud opt-in and consent flags. Never paste a key into TOML, CLI arguments, logs, or
benchmark manifests:

```bash
export OPENROUTER_API_KEY="YOUR_KEY"

uv run --locked transcriber revise correct "/path/to/episode_results.json" \
  --provider openrouter \
  --model "google/gemini-2.5-flash" \
  --allow-cloud --reasoning-max-tokens 0 --consent once --preview \
  --resume-dir "/private/path/openrouter-gemini-2.5-flash/resume"
```

Without `--allow-cloud`, strict-offline mode rejects the command before reading the key or
making a request. `--consent reject` also guarantees no request. `persist` remembers only
the exact non-secret provider/endpoint scope. Preview calls may incur charges. The adapter
requests no fallback routing and records non-secret parameters, token counts, and reported
cost when supplied. Cloud output requires the same manual review as local output.
Reasoning-capable cloud models must use an explicit, recorded setting for comparable runs.
For example, add `--reasoning-max-tokens 0` to disable Gemini 2.5 thinking for the initial
baseline. Enabled-reasoning runs are separate experiments because reasoning tokens affect
latency and billing.

## 10. Translate manually

The manual translation workflow is model-free. It supports `pl -> en` and
`en -> pl`; use the latest manually verified revision as the preferred source. Raw ASR
and LLM-corrected revisions are allowed only when deliberately selected and remain marked
as raw or automated candidates in the translation artifact.

The detailed end-to-end playbook, including migration of earlier translated
`EWP-REVIEW` copies, is
[`../WSL config/TRANSLATE_TRANSCRIPTS.md`](../WSL%20config/TRANSLATE_TRANSCRIPTS.md).

Prepare a protected bilingual review:

```bash
uv run --locked transcriber translate prepare "/path/to/episode_results.json" \
  --revision "/path/to/episode_revision_001.json" \
  --target-language en \
  --output-dir "/path/to/translation-reviews"
```

Omit `--revision` only to translate raw canonical text. Optional `--register` accepts
`preserve`, `formal`, or `informal`; `--discourse` accepts `preserve`, `academic`, or
`general`. Both default to faithful `preserve`. They never authorize summaries, added
facts, omissions, or changed speaker identity.

Open the resulting `*.translation.review.txt` in VS Code. Preserve `EWP-TRANSLATION`,
the `# metadata` line, every `@@` directive, and every `< ` source line. Enter one
translation after each corresponding `> ` marker. Every target must be completed.

Validate without writing, then publish:

```bash
uv run --locked transcriber translate preview \
  "/path/to/translation-reviews/episode_en.translation.review.txt" \
  --results "/path/to/episode_results.json" \
  --revision "/path/to/episode_revision_001.json"

uv run --locked transcriber translate apply \
  "/path/to/translation-reviews/episode_en.translation.review.txt" \
  --results "/path/to/episode_results.json" \
  --revision "/path/to/episode_revision_001.json" \
  --output-dir "/path/to/translations"
```

Preview and apply require the same exact canonical and optional revision files used by
prepare. Source hashes, units, speakers, timing, and token ownership are reconstructed;
any machine-owned edit fails. Apply publishes a complete immutable
`*_LANG_translation_NNN.json` snapshot.

For a directory, prepare selects canonical results deterministically. Supplying a
revision directory selects the highest compatible exact-hash revision separately for
each result:

```bash
uv run --locked transcriber translate prepare "/path/to/results" \
  --revision "/path/to/revisions" --target-language en \
  --output-dir "/path/to/translation-reviews"

uv run --locked transcriber translate preview "/path/to/translation-reviews" \
  --results "/path/to/results" --revisions-dir "/path/to/revisions"

uv run --locked transcriber translate apply "/path/to/translation-reviews" \
  --results "/path/to/results" --revisions-dir "/path/to/revisions" \
  --output-dir "/path/to/translations"
```

Batch failures are isolated and return exit code 5. Repair and retry only failed review
files to avoid creating unintended later translation numbers.

Export one snapshot or a directory without audio or models:

```bash
uv run --locked transcriber translate export "/path/to/translations" \
  --format txt --format srt --format vtt --format html \
  --output-dir "/path/to/translated-exports"
```

TXT and HTML use stable speaker IDs because translation artifacts do not invent display
names. SRT/VTT inherit
sentence-unit timing. If translated text needs multiple cues for line capacity, timing is
distributed within that unit; target-word alignment is not claimed. Identical files skip
safely, conflicting files fail before any requested format is written.

Reconstruct a reviewable source/target audit from the exact inputs:

```bash
uv run --locked transcriber translate audit \
  "/path/to/translations/episode_en_translation_001.json" \
  --results-dir "/path/to/results" --revisions-dir "/path/to/revisions" \
  --output-dir "/path/to/translation-audits"
```

Omit `--revisions-dir` for a raw-source translation. `--no-write --json-output`
validates and prints the report without publication. The audit reopens the hashed source,
reconstructs every machine-owned mapping, and pairs source and target text by unit.

### Translate automatically with LM Studio

Automated translation always creates a non-final candidate. Load the exact model in LM
Studio, start its local server, and run from a verified revision where possible:

```bash
export EWP_TRANSLATION_PILOT="$(mktemp -d /tmp/ewp-translation-pilot.XXXXXX)"

uv run --locked transcriber translate automate "/path/to/episode_results.json" \
  --revision "/path/to/episode_revision_001.json" \
  --target-language en --provider lm-studio \
  --model "EXACT-LM-STUDIO-MODEL-ID" --consent once \
  --output-mode plain-text \
  --context-units 0 \
  --resume-dir "$EWP_TRANSLATION_PILOT/state" \
  --output-dir "$EWP_TRANSLATION_PILOT/candidates"
```

An approved project dictionary is optional and never discovered automatically. Select its
exact JSON file with `--dictionary /path/to/project-translation-dictionary.json`. The strict
file declares its ID, project, approved job IDs, direction, and source/target entries. A job
or direction mismatch fails before provider calls. The exact file SHA-256 is included in
request/resume identity and candidate provenance; dictionary-assisted results must be
benchmarked separately from no-dictionary results.
Only entries whose source form occurs in the owned unit are sent to the provider. This local
relevance boundary prevents an unrelated proper name from being injected into another unit;
the model is still required to use an applicable term without adding unrelated content.
Each dictionary belongs to one declared project and explicitly lists approved jobs; create
separate files for unrelated projects. Translation snapshots and accepted manual children
carry dictionary version, ID, project, and SHA-256. Audits declare that object or `null`, and
exports write a deterministic `.provenance.json` sidecar with the same dictionary-or-none
record without adding metadata to transcript or subtitle text.
Matching is case-insensitive but uses Unicode word/phrase boundaries, not inner substrings.
The dictionary is source-directed context rather than post-processing: a Polish-source
`Szymon` entry does not activate for source `Simon`, and target text is never globally
search/replaced. Truly ambiguous identical source forms still require model context and
manual review.

Polish correction dictionaries use a separate artifact. Generate an editable proposal only
from exact canonical results and accepted manual revisions, always writing disposable pilot
material under `/tmp`:

```bash
pilot_root=$(mktemp -d /tmp/ewp-correction-dictionary.XXXXXX)
uv run --locked transcriber dictionary correction propose \
  --canonical-dir "/path/to/project/canonical" \
  --revision-dir "/path/to/project/manual-revisions" \
  --project-id "my-project" \
  --output "$pilot_root/proposal.json"
```

Review every candidate and change its `status` from `pending` to either `approved` or
`rejected`. Publication fails while any item is pending and never enables the result globally:

```bash
uv run --locked transcriber dictionary correction approve \
  "$pilot_root/proposal.json" \
  --dictionary-id "my-project-pl-v1" \
  --output "$pilot_root/correction-dictionary.json"
```

The default proposal threshold is two consistent occurrences. This is candidate discovery,
not automatic correction: grammar/style edits and ambiguous mappings still require human
judgment. Each proposal occurrence includes `source_context` and `target_context`; `[[...]]`
marks the changed span. Use that evidence for short or grammatically ambiguous forms rather
than treating a token pair as a global replacement rule. Proposal keys discard leading and
trailing punctuation/quotation marks but preserve internal punctuation such as a domain's
dots. Correction and translation dictionaries are separately selected and versioned.

Published correction dictionaries retain both `approved` and `rejected` decisions. Provider
requests use only approved entries. When refreshing a project proposal, pass the prior artifact
with `--previous-dictionary /path/to/previous.json`; exact matching decisions are carried
forward instead of returning as pending. Store redistributable project artifacts at
`dictionaries/<project-id>/correction/<language>/<dictionary-id>.json`, publishing a new
immutable ID/file for every changed decision set. Keep private proposals and pilots in `/tmp`.

Select an approved dictionary explicitly for Gemini 2.5 Flash through the existing
OpenRouter correction command:

```bash
uv run --locked transcriber revise correct "/path/to/episode_results.json" \
  --provider openrouter \
  --model "google/gemini-2.5-flash" \
  --dictionary "$pilot_root/correction-dictionary.json" \
  --project-id "my-project" \
  --allow-cloud --consent once \
  --resume-dir "$pilot_root/state" \
  --output-dir "$pilot_root/candidates" \
  --preview
```

The API key remains in the configured environment variable and is never copied into an
artifact. An explicit project mismatch fails before provider calls. Dictionary `job_ids`
record the manual-revision cases from which decisions were derived; they are not an allowlist,
so the same explicitly selected project dictionary can assist future episodes. Only entries
whose source form occurs in the editable chunk are included as context; no deterministic
replacement is performed. Dictionary ID, version, project, exact SHA-256, and proposal lineage
are retained by the resulting revision and its audit. Changing dictionaries invalidates
resume reuse.

After producing a correction benchmark report, stage unsupported edits for focused manual
review without diffing complete transcripts:

```bash
uv run --locked transcriber benchmark correction review \
  "/tmp/private-benchmark/manifest.toml" \
  --output "/tmp/private-benchmark/unsupported-review.json"
```

This review contains bounded transcript context and must remain private under `/tmp`. Each edit
starts with `classification: pending`; inspect it against audio/context and classify it manually
as supported alternative, stylistic but acceptable, or harmful. Do not commit the review file.

All pilot-generated state, candidates, exports, and reports belong under this temporary
directory—not in the private corpus, repository, or another long-lived project directory.
After recording the required content-free evidence, remove it with
`rm -rf -- "$EWP_TRANSLATION_PILOT"` only after confirming the variable starts with
`/tmp/ewp-translation-pilot.`.

Use `--preview` to build and validate without publishing; provider calls still occur and
resume state is still written. `--consent persist` stores only the exact non-secret
provider/endpoint scope in `translation-consent.json` beside the configured correction
consent store. A non-loopback endpoint is rejected unless `--allow-remote-endpoint` is
explicitly supplied, and then receives an additional network warning.
`json-schema` is the default structured-output mode. Use explicit `--output-mode json-text`
for model/backends that reject JSON Schema channels but reliably serialize JSON. Use
`--output-mode plain-text` when translated dialogue quotes cause malformed JSON. Because
each operation owns exactly one unit, the whole assistant content can safely be treated as
that unit's candidate after non-empty/control-character/fence validation. All modes retain
exact local operation/unit binding. Output mode is part of prompt provenance and resume
identity.
Some Bielik templates emit a valid one-field JSON envelope even in plain-text mode. The
adapter accepts and unwraps only `target_text` or `translated_text` with one string value;
malformed JSON, additional fields, and non-string values are rejected.
It also unwraps a valid JSON string returned as the entire response, preventing serialization
quotes from becoming transcript punctuation. Ordinary prose and quotation marks that are not
a complete valid JSON string remain unchanged. The prompt requires personal names to be copied
exactly rather than translated, anglicized, or normalized; manual name review is still required.
The observed exceptions are optional string `translator_notes` and `translation_notes`
fields. Neither is copied into transcript text; the adapter discards it and records
`PROVIDER_TRANSLATOR_NOTES_DISCARDED` on that unit so manual review can treat the output as
higher risk. Any other field remains invalid. The compatibility-envelope version is part
of prompt provenance and resume identity.
`--context-units` controls how many adjacent source units are sent on each side as
read-only context. The initial Bielik baseline uses `0`: the first context-one pilot copied
adjacent meaning into owned units and omitted owned text. Context-assisted runs are
separate experiments and must never be merged with the zero-context baseline.

Each request owns exactly one sentence unit. Adjacent units are read-only context and
cannot be returned, merged, reordered, or assigned to another speaker. Interrupted runs
reuse only exact-operation-matched validated state. Inspect content-free operational
evidence with:

```bash
uv run --locked transcriber benchmark translation operations \
  "$EWP_TRANSLATION_PILOT/state" \
  --output "$EWP_TRANSLATION_PILOT/translation-operations.json"
```

For offline contract checks, `--provider mock` requires no consent or model. Its output is
synthetic and must never be used as translation-quality evidence. Whether mock or LM
Studio, manually review meaning, omissions, additions, contradictions, uncertainty,
names, terminology, and style before treating any candidate as accepted text.

Directories use the same command. Pass a revision directory to select each result's latest
exact compatible revision; failures are isolated and return exit code 5:

```bash
uv run --locked transcriber translate automate "/path/to/results" \
  --revision "/path/to/revisions" --target-language en \
  --provider lm-studio --model "EXACT-LM-STUDIO-MODEL-ID" --consent once \
  --resume-dir "$EWP_TRANSLATION_PILOT/state" \
  --output-dir "$EWP_TRANSLATION_PILOT/candidates"
```

To accept or correct one automated candidate, create a protected review prefilled from the
exact immutable candidate, edit only `> ` lines, then preview/apply with the same parent:

```bash
uv run --locked transcriber translate prepare "/path/to/episode_results.json" \
  --revision "/path/to/episode_revision_001.json" --target-language en \
  --parent-translation "/path/to/episode_en_translation_001.json" \
  --output-dir "/path/to/acceptance-reviews"

uv run --locked transcriber translate apply \
  "/path/to/acceptance-reviews/episode_en.translation.review.txt" \
  --results "/path/to/episode_results.json" \
  --revision "/path/to/episode_revision_001.json" \
  --parent-translation "/path/to/episode_en_translation_001.json" \
  --output-dir "/path/to/translations"
```

The accepted artifact is a new manual child. The LLM candidate remains unchanged and the
child records its exact ID, number, filename, and SHA-256.

### Benchmark translation meaning

When automated candidates and a narrower approved manual reference exist, prepare an
exact-hash private semantic-review bundle and then report completed assessments:

```bash
uv run --locked transcriber benchmark translation prepare "/path/to/candidates" \
  --gold-dir "/path/to/manual-gold" --output-dir "/path/to/assessment"

uv run --locked transcriber benchmark translation report "/path/to/assessment" \
  --output "/path/to/semantic-report.json"
```

The reviewer scores preserved meaning per unit as faithful or a minor, major, or critical
semantic error and categorizes errors such as omission, addition, contradiction, or
changed uncertainty. Different idiomatic wording is not an error. Names, approved
terminology, and explicit dictionary conventions are assessed separately. Reports never
combine Polish-to-English with English-to-Polish and contain no transcript text. See the
translation playbook for the assessment fields and restrictions.

## 11. Export corrected transcripts

Latest compatible revision per result:

```bash
uv run --locked transcriber export "/path/to/results" \
  --revision "/path/to/revisions" \
  --format txt --format srt --format vtt --format ytt --format html --format segments \
  --output-dir "/path/to/corrected"
```

For one result, use `--revision latest` or an explicit revision JSON. Use
`--revision none` for raw canonical text. Directory export with a revision directory
selects the highest revision whose exact base-result hash matches each result. Duplicate
replay skips safely without `--force`.

## 12. Recover from failures

- Exit 3: run `doctor`; install the missing dependency/model explicitly.
- Exit 4: inspect the input, streams, grouping, and supported extension.
- Exit 5: a batch partially failed; use the per-item error and retry only failed items.
- Exit 6: user cancellation; the failed state and owned workdir are retained for review.
- Exit 7: another process owns the output lock; wait or use another output directory.
- Exit 8: canonical/revision/schema mismatch; do not hand-edit JSON.

Failed/interrupted transcription restarts from the beginning. Successful items and
immutable results remain safe. See
[`../WSL config/TROUBLESHOOTING.md`](../WSL%20config/TROUBLESHOOTING.md).

## 13. Clean retained workspaces: `clean`

Preview first:

```bash
uv run --locked transcriber clean all-workdirs --dry-run --older-than 7
```

Then explicitly remove only the marker-verified selection:

```bash
uv run --locked transcriber clean all-workdirs --yes --older-than 7
```

Cleanup never removes source audio, final results/exports, unknown directories, model
caches, configuration, or tokens.

## 14. Privacy and evidence

Normal transcription and manual revision are local-first. Keep `HF_TOKEN`, source
recordings, canonical paths, transcripts, revisions, audits, correction resume state,
and private benchmark material out of Git and shared logs. LM Studio correction is an
explicit local API boundary and is not equivalent to in-process offline execution.
Cloud correction is implemented but remains strict-offline by default and requires an
explicit command opt-in, scoped consent, an environment-only key, and separate paid-run
authorization during project benchmarking.

For later benchmark feedback, use
[`../WSL config/FEEDBACK_FOR_V2.md`](../WSL%20config/FEEDBACK_FOR_V2.md).
