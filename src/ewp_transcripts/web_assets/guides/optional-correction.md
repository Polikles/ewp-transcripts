# Optional correction

Use the numbered steps below with the matching GUI stage.

1. Choose recording: Open a completed recording from the queue. Batch checkboxes select independent recordings for batch actions.
2. Choose provider and dictionary: For assistance, choose the exact provider, model and optional dictionary. Check readiness and read the disclosure.
3. Generate correction candidate: Give scoped consent and Generate correction candidate. Suggestions remain non-final.
4. Continue to source review: Open the candidate in manual review, or Skip LLM-assisted correction to review the original ASR text.

## 1. Choose recording

Choose an ASR-completed recording. Batch checkboxes select separate recordings for a batch action; clicking a recording opens its own editor. Assistance is optional. Skip LLM-assisted correction uses raw ASR for human review. Entering manual source review directly also records that assistance was skipped, so the next-step indicator does not remain stuck at correction.

## 2. Choose provider and dictionary

Select OpenRouter with the shared key, or a separately running LM Studio server with the exact endpoint/model. LM Studio installation and model hosting are outside this application's installer; a compatible response does not establish model quality. Local models tested so far still require thorough review.

Use the readiness check before generation. It does not send the transcript. A remote endpoint is a separate disclosure choice. Select an optional project correction dictionary by exact edition; expand its controls only when needed. Correction dictionaries repair source-language terminology, not translation direction.

## 3. Generate correction candidate

Read and tick the disclosure checkbox for the current source/provider. Generate correction candidate sends the selected transcript text and approved dictionary context. OpenRouter calls can incur charges; it receives text, not source audio in this stage. The shared ASR key is managed in [Settings](settings.md).

A candidate is non-final. Check names, quotations, punctuation, repeated words and self-corrections. Assistance must not rewrite a speaker's meaning or turn speech into polished prose. A generation error does not grant permission for an unrelated or automatic paid retry. Technical details retain diagnostic codes.

## 4. Continue to source review

Open the candidate in [Source review & export](source-review.md), or skip assistance and review ASR directly. Human review, draft validation, manual verification and verified export are still required. The canonical ASR result remains unchanged. Save a work checkpoint if continuing later.
