# Interpreting the reported local speech-runtime messages

Reviewed against the locked WhisperX 3.8.6, Transformers 4.57.6 and ONNX Runtime 1.28.0 source.
The owner reported successful MP4 transcription. These messages alone do not establish a failed
job, nor do they qualify transcript quality or every GPU/runtime path.

## ONNX Runtime DRM discovery warning

The message about `/sys/class/drm/card0/device/vendor` is emitted by ONNX Runtime's Linux
hardware discovery. Its source logs a warning when reading a DRM device fails and continues
probing/fallback. It is not a PyTorch CUDA availability check. In the reported successful run,
this warning did not stop transcription. If a job actually fails, use Settings & About → Test
local dependencies and retain the queue's failure code; do not infer CUDA failure from this line
or suppress all runtime warnings.

Source: [ONNX Runtime 1.28.0 Linux device discovery](https://github.com/microsoft/onnxruntime/blob/v1.28.0/onnxruntime/core/platform/linux/device_discovery.cc).

## WhisperX voice activity detection INFO

The Performing voice activity detection using Pyannote line is an informational stage message.
Separate source/channel processing can invoke VAD more than once. The line itself is not an
exception or request to repair dependencies. New queue phase/elapsed/progress feedback makes
ongoing processing visible without relying on terminal log interpretation.

## Wav2Vec2 masked_spec_embed initialization warning

The exact reported missing parameter is the embedding used for training-time masking.
Transformers creates it when configured mask probabilities are nonzero, but its inference path
uses random masking only while training (or if explicit mask indices are supplied). Its
from_pretrained loader puts the model in evaluation mode. WhisperX's selected Hugging Face
alignment loader uses that loader and does not pass training masks during alignment.

For this specific message in this inference workflow, the generic TRAIN recommendation does
not require the user to train the model or replace locked weights. This is a source-based
inference, not a measurement of transcription quality. Missing encoder/head weights, a traceback,
load failure or a queue error would be a different condition and must be investigated separately.
No model configuration, checkpoint bytes or warning filters were changed for this finding.

Sources: [WhisperX 3.8.6 alignment loader](https://github.com/m-bain/whisperX/blob/v3.8.6/whisperx/alignment.py),
[Transformers 4.57.6 Wav2Vec2 masking](https://github.com/huggingface/transformers/blob/v4.57.6/src/transformers/models/wav2vec2/modeling_wav2vec2.py),
[Transformers pretrained evaluation mode](https://github.com/huggingface/transformers/blob/v4.57.6/src/transformers/modeling_utils.py).

## A long single-speaker review is a separate interface issue

The old review preparation grouped solely by speaker changes in the default mode and ignored
its word limit. One long speaker could therefore appear as one large review section regardless
of codec. Review preparation now honors both the word and speaker-block limits. Existing draft
presentation is bounded without silently rewriting the saved file or changing canonical times;
explicit saving persists the server-owned projected structure while preserving edits.


## Native Windows audio ConnectionAbortedError / WinError 10053

The reported traceback ends in _stream_review_audio -> socket.sendall, so that particular request
was interrupted while the browser was receiving its playback preview. It is separate from ASR and
canonical/subtitle publication. Seeking, switching previews or closing a page can abandon such
requests; the traceback alone does not identify which browser/host component ended the connection.
The handler now catches ConnectionAbortedError along with reset/broken-pipe errors during headers
and audio writes and closes the audio file. General I/O failures are still reported; there is no
blanket suppression of OSError or backend/runtime warnings. Focused tests cover all three disconnect
classes and genuine I/O failure propagation. Native playback remains an owner qualification.

The separately reported SPEECH_ENGINE_ERROR at the cloud adapter's missing-key check means the
server session has no API key after a restart. Workspace loading deliberately does not restore it.
Enter a key or choose Use saved OpenRouter key explicitly; this is not a missing local model/library.
