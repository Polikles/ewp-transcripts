# Installer payload size review — 2026-11-26

The0.26.0 growth comes from adding the self-contained native desktop application, not bundled
models or ML wheels. Source distributions contain app/scripts, reviewed web assets/fonts/help,
lock/configuration, integrity inventory, notices, uv and the Windows desktop host. Dependencies
and selected models are already downloaded explicitly during installation.

| Delivery | EXE bytes | MiB | Windows bundle bytes |
| --- | ---: | ---: | ---: |
|0.24.4, before native desktop |157323320 |150.04 |16975693 |
|0.26.0, native desktop |216719416 |206.68 |76366433 |
|0.26.1 qualified internal delivery |142183758 |135.60 |76733622 |

The0.26.0 bundle's largest compressed members are desktop EXE59371920bytes, uv15226897bytes,
mono font733741bytes and Montserrat216013bytes. The whole unpacked bundle is177675372bytes;
the desktop executable accounts for141220088bytes. No venv/cache, audio/transcripts, model
snapshots or torch/ROCm wheels are embedded. The outer wizard also carries its own .NET runtime.

EnableCompressionInSingleFile on both self-contained Windows executables reduces the final
installer by34.39% against0.26.0. The desktop EXE alone drops to65419679bytes. Outer ZIP compression
already worked well, so its size barely changes; the main saving is the outer wizard's runtime.
No framework update, system .NET prerequisite, unsupported WPF trimming, deleted license or
removed application feature is required. Compression can add startup decompression work; actual
Windows startup/lifecycle qualification passed:47 installer groups,18 filesystem cases and six
desktop cycles in run45899926602. No physical GPU inference is implied.

## Smaller online installer boundary

A bootstrap carrying only the wizard could download an immutable, hash-pinned application bundle
from the selected public release. It would reduce the initial file further, while the total required
application/runtime download remains. It needs stable published assets, verified network/retry/error
handling before host diagnostics, and safe cache/recovery for update/repair/offline maintenance.
No guessed unpublished URL or short-lived Actions URL should be an installer download contract.
The current package remains self-contained for its UI/application; ordinary dependency/model setup
is already online. A new online bootstrap is a separate packaging change, not an untested removal
of the embedded bundle. Settle its delivery/storage design before public publication if selected.

Exact measured inventories and final qualification status are in
[installer-size evidence](checkpoints/2026-11-26-installer-size-evidence.json). Preserve all prior
installer bytes. Public executable artifacts require signing, with the procedure/keys outside Git.

Primary implementation reference:
[.NET single-file compression](https://learn.microsoft.com/en-us/dotnet/core/deploying/single-file/overview#compress-assemblies-in-single-file-apps).
