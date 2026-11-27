# Hardware and locked-library compatibility

Fully local transcription is recommended with a compatible **NVIDIA GPU and 12 GB VRAM or more**,
32 GB system RAM, a multicore x64 CPU and SSD. 12 GB is approximate capacity guidance, not a proven
minimum or guarantee for every card/model. Smaller compatible configurations may work, but have
not been tested and are not guaranteed; **cloud ASR is recommended below 12 GB VRAM**. The reference
actually tested by the owner remains RTX 3090/24 GB. No lower-VRAM test campaign is scheduled.

## Exact current NVIDIA stack

| Component / policy | Current contract |
| --- | --- |
| Python / torch / audio | CPython 3.12; torch/torchaudio 2.8.0 from the cu128 index; TorchCodec 0.7.0 |
| ASR / CUDA / cuDNN | WhisperX 3.8.6, CTranslate2 NVIDIA 4.8.1; CUDA runtime 12.8.90 (12.8 Update 1 family), cuDNN 9.10.2.21 |
| Architecture intersection | PyTorch cu128 excludes Maxwell/Pascal; CTranslate2 float16 needs Compute Capability 7.0+. Volta is the lower architectural boundary; common GeForce starts at Turing (RTX20xx/GTX 16xx), then Ampere/Ada/Hopper/Blackwell as supported by the pinned binaries. |
| Project driver floor | Windows/WSL host driver 572.61; native Linux 570.124.06. This deliberately uses the matching full CUDA 12.8 Update 1 driver baseline; it is not a claim that every older driver fails NVIDIA's limited minor-version compatibility mode. |
| Known preflight CC values |7.0,7.5,8.0,8.6,8.9,9.0,10.0,12.0. Unrecognized future/unknown metadata is unverified, not automatically certified by a numerical comparison. |
| Toolkit installation | No separate system CUDA Toolkit is required; locked packages supply runtime libraries. Install/update the appropriate GPU driver separately. nvidia-smi's CUDA banner describes maximum driver compatibility, not an installed toolkit or an inference test. |

The floor comes from the intersection of actual locked libraries, not CUDA's general GPU list:
CUDA 12.x itself can support older cards while this PyTorch/float16 pipeline does not. GTX10xx/Pascal,
Maxwell and older architectures cannot use the current local NVIDIA pipeline. A newer driver does
not restore missing kernels. No Pascal/GTX 1070 adapter, old-runtime profile or telemetry test is planned.

Primary evidence, checked 2026-11-27:

- [PyTorch2.8 cu128 architecture policy](https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128)
- [Pinned CTranslate2 4.8.1 Windows build: CUDA 12.8.1/cuDNN 9.10](https://github.com/OpenNMT/CTranslate2/blob/v4.8.1/python/tools/prepare_build_environment_windows.sh)
- [CTranslate2 float16 capabilities](https://github.com/OpenNMT/CTranslate2/blob/v4.8.1/docs/quantization.md)
- [CUDA 12.8 Update 1 driver table](https://docs.nvidia.com/cuda/archive/12.8.1/cuda-toolkit-release-notes/)
- [NVIDIA architecture/compute matrix](https://docs.nvidia.com/datacenter/tesla/drivers/latest/cuda-toolkit-driver-and-architecture-matrix.html)

## Installer behavior

Host checks use driver metadata without loading ML/models: GPU identity, driver, compute capability
and total dedicated VRAM. Unsupported architecture/old driver/unverified selection gets actionable
cloud guidance; new local-model preparation is unavailable until compatibility is established.
An ordinary app-only update/repair or cloud-only install remains available. A compatible card below
12 GB gets an explicit probably-will-not-work/untested/no-guarantee warning and cloud recommendation;
a deliberate local choice remains possible. Unknown VRAM is never converted into an invented success.
Automatic post-install doctor remains the actual runtime check; preflight does not qualify inference.

VRAM from separate GPUs is never added. The check uses an explicit CUDA_VISIBLE_DEVICES selection
(index/UUID), an unambiguous single GPU or explicit PCI_BUS_ID order; otherwise a mixed multi-NVIDIA
selection remains unverified. It does not silently change GPU selection. 12 GB guidance uses decimal
bytes and permits nominal 12 GiB cards with small driver-reserved memory; it is a recommendation,
not a memory-allocation guarantee. Total capacity is separate from current free memory.

AMD Windows follows its separate [experimental adapter scope](AMD_EXPERIMENTAL.md), with GPU ASR
and CPU alignment/diarization. AMD processors alone do not select it; physical AMD inference remains
untested. Fresh supported mixed hosts retain the NVIDIA profile, existing AMD profile is preserved.

## Other resources and modes

Fresh installation needs 25 GB on the target volume, plus additional models, media and outputs;
model cache may be on another volume. Cloud ASR and existing-result review do not require a local
NVIDIA GPU. Cloud operations still need a key/network and exact explicit upload/text consent.
Owner accepts the compressed 142 MB self-contained installer; no further slimming or downloader is
planned. Artist work is non-blocking. Signing/release planning follows the documentation audit;
no physical-GPU/provider tests or public release are implied by these recommendations.
