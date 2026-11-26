# AMD acceleration (experimental)

AMD support is experimental and has not been tested on a physical AMD card. The first adapter
targets Windows x64 and the official CTranslate2 ROCm/HIP backend. Local ASR uses the same pinned
large-v2, optional large-v3 and large-v3-turbo snapshots as the NVIDIA path. Word alignment and
speaker diarization run on CPU using the existing pinned models/PyTorch. This can make those stages
slower than the NVIDIA profile. AMD ASR uses serial float16 decoding and ordinary Whisper segment/
no-speech handling; it does not use WhisperX's torch/CUDA VAD or implicit CPU ASR fallback.
HIP ASR runs in a private child process so its OpenMP/DLL runtime is isolated from the CPU torch
stages. The native application's owned process job also owns this worker. Doctor probes HIP and
the CPU speech libraries separately; transcript data travels only through the local worker pipe.

Implemented in **0.26.0**, product source `6c5fbcd463283187f99b262ae819012c56249347`.
See [native qualification evidence](checkpoints/2026-11-26-snap-amd-evidence.json) and
[EN](gui/windows-native.md) / [PL](gui/pl/windows-native.md) launch instructions.

## Implementation map

| Component | Responsibility |
| --- | --- |
| `installer/manager.py`, `installer/windows/WizardAmd.cs` | PCI display-adapter detection, profile inventory, preflight and blocking Install/Update acknowledgement |
| `scripts/setup-amd.py`, `scripts/setup-windows.ps1` | Verified dependency overlay after the ordinary locked environment setup |
| `src/ewp_transcripts/resources/amd-windows-runtime.json` | Exact upstream URLs, sizes, archive/wheel/DLL SHA-256 pins |
| `src/ewp_transcripts/config.py`, `application.py` | Hardware-profile default, explicit-config precedence, AMD ASR plus CPU stages |
| `src/ewp_transcripts/engines/amd.py`, `amd_runtime.py` | Private HIP ASR worker, offline pinned models, runtime identity/device checks |
| `src/ewp_transcripts/doctor.py` | Separate HIP and CPU diagnostics to avoid mixing DLL/OpenMP runtimes |
| `tests/unit/test_amd.py`, `test_amd_windows.py` | Adapter/failure/download guards and actual native DLL-import qualification without models |

## Installation and profile selection

Install/Update host checks query PCI display adapters, not processor architecture. An AMD processor
or the name AMD64 does not activate AMD support. An AMD display adapter also triggers the warning
on a mixed NVIDIA/AMD PC. Close the warning to stay at the computer-check page, or choose
**I understand, continue** to acknowledge it. A repeated render/disk refresh does not reopen the
same acknowledged warning; a new installer session or operation requires its acknowledgement.
The Polish dialog says **obsługa kart AMD jest eksperymentalna i nie została przetestowana**,
with **Rozumiem, kontynuuj**. Terminal installation uses the same backend acknowledgement:
`Install-EwP.ps1 -AcceptExperimentalAmd` (manager flag `--accept-amd-experimental`). This does
not grant model terms or cloud-upload consent.

Fresh AMD-only hosts select the AMD runtime profile; fresh mixed hosts retain the NVIDIA profile.
An existing AMD profile is retained while its adapter remains available. The managed state stores
the hardware profile and acknowledgement; launch passes `EWP_LOCAL_ACCELERATOR=amd` to configuration.
Explicit TOML/CLI model configuration still has higher precedence. Repair reapplies the selected
runtime overlay after the normal locked dependency sync. Adding models retains the installed profile.

Install an appropriate AMD graphics driver first. CTranslate2's published support describes RDNA2/
RDNA3; consult its compatibility page for the current limits. Detection establishes card/driver
visibility only; automatic doctor must establish that the installed HIP runtime sees a device and
supports float16. Unsupported devices/drivers fail diagnostics; a detection result or acknowledgement
does not prove inference, performance, model quality, or support for every Radeon/iGPU.

## Runtime identity and downloads

The separate overlay installs official CTranslate2 ROCm4.9.1 for CPython3.12 and AMD SDK7.2.0.dev0
core/libraries packages. The compressed download is about1.33GB; extracted libraries use about3.71GB.
It does not require the development/compiler SDK or a system HIP installer. These are application
dependencies, not model downloads. Base NVIDIA dependencies and all model revisions remain unchanged.
The downloaded wheels preserve their upstream license files; no new GPU driver is installed silently.

All archive sizes, SHA-256 values, the selected inner wheel and HIP DLL identity are pinned in
`src/ewp_transcripts/resources/amd-windows-runtime.json`. Setup verifies downloads before pip install;
normal ASR verifies the HIP build before loading a model. Repair is required for a missing/wrong
backend. A manual `uv sync` can replace the overlay with the base NVIDIA wheel; rerun the managed
repair or `scripts/setup-windows.ps1` with the AMD profile environment selected. Normal managed
launch uses the prepared environment without synchronizing it again.

Source-checkout users explicitly set `$env:EWP_LOCAL_ACCELERATOR='amd'` before setup and launch;
keep that selection for subsequent repair. Use `--no-sync` when invoking the prepared AMD
environment so uv does not replace the verified HIP overlay with the base NVIDIA wheel:

```powershell
$env:EWP_LOCAL_ACCELERATOR = 'amd'
powershell -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Install
uv run --locked --no-sync transcriber doctor --test-speech-runtime
uv run --locked --no-sync transcriber gui
```

Model preparation remains a separate deliberate step as described in the installation guide.
This adapter does not enable AMD on Ubuntu/WSL, Ryzen
NPUs, DirectML or arbitrary ROCm/PyTorch combinations. NVIDIA remains the unchanged default there.

## Qualification boundary

Unit tests cover engine selection, CPU stages, offline decode/timestamps, missing runtime/failure,
configuration precedence, PCI vendor detection and acknowledgement before filesystem mutation.
Native Windows checks exercise warning controls and real verified DLL imports without models.
Import success does not establish physical AMD GPU execution. No physical AMD card is available;
that inference/performance qualification remains explicitly unperformed. No paid API campaign is used.

Primary references checked2026-11-26:

- [CTranslate2 hardware support](https://opennmt.net/CTranslate2/hardware_support.html)
- [Official ROCm Windows build/runtime notes](https://opennmt.net/CTranslate2/building_rocm_windows.html)
- [CTranslate2 ROCm4.9.1 release](https://github.com/OpenNMT/CTranslate2/releases/tag/v4.9.1)
- [AMD's SDK7.2 distribution](https://repo.radeon.com/rocm/windows/rocm-rel-7.2/)
