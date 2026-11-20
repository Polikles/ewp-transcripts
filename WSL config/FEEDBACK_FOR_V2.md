# Collect feedback for V2

Historical feedback guide. Current acceptance/scope is recorded in
[the roadmap](../docs/99-roadmap-v2.md#owner-scope-and-current-status--2026-11-20).
Do not restart the completed pilot or require a new corpus/benchmark campaign from this guide.
Ordinary podcast-workflow feedback remains useful; research evaluation is optional.

The first internal pilot should reveal the correction and delivery workflow that V2
actually needs. It is not another release gate and should use real archive material.

## 1. Select a bounded pilot

Choose 3–5 episodes that collectively cover useful variation:

- one straightforward episode;
- one episode with two speakers or separate tracks;
- one difficult case such as overlap, music, long silence, names, technical terms, or
  uneven recording quality;
- at least one episode representative of the future blog/player workflow.

Do not begin with the entire archive. Record duration, language, known speaker count,
source topology, and whether the material may later contribute licensed ground truth.

## 2. Preserve original evidence

For every episode retain, outside Git:

```text
source audio
inspect JSON
dry-run output
canonical *_results.json
generated TXT/SRT/VTT
exact command or sanitized config
application commit and result SHA-256
```

Never edit `*_results.json`. Copy generated text into a separate review file. Do not
replace generated exports with hand-edited variants under the same name.

## 3. Classify corrections

Record each correction using one primary category:

- wrong word or omitted/inserted speech;
- proper name, product name, abbreviation, number, or foreign term;
- punctuation, capitalization, quotation, or paragraph boundary;
- sentence/cue split or merge;
- wrong speaker or speaker-label change;
- inaccurate word/cue timing;
- overlap that cannot be represented faithfully;
- hallucination during silence, music, or noise;
- export/readability issue rather than transcription error.

For a useful sample, retain the original text, corrected text, approximate timestamp,
speaker, correction category, and whether the correction was manual, dictionary-assisted,
or LLM-assisted. Private text can remain local; aggregate counts and sanitized examples
are sufficient for design discussion.

## 4. Record workflow friction

Note the human work, not only model accuracy:

- time spent reviewing per hour of audio;
- tools used for listening and correction;
- whether review is easiest by word, sentence, speaker turn, or subtitle cue;
- operations that require split/merge, speaker reassignment, or timestamp adjustment;
- words whose speaker was correct in canonical JSON but changed at a generated review
  boundary;
- canonical sentences missing from a generated review file;
- mistakes caused by editing TXT, SRT, and VTT independently;
- terminology that should become a reusable dictionary;
- information needed to resume an interrupted review;
- privacy boundaries for any local or cloud LLM assistance.

## 5. Review web and platform delivery

For the blog/player use case, record:

- desired seek granularity: word, sentence, or speaker turn;
- current-sentence highlighting behavior;
- speaker colors plus accessible textual labels;
- standalone page versus embeddable fragment needs;
- keyboard, screen-reader, and mobile behavior;
- whether YouTube, Spotify, Apple Podcasts, or Podcasting 2.0 requires a different
  conservative export.

## 6. Minimum feedback summary

After the pilot, provide a sanitized summary containing:

```text
episodes and total duration:
source topologies and languages:
review time:
corrections by category:
speaker/timing/subtitle problems:
repeated terminology or names:
preferred correction tool/workflow (including useful bulk-replace features):
HTML/player requirements:
material eligible for future ground truth:
three most expensive manual operations:
```

This summary determines the V2 correction schema, editor/import boundary, HTML export,
and ground-truth expansion order. Raw private audio or transcript text is not required.
