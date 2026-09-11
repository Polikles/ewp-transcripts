# Post-0.1 Roadmap

The filename is retained for compatibility with existing links. The roadmap now tracks
planned work after the `0.1.x` internal release candidates rather than implying that all
items belong to one monolithic "Version 2" release.

## Current execution order

1. **v0.2.0 manual transcript revisions** — promoted from backlog into the next MVP
   increment and specified normatively in
   [`13-transcript-revisions.md`](13-transcript-revisions.md), ADR-0020, and
   [`21-v0.2.0-transcript-revision-plan.md`](21-v0.2.0-transcript-revision-plan.md).
2. Retain the completed 24-episode corrected corpus privately, outside this repository,
   until every included episode is public and redistribution is appropriate.
3. **v0.3 automated transcript correction — implemented** using local/cloud API models, configurable
   chunking, read-only overlap, the same revision engine, benchmarking against the
   private corpus, and manual revision of model output. v0.3 also includes the scoped
   fresh-install/verification script and README onboarding work in section 14.
4. **v0.4 manual and automated translation**, with a structured translation artifact,
   corrected transcript as the normal source, an explicit raw/dirty source option, and
   optional manual revision of automated output.
5. **v0.4 platform transcript exports**, including YouTube srv3 YTT
   and an embeddable synchronized HTML transcript fragment, with the compatibility,
   accessibility, security, and raw/revised/translated-source tests in sections 11-12.
6. **v0.4 optional project-scoped dictionaries**, conditional on benchmark evidence;
   later public-corpus work may also propose a separate optional general Polish resource,
   but neither kind is inherited or enabled silently.
7. After functional requirements and private-corpus validation, run separately licensed
   public-corpus WER and diarization benchmarks described in section 9.
8. Remaining audio, discovery, benchmark, subtitle, distribution, and operations work
   based on observed value and risk.
9. **GUI workflow queues — active work:** extend the implemented transcription queue into
   correction, review/export, and translation queues. The GUI reuses application services and
   does not implement a parallel pipeline.

Cross-cutting observability is implemented in
[`25-warning-error-catalog.md`](25-warning-error-catalog.md): domain warnings, expected
application errors, direct policy warnings, command wrappers, and framework-generated usage
failures print stable codes. The catalogue records meaning, likely causes, safety implications,
and operator action, while automated coverage rejects undocumented emitted codes.

The earlier small production pilot requirement is superseded operationally by the larger
manual-review corpus used to build correction ground truth. Existing accepted v0.1
validation evidence remains valid.

The 24-episode audio and corrected-transcript corpus is complete and is the private
reference benchmark for future ASR model, preset, correction, and translation
comparisons. It must not be committed while any included episode is non-public. Once all
episodes are public, publication in this repository requires a separate licensing,
privacy, size, and repository-distribution review; public availability alone does not
implicitly authorize committing the corpus.

The retained private package includes canonical results and raw exports, editable review
files, immutable revision and audit artifacts, and revised TXT/SRT/VTT/segments exports.
Future benchmark tooling must treat the accepted revisions as gold without requiring the
corpus itself to live in this repository.

Within each compatible base-result lineage, the highest revision number is the accepted
gold transcript. Lower revisions remain immutable historical/intermediate states rather
than being discarded. Benchmark manifests must resolve this by exact base-result hash
and revision number, never modification time or filename order alone. They should expose
at least two correction tasks when an intermediate revision exists:

- raw canonical result -> latest accepted gold, measuring complete ASR correction;
- earlier revision -> latest accepted gold, measuring incremental cleanup of text that
  has already received human review.

Earlier revisions are useful benchmark inputs but are not alternate gold references.
Evaluation must also measure harmful changes to text that was already correct.

## 1. Manual transcript correction — promoted to v0.2.0

The following is no longer an unscheduled roadmap idea. It is the implemented v0.2.0 contract:

- immutable canonical `results.json`;
- versioned full-snapshot revision artifacts linked by base-result SHA-256;
- `EWP-REVIEW 1` human-readable manual correction format;
- stable canonical word anchors and corrected speaker attribution;
- batch `revise prepare` and batch `revise apply`;
- `revise preview` and `apply --no-apply` equivalence;
- external-editor `revise edit`, with successful editor close applying automatically
  unless `--no-apply` is used;
- deterministic anchored token alignment for substitutions, punctuation, sentence
  boundaries, merge/split, insertion, deletion, repetition preservation, and speaker
  reassignment;
- no normal manual timestamp editing;
- runtime `EffectiveTranscript` shared by raw and revised export;
- revision-aware TXT/SRT/VTT/segments regeneration without source audio or ML models;
- mandatory provenance/statistics and optional/reconstructable detailed audit.

Detailed design belongs in docs 13/21 rather than this roadmap.

## 2. Automated transcript correction — implemented in v0.3.0

Automated correction follows manual correction so model performance can be measured
against manually verified ground truth.

Requirements:

- local API endpoints and explicit cloud API endpoints;
- cloud use is explicit opt-in and requires privacy warnings/documentation;
- no audio is sent to the correction model;
- the LLM receives relevant transcript blocks plus word/speaker/timing metadata needed as
  context, not the complete canonical processing/configuration payload;
- corrected LLM output is passed through the same alignment and `RevisionEngine` used by
  manual review;
- the implemented default prompt corrects only obvious ASR lexical errors and high-confidence
  proper-name spelling; punctuation, capitalization, and sentence boundaries remain manual;
- preserve the speaker's actual wording, repetitions, self-corrections, fillers,
  malformed sentences, grammatical mistakes, and stylistic quirks; never paraphrase,
  polish prose, or silently repair how the person spoke;
- require corrected editable text from the provider; the local revision engine derives
  exact source spans, before/after text, deterministic categories, and the authoritative
  audit. Optional provider change annotations remain advisory evidence;
- model/prompt/config provenance is persisted without secrets;
- LLM revisions may be direct siblings of manual gold for benchmark comparison;
- a model revision may later have a manual child revision, with parent provenance but a
  complete standalone child snapshot.

A later experiment may add two independent, default-off GUI modes: **check also punctuation**
and **try basic editorial fixes**. They require separately versioned prompt contracts and
evaluation because punctuation repair changes sentenceization, while editorial repair crosses
the default boundary that preserves spoken grammar and style. Both controls must warn that they
may increase API token usage and unsupported edits, and neither may remove mandatory manual review.

Benchmarking must cover local and cloud providers separately and report at least lexical
accuracy against manual gold, locally derived change precision/recall, unsupported or stylistic
changes, speaker-attribution preservation, audit completeness, latency, request/token
volume, estimated or actual cost, and failure/retry behavior. Provider-annotation precision
is reported separately only where annotations exist. A reviewer must be able to
prepare, manually correct, apply, audit, and export an LLM-produced revision through the
same workflow used for manual revisions.

Later benchmark automation should use supported backend APIs to load and, where available,
unload models,
wait for exact model readiness, run an explicit model x quantization x prompt x chunking
matrix, collect timing/resource/failure evidence, and unload cleanly without continuous
operator supervision. The observed LM Studio 0.4.21 server advertises native model
listing/loading and download-status endpoints in addition to its OpenAI-compatible
inference API; an unload mechanism must be verified against the selected backend/version
before automation relies on it. Other backends require separate adapters.
Every run identity and report must distinguish exact model identifier, quantization,
backend/version, prompt ID and content hash, output mode, chunk settings, context window,
sampling parameters, and hardware. Automation must retain bounded retries, private resume
state, sanitized logs, and the manual final-acceptance gate. It must never initiate paid
cloud runs or broaden API consent without separate explicit authorization.

Provider integration also requires deterministic mocked tests, secret-safe
configuration, timeout/rate-limit/retry handling, resumable failure-isolated batches,
and the consent/privacy contract in `11-security-and-privacy.md`.

The OpenRouter adapter and offline safety tests are implemented. A paid cloud pilot remains
an operator gate requiring an environment-only key, exact live model-slug confirmation,
explicit `--allow-cloud`, scoped consent, and separate authorization. Planned candidates
remain Qwen 2.5 72B Instruct and the exact currently available DeepSeek V3-family slug;
neither may be silently replaced when the catalog changes.
Gemini 2.5 Flash (`google/gemini-2.5-flash` when confirmed by the live catalog) is also a
cloud candidate. Its reasoning budget must be explicit and reported; the first comparable
baseline disables thinking, while enabled reasoning is a separate cost/quality experiment.

### Configurable chunking

Chunking is required for flexibility across local and cloud models and must not assume a
large context window.

Future configuration must expose at least:

- target chunk size;
- maximum chunk size;
- read-only context overlap;
- CLI/request overrides through the normal configuration precedence system.

Exact defaults are deferred until automated-correction benchmarks. Overlap is context
only: every editable source range belongs to exactly one chunk, preventing conflicting
corrections in adjacent requests.

## 3. Optional dictionaries — project-scoped work planned for v0.4

Dictionary support remains conditional on benchmark evidence and is not part of v0.2.0.

Project dictionaries, if implemented:

- users may create/select multiple small named dictionaries scoped to a project, for
  example `podcast`,
  `training`, or `history_lectures`;
- selected terminology may be provided to correction/translation LLMs as context only
  after explicit project/job selection;
- no dictionary is inherited automatically across projects;
- dictionary use is optional, and its identity and content hash must be included in
  provenance where it affects automated output;
- ASR vocabulary biasing is not enabled by default because an irrelevant dictionary may
  reduce recognition quality.

Dictionary entries may be supplied manually or proposed by analyzing accepted revision
audits for frequent and consistent corrections, including proper names and canonical
forms such as `OpenAI` versus `Open AI`. Automatically discovered items are candidates
only: a user must approve them before they affect correction or translation. Benchmarks
must compare no-dictionary and selected-dictionary runs and detect harmful replacements.
Initial private-corpus candidates include phrase-aware normalization of recurring
`nabiało`/`nabiał` ASR forms to spoken `na biało`, plus the project email's spoken and
written forms (for example `małpaetyka` and `kontakt@etykawpetli.pl`). These examples must
remain project-scoped; they are not safe global replacements. Dictionaries should also
support explicitly approved equivalent aliases for correction and scoring, for example
the Latinized `Csikszentmihalyi` and diacritic `Csíkszentmihályi`. Equivalence must not be
implemented through global accent folding because Polish diacritics are lexically
meaningful.
The course name `AIDEAS` and its ASR/model variants such as `Ideas` or `IDEAS` are another
initial project-specific candidate: a merely plausible capitalization repair is not a
substitute for the approved canonical name.

The correction benchmark must test two dictionary hypotheses explicitly:

- whether the same LLM with an approved project dictionary is materially closer to manual
  gold than the identical model/prompt without one, especially for recurring proper names
  and project spelling conventions;
- whether manual review starting from an LLM candidate reduces reviewer time and accepted
  edit count relative to starting from raw ASR, both without and with dictionary context.

The planned production pipeline uses Gemini 2.5 Flash for the Polish automated-review candidate;
evaluated local models did not improve ASR error rate. Its project-scoped dictionary is
explicit hashed context. The required stage order is:

```text
transcript -> Gemini-assisted Polish review -> manual Polish review -> export
           -> translation (manual or LLM-assisted)
```

Translation normally consumes the accepted Polish revision. Translating an unaccepted
Gemini candidate remains an explicit supported option, but the CLI must warn and the
translation artifact must retain the exact revision with verification
`automated_candidate`, never `manually_verified`.
Correction and translation dictionaries remain distinct versioned artifacts even where
approved project identifiers overlap.

Use a four-branch matrix—raw ASR, LLM only, dictionary-assisted LLM, and manual gold—and
record lexical error, harmful/style changes, reviewer corrections, and review time. A
dictionary is accepted only if gains are not offset by confident harmful replacements.

After all functional requirements and the private benchmark are complete, BIGOS may also
be evaluated as a candidate source for an optional general Polish dictionary. Such a
resource must live in a separate repository catalog from project dictionaries, be
versioned and disabled by default, and require explicit selection. Dataset license and
redistribution terms must be reviewed before committing derived entries. Training or
dictionary-extraction partitions must be disjoint from held-out evaluation partitions;
the same examples cannot both teach the dictionary and inflate its reported WER result.
The no-dictionary baseline remains mandatory.
This post-functional work is an explicit retained TODO: measure ASR error rates on the listed
public Polish datasets first, then derive and manually review a separately versioned general
dictionary from dataset ASR/reference differences. It must not inherit project decisions or
reuse its extraction/evaluation examples across training and held-out benchmark partitions.

The next private correction benchmark is deliberately deferred rather than part of the
immediate v0.3 acceptance path. Manual-gold errata recorded in
`22-v0.3-automated-correction.md` will be published as later immutable revisions when the
translation pipeline is tested. At that point the private benchmark also expands with
manually approved translation examples, its exact-hash manifests are rebuilt, and both
correction and translation baselines are rerun. The current full-corpus correction run
remains the baseline for implementation decisions until that scheduled expansion.

## 4. Manual translation pipeline — implemented v0.4 slice

Translation is a separate pipeline, not a branch inside transcript correction, although
it reuses common versioning, batch, editor, provenance, audit, and future GUI
infrastructure. The manual-first prepare/preview/apply/audit/export slice is implemented
and structurally validated on the private 24-file English corpus. That evidence does not
measure translation accuracy because the approved English text permits artistic freedom.

The future translation source can be:

```text
--source raw
```

for an intentionally dirty/raw canonical translation, or a selected corrected revision.
The latest manually verified compatible revision is the ideal and normal production
source. Raw canonical text and non-final automated-correction revisions remain explicit
experimental/comparison inputs; the pipeline must never silently present either as
manually verified.

Translation requirements:

- the initial supported language pair is Polish and English in both directions. The
  primary production path is Polish podcast audio/transcript to English; the same
  pipeline also translates English materials to Polish rather than maintaining a second
  direction-specific implementation;
- source units are sentence-level after sentenceization of the selected transcript;
- translation mapping is sentence-to-sentence, not word-to-word;
- source sentence timing is retained for target subtitle planning;
- translated word count/order is free to differ from the source language;
- manual translation is implemented first and becomes benchmark ground truth;
- target-language text can itself be manually revised;
- one structured immutable translation artifact becomes the source for target TXT, SRT,
  VTT, and future HTML exports;
- the artifact records exactly which raw result or transcript revision was translated;
- the implemented translation JSON Schema validates complete immutable snapshots and
  exact source lineage.

Translation is source-faithful by default: preserve meaning, intent, tone, level of
formality, technical specificity, repetitions, hedges, emphasis, and speaker character as
far as idiomatic target-language expression permits. Do not summarize, add facts,
silently omit difficult content, censor, or turn spoken language into polished prose.
Literal word order is not required where it would sound unnatural or change meaning.

Style guidance is explicit, optional, and recorded in artifact/provider provenance. The
initial contract uses two independent controls rather than conflating register with
subject matter:

- `register = "preserve" | "formal" | "informal"`;
- `discourse = "preserve" | "academic" | "general"`.

Both default to `preserve`. `formal` and `informal` guide address forms, contractions,
and equivalent register choices; `academic` and `general` guide terminology and expected
reader background. These controls must not authorize factual changes, paraphrased
arguments, invented definitions, deletion of spoken uncertainty, or altered speaker
attribution. Unsupported combinations or language directions fail before provider use.
Benchmarks keep each exact style configuration separate and compare the preserve/preserve
baseline first.

## 5. Automated translation — implemented compatibility slice

After manual translation establishes ground truth:

- local LM Studio and OpenRouter cloud translation providers are implemented for the GUI; expand
  CLI provider parity only with a separately qualified operator workflow and benchmark evidence;
- benchmark local instruction models as first-class translation candidates rather than
  assuming correction-pipeline rankings transfer to translation. Translation quality may
  differ materially because a verified source removes many ASR/proper-name ambiguities
  that harmed dictionary-free correction;
- retain provider/model/prompt/config provenance;
- use configurable chunks/context appropriate to the model;
- preserve sentence-level source mapping and source time spans;
- allow manual revision of automated translations;
- benchmark automated output against manual translations separately from transcript
  correction quality.

Both manual and automated translation must support a later manual revision pass, exact
source/parent lineage, batch resume and failure isolation, and deterministic regeneration
of every translated export. Evaluation must keep translation quality separate from
upstream ASR/correction quality.

Useful benchmark paths include:

```text
raw PL -> automated translation -> compare with EN gold
manual corrected PL -> automated translation -> compare with EN gold
raw PL -> automated correction -> automated translation -> compare with EN gold
latest manually verified PL -> local-model translation -> compare with EN gold
latest manually verified PL -> cloud-model translation -> compare with EN gold
manual corrected EN -> automated translation -> compare with PL gold
```

The principal model comparison holds source, sentenceization, style guidance, prompt,
and scoring constant and varies only provider/model configuration. Reports distinguish
local from cloud execution and include translation quality, unsupported meaning changes,
terminology/name handling, sentence-lineage preservation, latency, resource use, request
volume, and cost where applicable. Dictionary-assisted translation is a later separate
branch rather than part of the initial no-dictionary baseline.

Initial reference local-model candidates are:

- Qwen 2.5 32B Instruct Q4;
- Bielik 11B Q8;
- Llama 3.3 8B Q8;
- MADLAD-400;
- NLLB-200.

These are benchmark candidates, not validated compatibility, quality, licensing, memory,
or packaging claims. Exact model artifact, revision, quantization, backend, prompt, and
hardware must be recorded. General instruction models and translation-specialized models
may require different provider adapters and request contracts while producing the same
validated translation artifact.

Current conclusion: local LLM translation is usable as an explicitly non-final candidate,
but is not recommended for publication-quality translation because observed output is too
mechanical and still needs full human semantic and convention review. The completed Bielik
gate tested compatibility and workflow behavior, not comparative quality; broad sweeps over
models and generation settings are intentionally out of scope for the functional gate.

Optional post-functional work may revisit local translation quality only after the remaining
functional requirements are complete and a scalable semantic-comparison method avoids manual
review of entire corpora for every model/configuration. Until then, do not schedule wide local
model sweeps or infer a ranking from the single-model compatibility pilot.

Polish-to-English and English-to-Polish are separate benchmark suites. They use separate
manually approved gold translations, aggregate metrics, qualitative review, failure
analysis, and rankings; results must not be averaged into one bidirectional score that
hides direction-specific weaknesses. The primary production acceptance gate is `pl -> en`.
The reverse `en -> pl` suite independently qualifies the same pipeline for English source
materials.

## 6. Content-aware directory discovery

- Replace the directory extension allowlist with a bounded ffprobe-based candidate
  classifier so any FFmpeg-decodable audio can be included without treating documents,
  cover art, and other ordinary siblings as failed transcription jobs.
- Preserve the current rules for symlinks, recursion, natural ordering, and direct-file
  errors, and emit a structured skip reason for non-audio files.
- Avoid probing each accepted source twice by carrying trusted probe data into inspection.

## 7. Audio repair

- problem-type classification;
- denoising;
- loudness normalization;
- clipping repair where feasible;
- dereverberation;
- creation of a new working file without modifying the source;
- separate SHA-256 for the processed variant;
- `off`, `ask`, and `auto` modes;
- comparison of original and repaired audio.

## 8. Transcript comparison

- transcribe original and repaired audio;
- compare confidence and agreement automatically;
- difference report;
- select the better result or a controlled hybrid;
- preserve both canonical results.

## 9. Presets and benchmark

- `balanced`;
- `low-vram`;
- optional `cpu-only`;
- optional Apple Silicon preset after a compatible application build exists;
- automatic batch-size selection;
- bundled or explicitly downloaded licensed audio samples;
- benchmark of speed, VRAM, WER, timestamps, and diarization;
- repeatable wall-clock, real-time-factor, per-stage duration, peak process RAM, and
  sampled peak VRAM measurements for every preset comparison;
- retain raw measurement provenance so later hardware and dependency baselines can be
  compared without relying on terminal summaries;
- HTML/JSON report;
- hardware comparison.

These names are roadmap targets, not current compatibility or quality claims. Preset
acceptance requires complete transcription and correction benchmarks on its stated
hardware. No preset below the GTX 1070 target is planned.

### Low-VRAM local correction target

The lowest planned GPU tier will be physically validated on a PC with an NVIDIA GTX 1070
in addition to later testing on the reference RTX 3090. Candidate instruction models and
quantizations are:

- Bielik 3.0 11B Instruct: IQ4_XS or Q3_K_L;
- Qwen 2.5 7B Instruct: Q5_K_M or Q6_K;
- Llama 3.1 8B Instruct: Q5_K_M;
- Gemma 2 9B Instruct: Q4_K_M.

Final membership depends on measured load success, memory headroom, throughput, correction
quality, faithful-speech behavior, and complete-job stability. Merely loading a model does
not qualify it.

Initial reference-workstation evidence for the quality-first local tier: Qwen 2.5 14B
Instruct Q8_0 loaded in LM Studio with a 32K context and used approximately 18.5 GB VRAM
on the 24 GB RTX 3090. Bielik 3.0 11B Instruct will compare Q8_0 against F16 with CPU
offload. These observations are configuration-specific baselines, not guarantees for
other systems.

### Optional CPU-only correction target

The CPU-only preset targets a recommended minimum of 16 GB system RAM. Candidates are:

- Bielik 3.0 11B Instruct: Q5_K_M or Q6_K;
- Qwen 2.5 14B Instruct: Q4_K_M;
- Mistral NeMo 12B Instruct: Q4_K_M.

Benchmark reports must include CPU model, usable RAM, thread settings, latency, throughput,
peak process RAM, correction quality, and whether swapping occurred. The 16 GB figure is a
planned validation floor, not an accepted requirement until those runs pass. The planned
physical CPU-only validation machine has 32 GB RAM; operation below 16 GB is out of scope.

### Optional Apple Silicon correction target

Apple Silicon support is deferred until all functional requirements are complete and a
separate compatible transcriber build has been prepared. The planned minimum is 16 GB
unified memory. Candidates are:

- Bielik 3.0 11B Instruct: Q5_K_M, Q4_K_M, or MLX 4-bit;
- Qwen 2.5 14B Instruct: Q4_K_M or MLX 4-bit;
- Mistral NeMo 12B Instruct: Q4_K_M;
- Qwen 2.5 7B Instruct: Q8;
- Llama 3.1 8B Instruct: Q8.

Because no local Mac is available, validation may use explicitly rented Apple hardware
from MacinCloud and/or Scaleway. This is infrastructure access, not permission to send the
private corpus to an unrelated LLM API. Tests should cover the native CLI first and the GUI
when available, and record the exact Apple chip, unified memory, OS, runtime/backend,
quantization, cost, and benchmark provenance.

The expanded manual correction corpus should also become the reference source for lexical
correction benchmarks. Separate timestamp and diarization ground truth is still required
for timestamp/DER/JER evaluation.

### Public-dataset validation after functional completion

After all functional requirements pass and private-corpus evaluation is complete, add a
reproducible public-dataset matrix comparing supported ASR models, presets, correction
paths, and optional dictionaries. Candidate lexical/recording corpora are:

- BIGOS, for Polish WER evaluation and possible general-dictionary candidate extraction;
- Google FLEURS, for multilingual recordings and references;
- Mozilla Common Voice;
- Multilingual LibriSpeech.

Candidate diarization corpora are:

- VoxConverse;
- AMI Meeting Corpus.

### Ephemeral speaker auto-discovery research — later

Research options for within-job speaker discovery when the operator does not know whether a
meeting contains, for example, three or four speakers. Evaluate whether the existing
`speaker_count = auto` diarization behavior is sufficient or needs a clearer explicit
auto-discovery mode, confidence reporting, lower/upper bounds, or alternative clustering.
Candidate work should compare diarization embeddings and within-recording clustering against
fixed-count operation on held-out meeting material, including overlap and short-speaker cases.

Any speaker “fingerprint” in this feature means an ephemeral representation used only to
cluster segments inside the current job. It MUST NOT create a general identity database,
label a real person across recordings, or be written as reusable biometric identity data.
Artifacts may retain ordinary anonymous `speaker_NNN` assignments and audit parameters, but
the temporary embeddings/fingerprints are discarded when the job finishes.

Extend the browser review editor with safe block splitting/merging so a word or sentence can
be reassigned to the correct speaker without moving unrelated text. Revision-scoped speaker
display-name editing and revision-local speaker addition are externally qualified for recordings
whose canonical result lacks useful names, misses a speaker, or combines multiple speakers on
one source channel. Unused local speakers can be removed, while text-assigned speakers require
reassignment or merging before removal.

The editor-recovery/comfort slice is externally qualified: it saves a dirty mutable draft before
each structural block-edit operation, offers explicit bounded Undo and Redo for the current
editor history, and groups controls by workflow. The left group presents **Prepare** then
**Preview**. The right group presents **Save** and **Restore**, then **Undo** and **Redo**, with
the destructive **Clear** control in the lower-right. Undo/Redo affects only the mutable review
draft, keeps protected anchors/lineage intact, and still requires an explicit save plus preview
before immutable application.

Every dataset requires a pinned version/configuration, source and license record,
download/preparation hashes, official split preservation, normalization declaration,
language/subset selection, and a report of exclusions. WER/CER comparisons must not mix
dictionary-training material into their held-out test split. Diarization experiments must
report DER/JER methodology, collar and overlap policy, speaker-count assumptions, and the
exact pyannote/segmentation settings. Results should be presented as a table alongside
the private real-podcast benchmark, not merged into one opaque score.

An optional later real-world tier may add a small number of long-form public YouTube
podcast discussions with three or more speakers. Inclusion requires a separate license,
terms, privacy, and redistribution review plus manually verified references. URLs or
public availability alone do not authorize committing media or transcripts. This tier is
supplementary and does not replace controlled WER or diarization corpora.

## 10. Advanced channel handling — later, release unassigned

This remains on the later roadmap without an assigned release and is not on the current
critical path.

- detect and remove duplicates caused by crosstalk;
- compare channel transcripts with timestamps;
- preserve legitimate single-word and rhetorical repetitions;
- support more than two channels with explicit topology rather than treating channel
  count as speaker count;
- for isolated speaker channels, split selected channels, expose the channel/speaker map
  and warning, transcribe separately, and merge chronological timelines;
- for general multichannel and cinematic 5.1/7.1 audio, use a layout-aware program
  downmix plus diarization and clearly report the transformation;
- automatically use that fallback only for a recognized channel layout; require a
  dedicated explicit `program-mix` topology choice for missing or unsupported layouts,
  and do not overload output-versioning `--force`;
- never silently use one channel as a complete transcription of 3+ channel media.

## 11. Subtitles

Two conservative TTML pilots were accepted with correct timing, language, turn labels, and
diacritics, but YouTube ignored wrapping, centering, and colors. The active implementation
therefore targets YouTube's srv3 YTT XML based on an owner-supplied accepted example. It
remains opt-in because it is platform-specific. Its first upload centered cues and
preserved text/timing but flattened `<br/>` line elements. The owner-supplied corrected
template instead uses literal in-paragraph newlines and near-white `#FEFEFE`; the renderer
now matches that structure byte-for-byte. The final unlisted upload passed two-line
wrapping, distinct speaker colors, centering, timing, turn labels, and Polish diacritics.
The profile is qualified for the tested real Polish two-speaker case and stays opt-in as a
platform-specific export.

- add a deterministic `.ytt` export using YouTube's srv3 timed-text XML profile;
- use UTF-8 XML with `<timedtext format="3">` and millisecond `t`/`d` timing;
- map exactly one already-planned canonical subtitle cue to one `<p>`; YTT rendering
  must not introduce another cue segmentation pass;
- give every spoken cue a deterministic numeric speaker pen derived from stable speaker order;
- print the visible speaker name only on the first cue of a continuous speaker turn while
  retaining that speaker's style on every continuation cue;
- keep speaker colors in renderer configuration, never transcript data. The initial
  ordered fallback palette uses the normal/default foreground for the first stable
  speaker, blue for the second, yellow for the third, then distinct green, magenta, and
  cyan entries for additional speakers. Exact color values and palette exhaustion rules
  require an unlisted YouTube smoke test and remain configurable;
- allow a separate italic pen for structured non-speech cues, but do not infer
  non-speech semantics or italics from transcript punctuation or text;
- use the tested srv3 centered window and bottom-center position records without adding
  unrelated generated-format attributes;
- serialize with a real XML serializer, escape text and attributes, reject invalid XML
  instead of emitting it, and test parsing, namespaces, language, cue cardinality,
  timing, pen references, line breaks, escaping, and deterministic bytes;
- manually validate upload acceptance, Polish diacritics, timing, labels, and speaker
  colors on YouTube before treating the profile as qualified;
- styled WebVTT;
- ASS/SSA;
- burned-in subtitles;
- platform presets;
- visual preview.

Before non-speech-aware YTT or HTML rendering is implemented, design and version an
additive canonical JSON schema update that records the semantic `kind` of a timed event.
The initial vocabulary must at least accommodate `speech`, `music`, `laugh`, `cough`,
and `note`, while defining whether the field belongs on segments/cues or a distinct event
structure and how older results default to speech. This is semantic transcript data;
presentation choices such as colors, labels, brackets, and italics remain renderer
configuration. Schema documentation, migration/compatibility behavior, fixtures, and
raw/revised export tests are required before enabling the field in production output.

Implemented foundation: canonical schema `1.1` places the closed kind vocabulary on timed
segments; schema `1.0` omissions default to `speech`. Effective raw/revised projection, derived
segment JSON `1.1`, and subtitle cue planning preserve kind without changing current SRT/VTT
presentation. See `24-v0.4-timed-event-semantics.md`. Explicit non-speech authoring and
renderer styling remain separate later slices.

## 12. Platform transcript delivery and HTML — planned for v0.4

Implemented foundation: raw and manually revised `--format html` exports now emit the
specified escaped, deterministic fragment with sentence-level native buttons, explicit
speaker turns, BCP 47 language, and integer timing/speaker/kind metadata. Immutable
translation artifacts use the same contract with target language/text and inherited unit
timing. No CSS, JavaScript, inline styles, or event handlers are emitted. The consuming
mock player is implemented separately with native audio, site-owned CSS/JavaScript,
click/keyboard seeking, current-sentence following, accessible focus, reduced-motion,
light/dark presentation, and readable unenhanced markup. A manual real-media browser check
passed Firefox/LibreWolf but exposed Chromium-family clicks restarting at zero. The retry
waits for metadata and seek completion and adds explicit theme/auto-follow controls. A
second Chromium retry isolated the remaining failure to the basic Python static server;
the example now includes a single-range `206 Partial Content` server. The final retry
passed Chrome and Brave seeking; Firefox and LibreWolf, theme/auto-follow controls, and the
no-script fallback also passed. The HTML delivery slice is accepted. Occasional minor
acoustic spill across sentence boundaries is inherited from word alignment and deferred
to alignment-quality work; renderers must not hide it with heuristic timestamp shifts.

- qualify SRT and WebVTT behavior on YouTube, Spotify, Apple Podcasts, and selected web
  audio/video players; record account- or host-dependent limitations;
- publish multiple Podcasting 2.0 transcript links where appropriate, including a
  readable transcript and a timed caption resource;
- build an accessible synchronized HTML transcript from the selected effective transcript
  or suitable derived timed data, with sentence-level seeking, current-sentence
  highlighting, and keyboard controls;
- add HTML as an explicit generated export (`transcriber export --format html`), with a
  UTF-8 embeddable fragment—not a standalone document—that requires no transcription
  rerun. Its root is `<section class="ewp-transcript">` with a valid BCP 47 `lang`;
- represent speaker turns explicitly. Every cue retains integer `data-start-ms` and
  `data-end-ms` values, and stable machine-readable speaker identity uses `speaker_id`,
  never the display name;
- keep visible speaker names as escaped presentation text shown once per turn, retain
  logical reading order, and make the fragment useful with CSS and JavaScript disabled;
- emit transcript text as escaped plain text: no trusted transcript markup, inline style,
  embedded CSS, inline JavaScript, or event-handler attributes;
- apply light/dark mode, accessible contrast, branding, active-cue state, and speaker
  colors only in consuming-site CSS. Seeking, highlighting, and auto-scroll belong to
  consuming JavaScript rather than the generated fragment;
- define export presets for conservative platform interchange and web-native playback;
- design translated/bilingual HTML after the translation artifact contract exists.

Acceptance includes a separate self-contained mock/placeholder site that embeds the
generated fragment alongside a real HTML audio player and supplies its own CSS/JavaScript.
Playback highlights or follows the active cue, and activating a transcript sentence seeks
the player to that sentence's start time. Renderer tests must cover the exact root and
language contract, explicit turn grouping, stable speaker IDs, integer timestamps,
escaping/untrusted text, absence of CSS/JavaScript/inline styles, deterministic output,
and raw/revised/translated sources. Mock-site tests additionally cover keyboard operation,
accessible seeking, light/dark presentation, and behavior with enhancement disabled.

The reviewed `ewp_transcripts_agent_pack` contracts are compatible with this direction
after these scope decisions: implementation is scheduled for v0.4, HTML output is
fragment-only, YTT is specifically a YouTube srv3 profile, and RSS transcript
material is publishing policy rather than a required exporter. Its examples are design
inputs, not accepted golden files; repository terminology, current cue generation, schema
versioning, and exporter architecture remain authoritative during implementation.

## 13. GUI

GUI remains deliberately late in the roadmap so the application/domain contracts are
stable first. ADR-0021 selects one self-contained local browser application shared by WSL2,
bare-metal Ubuntu, and the future Docker image. The normative workflow, path, privacy,
security, accessibility, and implementation-slice contract is in
[`26-local-web-gui-contract.md`](26-local-web-gui-contract.md).

Planned capabilities:

- file, directory, and group selection;
- add and qualify optional cloud-based speech-to-text providers for hardware-constrained
  environments. Local transcription remains the default local-first path, but a cloud adapter
  may let the application operate as a light orchestration/review/export client when the operator
  explicitly accepts that media and transcript data leave the machine. It must retain provider,
  model, endpoint, cost/usage where available, consent, source identity, and failure provenance;
  produce the same canonical-result contract or fail closed; and receive separate accuracy,
  timing, privacy, retry, and manual-workflow testing before it is presented as supported.
- dry-run preview;
- audio-stream selection;
- per-file language selection and speaker-count selection, including clearly labeled
  automatic choices and the later ephemeral auto-discovery research mode;
- persistent named media/project roots managed through an explicit local configuration or launch
  workflow, so ordinary use does not require repetitive path flags while browser requests remain
  unable to grant themselves broader filesystem authority;
- replace the current testing-oriented allowed-root allowlist with a reviewed local-user safety
  policy that blocks clearly dangerous system locations and path traversal without making normal
  media locations unusable; pair it with an operating-system file/directory picker rather than
  relying primarily on custom browser path text fields;
- content-aware input validation and time-of-check/time-of-use protection: retain strict JSON
  parsing and FFprobe decoding, then compare exact source fingerprints again when a staged job
  starts. This pre-open fingerprint check is implemented; evaluate an optional owned immutable
  input snapshot for workflows where files may change during processing, because a check alone
  cannot eliminate every race before a decoder opens the file. Do not rely on filename extensions
  or non-portable long-lived locks alone;
- warning display and job queue;
- support directory scanning and checkbox selection of recognized canonical JSON results for
  later correction, review, and translation queues. The first queue presentation slice now
  derives visible per-item queues from completed GUI transcription records; directory scanning
  remains required to include independently discovered canonical results. Every workflow stage
  should expose a compact per-item queue with the same grey/green/red/blue legend, allowing work
  to resume at any stage;
- make each stage queue an expandable, visible control surface even when it contains only one
  item. It must let an operator reopen or restart that specific stage for any queued item rather
  than relying on whichever document was most recently open. Correction and translation queues
  must additionally support explicit checkbox bulk selection and **Select all**, while preserving
  individual dictionaries, consent, provenance, retry bounds, error isolation, and review gates;
- after the individual optional LLM stages are fully qualified, add explicit batch correction and
  batch translation operations for compatible queued items. They must preserve the same per-item
  consent, provenance, bounded retry, resumable state, error isolation, and manual-review gates
  as individual operations; they must not be implemented as an unbounded loop behind a cosmetic
  bulk button. Batch correction may start per completed cloud-backed transcription while other
  transcription jobs continue. Batch translation must list the newest accepted revision for each
  chosen job, allow a distinct project dictionary per item, disable completed current-version
  items, and re-enable an item when a newer verified source revision exists;
- an explicit visible workflow progression: transcription, transcript review (or provisional
  export), apply and verified export, then optional translation, translation review (or
  provisional export), apply, and verified translated export;
- transcript correction and speaker-attribution editing;
- hide review anchors while retaining the same internal revision mapping;
- rebalance transcript-review anchors around a target number of visible speaker blocks while
  preserving revision-safe word boundaries and immutable source mapping; this is an ergonomics
  improvement, not permission to alter canonical timing or text;
- preview revision changes without applying them;
- re-export raw or selected revision without ASR;
- translation and translated-text revision after those pipelines exist;
- secure handling of optional API credentials;
- audio-following review where useful;
- an About section with application/version information;
- add maintained project URL and project-website metadata when the public destination is ready;
- a License section presenting the applicable license and warranty notice;
- a Source Code section with a direct link to the public project repository:
  <https://github.com/Polikles/ewp-transcripts>.
- a manual plain-language review of all bundled and repository instructions with
  less-technical users after the workflow stabilizes; screenshots are added after that pass.
- a floating left-side workflow navigator, designed with the eventual podcast branding, that
  follows the page, identifies the active file, mirrors per-stage status circles, offers direct
  step navigation, and includes a **Back to transcription queue** action. Exact visual layout is
  deferred until functional GUI coverage is complete.
- replace interim CSS spinners and status circles with the approved project icon system during
  that same branding pass, without making status depend on color or animation alone.
- after functional GUI coverage, a dedicated frontend pass that aligns appearance with the
  owner's other projects and adds final responsive light/dark styles;
- add table-of-contents navigation and collapsible top-level workflow sections as correction,
  translation, and dictionary functions make the page longer;
- after GUI function coverage, replace the interim long page with numbered workflow tabs or
  equivalent routed views for transcription, optional correction, review/export, translation,
  and semantic review/export; keep dictionary and settings management in separate tabs while
  preserving state across navigation;
- add a bounded recent-work browser for saved GUI review sessions, labeled by optional project
  name plus job/input identity, so recovery does not require remembering an output root; handle
  expired temporary paths as unavailable entries;
- add allowed-root-constrained Browse controls for transcript/result/dictionary inputs and
  output directories without uploading files or exposing an unrestricted filesystem browser;
- an explicit light/dark mode switch in that pass; automatic system preference remains an
  interim behavior rather than the final theme control.
- add explicit next-step actions after apply/export that carry exact canonical, revision,
  language, project, and output context into the following workflow; selecting a revision
  should prefill its canonical source whenever exact lineage resolves it unambiguously;
- make installed and custom dictionary directories discoverable through project/language/
  version selectors, while retaining direct allowed-root path selection;
- add GUI dictionary proposal, preview, decision editing, versioned publication, and audit
  views with bundled plain-language workflow documentation;
- persist non-secret preferences such as common output roots and dictionary locations;
  application settings must support versioned import/export, with a deliberate option to
  include or omit custom dictionaries and no secret/API-key export;
- add explicit Save current work state and Load previous work state actions. A versioned
  server-side workspace record should restore all non-secret fields, staged artifact paths,
  terminal queue history, open saved review, and current workflow step after a full
  workstation/VM restart, while revalidating allowed roots and hashes and never persisting
  credentials or unsaved edits. Terminal history and hash-bound staged jobs are implemented;
  interrupted GPU work remains intentionally non-resumable;
- when functional GUI work is complete or nearly complete, qualify one full cross-directory
  workflow with several inputs and one shared output root: transcription, optional correction,
  manual verification/export, translation, semantic review, and translated export;
- after that end-to-end qualification, perform the dedicated GUI visual overhaul so it aligns
  with the Ethics in the Loop blog and podcast branding;
- shortly before public release, add an explicit Polish/English interface-language selector
  alongside the final light/dark toggle and persist both preferences;
- add consistent accessible information controls for unfamiliar options, beginning with
  non-loopback endpoints, and link them to the corresponding bundled local documentation;
- expand bundled help into a designed pipeline guide covering transcription, optional LLM
  correction, manual verification, export, optional translation, semantic review, and final
  translated export.

The GUI calls application services directly and MUST NOT execute CLI commands as a
subprocess or maintain a second revision/translation model.

Implementation begins before Docker with the loopback server and read-only inspect/dry-run
slice. Docker later packages the already qualified application and provides explicit host
mounts; it does not receive a separate frontend. Browser uploads, remote listening,
authentication, and multi-user hosting are not part of the initial GUI.

## 14. Distribution

No internal beta is tagged or published while requirements work continues. The first public
release is a deliberate checkpoint immediately before Docker-image implementation begins;
Docker artifacts are not the mechanism used to discover whether the source application is
releaseable.

- For v0.3, provide a reviewable fresh-install and verification script that installs and
  verifies prerequisites, the locked application environment, model readiness, and
  diagnostics while retaining explicit consent for gated model access and avoiding
  hidden system changes. Updating an existing installation is a separate workflow and
  must not be silently folded into the fresh-install script.
- For v0.3, restructure the root README with concise `Prerequisites`, `How to install`,
  and `How to use` sections. Prerequisites must summarize supported WSL2/bare-metal
  Ubuntu shapes, required Ubuntu packages, the validated software/hardware stack, a
  recommended minimum of 20 GB on preferably SSD storage, and the fact that RAM/VRAM
  requirements remain pending preset validation. Installation must briefly invoke the
  fresh-install script. Usage must show representative transcription and staged review
  command syntax and link to the complete `Instructions/` runbook.
- GPU-enabled Docker image;
- pinned image versions;
- local service/API;
- GUI installer;
- Ubuntu 26.04 LTS qualification;
- optional native Windows support as Tier 2.
- Canonical repository and issue-tracker URLs are present in package metadata and release
  surfaces.
- Add the public project website once its address and deployment are ready.

The fresh instance used for the v0.3 correction benchmarks was installed from the
v0.2.1-era repository and supplies sufficient installation evidence for the current
development gate. A redundant manual installation-only rerun is not required for v0.3.
Full clean-machine validation later passed manually for the current beta line on a fresh Ubuntu 24.04.4
WSL2 distribution, covering installation, pinned-model setup, transcription, restart-safe
replay, automated and candidate-backed review, verified export, and local translation
candidate/audit/review preparation. Automation is designed only after the manual procedure
and expected evidence have stabilized.

## 15. Operations

- `fail-fast`;
- explicit per-input aliases/output identities for intentionally processing separate
  same-stem sources in one batch, without overloading result versions or context-dependent
  canonical IDs;
- queue scheduling;
- automatic cleanup of old work directories;
- quality-trend reports between releases.

Before the CLI is declared ready for general users, create a top-level `Instructions/`
directory containing a concise operator runbook for every shipped command and workflow:
installation/model preparation, doctor, inspect, dry-run, single/group/batch transcribe,
revision prepare/preview/apply/audit, raw/revised batch export, cleanup, warnings,
recovery, privacy, and command-specific `--help` discovery.
