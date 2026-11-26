# Hardware recommendations and qualification

The local speech pipeline needs a compatible GPU architecture as well as sufficient VRAM.
These are current practical recommendations, not a promise that every matching machine has been
tested. Windows AMD has its own [experimental scope](AMD_EXPERIMENTAL.md).

| Use | Guidance and evidence |
| --- | --- |
| Tested NVIDIA reference | RTX 3090 with 24 GB VRAM; owner-tested local ASR/workflow on Windows11x64 and WSL. |
| Recommended local starting point | A recent NVIDIA RTX GPU with 12 GB VRAM or more,32 GB system RAM, a multicore x64 CPU and SSD storage. Capacity recommendation only; each card/runtime/model combination still needs compatibility checks. |
| Possible lower VRAM floor | 8 GB is an unvalidated test target, not an established supported minimum. Model, batch, duration/stages and competing GPU applications affect headroom. |
| Disk | At least25 GB on the fresh-install target volume; optional models, recordings, results and retained versions need additional space. Model cache may use another volume. |
| Cloud ASR / existing-result review | A local NVIDIA GPU is not required for these modes. Cloud audio/text operations require the appropriate connection, key and explicit consent. |
| AMD Windows | Experimental GPU ASR; CPU alignment/diarization. No physical-card inference/performance qualification. |

## Older NVIDIA cards and the planned GTX 1070 test

The current lock uses PyTorch 2.8.0 CUDA 12.8 binaries. PyTorch removed Pascal/Maxwell GPU support
from that binary variant. GTX 1070 is Pascal;8 GB on this card therefore cannot by itself qualify the
current pipeline. A recent driver does not add missing kernels to a package. Future tests must
first establish a compatible runtime/profile and actual execution of every GPU stage. This may
require a separately pinned legacy profile; no dependency replacement is implemented or promised
here. Keep the working reference profile unchanged.

Primary source: [PyTorch 2.8 architecture policy](https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128).

Owner expects access later to GTX 1070/8 GB,32 GB RAM,Intel Core i5-10400F. No such machine is currently
available. TODO queues the compatibility-first qualification and possible measurement scripts:
OS/CPU/GPU/driver/compute capability, torch compiled architecture list and a real CUDA operation,
CTranslate2 supported compute types, model revisions/batch/compute settings, duration and per-stage
wall time, sampled whole-GPU VRAM peak and baseline, process RAM/CPU/utilization/temperature/power
where exposed. Sampling must distinguish total device use from application allocation; under WDDM,
per-process nvidia-smi VRAM may be unavailable. Short spikes between samples are not a true measured
maximum. No audio/transcripts, secrets or unrelated process command lines belong in reports.

Begin with the shipped default model, then selected optional models; exercise alignment/diarization,
repeated jobs and cleanup. Retain cancellation/restart/OOM behavior and evidence, not a load-only
claim. Compare observed memory headroom and elapsed time with the RTX 3090 reference on matched
material/settings. This is later owner hardware work, not a new public-release gate or authorization
for paid/corpus benchmarks. Update the8 GB recommendation only after evidence exists.
