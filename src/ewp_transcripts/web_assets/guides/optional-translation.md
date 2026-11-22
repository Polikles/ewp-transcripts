# Optional translation

Use the numbered steps below with the matching GUI stage.

1. Choose source recording: Choose a recording and its verified source revision. Skip LLM-assisted translation below the queue to translate manually.
2. Choose translation direction: The source language selects the default direction. Accept a direction change explicitly and choose a matching source recording.
3. Generate candidate: For API assistance, choose provider/model, check readiness, consent and generate a non-final candidate. Source details and the optional dictionary can be expanded.
4. Continue to translation review: Review meaning and speakers in Translation review & export before applying and exporting.

## 1. Choose source recording

Select a recording and preferably its manually verified source revision. An unreviewed ASR result or correction candidate can be translated explicitly, but its weaker verification status is recorded; it is not promoted to human-verified text. To translate manually, use Skip LLM-assisted translation below the queue, then open translation review.

## 2. Choose translation direction

The source language selects PL → EN or EN → PL. A direction change needs explicit acceptance and a matching source. Interface language does not control this direction. Check source identity before generating; do not use the same translation draft for an unrelated canonical result.

## 3. Generate candidate

For assistance, select OpenRouter or a separately hosted LM Studio endpoint and its exact model. Check readiness, expand the optional project translation dictionary if needed, and read the disclosure. The shared OpenRouter key serves ASR/correction/translation, but each operation has its own data and consent scope.

After explicit consent, Generate translation candidate sends source text, not audio, in this stage. OpenRouter may bill the request. A project dictionary supplies approved terms/conventions for the selected direction; it does not guarantee meaning or fluency. Missing consent highlights its checkbox. Success records the candidate in the queue and disables accidental duplicate generation for that state.

## 4. Continue to translation review

Open the generated candidate in [Translation review & export](translation-review.md). Read every source/target unit and correct meaning, omissions, additions, names and register. A successful API response is not semantic approval. Save work to return later. If you do not need a translation, you may stop after source export without calling an API.
