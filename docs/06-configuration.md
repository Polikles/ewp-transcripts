# TOML Configuration

## 1. Precedence

From highest to lowest priority:

```text
> CLI flag
> file selected with --config
> project configuration
> user configuration
> preset
> application default
```

The effective configuration must be stored in `results.json`, excluding secrets.

## 2. Locations

Recommended locations:

```text
project: ./transcriber.toml (resolved from the command's current working directory)
user: ~/.config/ewp-transcripts/config.toml (applies from every working directory)
```

An arbitrary file may instead be selected with `--config /exact/path/to/file.toml`.
Configuration keys must be placed below their TOML section header; for example,
`editor` belongs below `[revision]`.

The application should not modify project configuration automatically.

## 3. Sections

Complete example: [`../examples/config.example.toml`](../examples/config.example.toml).

- `[general]` — language, preset, offline mode, interactivity;
- `[input]` — recursion, supported formats, symbolic links;
- `[grouping]` — speaker separator and duration thresholds;
- `[channels]` — classification mode and thresholds;
- `[models]` — models, cache paths, compute type, batch size;
- `[diarization]` — model, speaker count, overlap behavior;
- `[subtitles]` — cue rules and the ordered YTT speaker-color palette;
- `[outputs]` — default exports and naming;
- `[runtime]` — work directories, temporary files, locks, logging;
- `[quality]` — diagnostics without audio repair.
- `[correction]` — automated-correction editable chunk and read-only context sizes.

YTT export is disabled in default output generation because it is YouTube-specific.
Request it explicitly with `--format ytt`, or set
`[outputs].generate_ytt = true`. `[subtitles].ytt_speaker_palette` is a non-empty ordered
list of `#RRGGBB` colors; it cycles deterministically when a transcript has more speakers
than configured colors. Speaker colors remain presentation configuration, not transcript
data.

HTML fragment export is also opt-in: request `--format html`, or set
`[outputs].generate_html = true`. The generated fragment deliberately has no renderer
styling or behavior configuration because CSS and JavaScript belong to the consuming site.

Fresh transcription defaults to canonical JSON, machine-readable segments JSON, and a TXT
preview. SRT and VTT are disabled by default so unreviewed ASR is less likely to be mistaken
for publication-ready subtitles. All formats remain available through explicit
`transcriber export`; the recommended production path reviews and applies a revision first.

### Warning-only quality thresholds

Inspection decodes each source once and reports four lightweight diagnostics. The MVP
defaults are deliberately conservative:

| Key | Default | Warning condition |
|---|---:|---|
| `clipping_min_sample_ratio` | `0.0001` | At least this fraction of decoded PCM samples is at or near full scale. |
| `low_level_max_rms_dbfs` | `-35.0` | The louder channel's overall RMS is at or below this level. |
| `channel_imbalance_min_rms_difference_db` | `6.0` | A true two-channel source differs by at least this RMS level. |
| `high_silence_min_ratio` | `0.5` | At least this fraction of 500 ms windows has neither channel active. |

Individual `detect_*` switches may disable a warning, and `analyze = false` disables all
four. Diagnostics never normalize, repair, or otherwise modify input audio. These
thresholds are an initial operational baseline and must be recalibrated on the future
larger dataset.

## 4. `accurate` preset

The MVP preset is optimized for an RTX 3090 and prioritizes quality. It should define:

- `large-v2` by default, selected through ADR-0007's initial project benchmark;
- CUDA `float16`;
- a batch size validated by an OOM stability test;
- word alignment;
- full diarization when required;
- no quality-reducing quantization;
- no automatic audio repair.

The ASR model and batch size must remain configurable.

Model selection is separate from local artifact resolution. The `[models]` and
`[diarization]` sections record, for ASR, Polish word alignment, and Community-1:

- the model or repository identifier;
- the exact immutable revision;
- the explicit local snapshot directory.

The snapshot path is authoritative at transcription time. EWP-transcripts does not
search an arbitrary Hugging Face cache, resolve a moving branch, or download a missing
artifact while transcribing. Each snapshot path must end with its configured revision;
existence and model compatibility are checked by the runtime operation that loads it.
The packaged paths assume the standard `~/.cache/huggingface` location established by
the WSL setup guide. Installations with a different `HF_HOME` must override all three paths.

The selection is provisional because the comparison corpus contained only three cases. A larger manually verified corpus may justify changing the default through a new or superseding ADR.

## 5. Validation

- unknown keys: error in strict mode, warning in compatibility mode;
- out-of-range values: error before models are loaded;
- CLI/TOML conflict: CLI wins and the override appears in debug logs;
- secrets are not allowed in project TOML.

## 6. Compatibility

Configuration should include an optional version:

```toml
config_version = "1.0"
```

Changing the meaning of an existing key requires a major configuration-version update or a migration layer.


## 7. Transcript revision configuration

Manual revision uses the normal precedence rules and adds a strict `[revision]` section.
The v0.2.0 defaults are:

```toml
[revision]
anchor_target_words = 200
anchor_target_speaker_blocks = 5
long_gap_warning_ms = 2000
generate_audit = false
editor = ""
```

- `anchor_target_speaker_blocks` is the preferred number of consecutive speaker blocks shown in
  one GUI review section. The final section can contain fewer blocks. Set it to a positive value
  to keep review navigation consistent; it defaults to `5`.
- `anchor_target_words` is retained as the approximate review/alignment window size for callers
  that deliberately disable speaker-block grouping.
- `long_gap_warning_ms` controls the warning for inserted text positioned between
  canonical source words separated by a large pause. It does not move canonical timing.
- `generate_audit` controls optional detailed audit persistence; compact provenance and
  statistics remain mandatory.
- an empty `editor` uses the `VISUAL` environment variable and then the `EDITOR`
  environment variable for `revise edit`. Their values must be installed commands such
  as `nano` or `code --wait`; the words `VISUAL` and `EDITOR` are not commands.

Revision batch failure behavior reuses the existing runtime batch policy rather than
introducing a duplicate correction-only setting.

## 8. Automated-correction configuration

The first v0.3 correction slice defines:

```toml
[correction]
provider = "" # disabled; set explicitly to "lm-studio" or "openrouter"
model = "" # exact identifier reported by the selected provider
endpoint = "http://127.0.0.1:1234/v1"
openrouter_endpoint = "https://openrouter.ai/api/v1"
openrouter_api_key_env = "OPENROUTER_API_KEY"
# openrouter_reasoning_max_tokens = 0
allow_remote_endpoint = false
output_mode = "json-schema"
prompt_id = "faithful-correction-v11"
target_tokens = 600
max_tokens = 800
context_tokens = 80
timeout_seconds = 120
max_attempts = 3
retry_delay_seconds = 1.0
temperature = 0.0
consent_store = "~/.config/ewp-transcripts/correction-consent.json"
```

These count application transcript tokens, not provider-specific tokenizer units.
`target_tokens` guides preferred boundary selection, `max_tokens` is a hard editable
limit, and `context_tokens` bounds read-only context on each side. All must be
overrideable through normal configuration/application requests. The maximum context of
any provider model MUST NOT be hard-coded into the revision engine. Defaults remain
subject to benchmark-driven adjustment before v0.3 acceptance.

Automated correction remains disabled while `provider` is empty. `lm-studio` accepts an
uncredentialed HTTP(S) endpoint whose path ends in `/v1`. Loopback is required unless
`allow_remote_endpoint = true` or the matching CLI flag explicitly opts into a LAN,
VPN, or Tailscale-like address. This opt-in does not make a remote process private or
guarantee transport confidentiality. `model` must be the exact identifier exposed by
LM Studio. Timeouts and retry counts are per chunk.
`output_mode = "json-schema"` is the default and requests grammar-constrained structured
output from LM Studio. Use `output_mode = "json-text"` only as an explicit compatibility
fallback when a model/chat-template combination cannot initialize LM Studio's JSON-schema
grammar. The fallback omits the API `response_format`, but the application still requires
the entire response to be one schema-valid JSON document and retains all reconstruction,
speaker, and token-drift safety gates. Markdown fences, explanatory prose, and malformed
JSON are rejected. The selected mode is included in the prompt hash, so resume state from
one mode cannot be reused by the other.
The consent store contains only non-secret exact scopes and is created with private
permissions; API keys never belong in this configuration.

`openrouter` is an explicit cloud provider. Its endpoint must be an uncredentialed HTTPS
URL ending in `/api/v1`. The CLI secret is read lazily from the environment variable named by
`openrouter_api_key_env`. The loopback GUI may instead accept a key into server-process memory
for the current run; it clears the browser field immediately and never persists the value. The
value is never accepted in TOML, CLI arguments, provenance, resume state, or logs. A cloud
command additionally requires `--allow-cloud` and scoped
reject/once/persist consent. The adapter disables provider fallback and requires support
for requested structured-output parameters. Pin the exact model slug reported by the
provider; never silently substitute a similarly named model.
The GUI readiness check validates OpenRouter credentials through the authenticated
`GET /api/v1/key` endpoint before separately reading the model catalog. A public model-list
response alone is not evidence that the supplied key is valid.
The GUI's bundled OpenRouter presets show approximate listed input/output tokens per USD for
orientation. `Check models and pricing` explicitly refreshes the three bounded preset records
from `/models`; rates are mutable external evidence, not configuration or a cost guarantee.
`openrouter_reasoning_max_tokens` is optional and provider-specific. Set it to `0` to
disable thinking on supported models such as Gemini 2.5, or use a positive explicit budget
for a separately identified benchmark run. The value participates in prompt/resume identity
and non-secret provenance; omitting it preserves the provider/model default.
