"""Build terminal bundles and self-contained Windows wizard without publishing a release."""

from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

from build_distribution import ROOT, build


def build_setup(tools: Path, output: Path, *, allow_dirty: bool = False) -> None:
    if output.exists():
        raise ValueError("Use a new output directory; previous artifacts stay immutable")
    pins = json.loads((ROOT / "installer/toolchain.json").read_text())
    version = next(
        ast.literal_eval(n.value)
        for n in ast.parse((ROOT / "src/ewp_transcripts/_version.py").read_text()).body
        if isinstance(n, ast.Assign)
    )
    environment = {
        **os.environ,
        "DOTNET_CLI_HOME": str(tools / "dotnet-home"),
        "NUGET_PACKAGES": str(tools / "nuget"),
        "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
        "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1",
        "DOTNET_GENERATE_ASPNET_CERTIFICATE": "false",
    }
    dotnet = str(tools / "dotnet/dotnet")
    assert (
        subprocess.check_output([dotnet, "--version"], env=environment, text=True).strip()
        == pins["dotnet"]["version"]
    )
    project = str(ROOT / "installer/windows/EwP.Setup.csproj")
    properties = [
        f"-p:BaseIntermediateOutputPath={tools / 'obj'}/",
        f"-p:BaseOutputPath={tools / 'bin'}/",
        f"-p:RuntimeFrameworkVersion={pins['windows_runtime']}",
    ]
    subprocess.run([dotnet, "restore", project, *properties], env=environment, check=True)
    # Redistribution notices are embedded in the same bundle carried by the EXE.
    for source, name in [
        (tools / "dotnet/LICENSE.txt", "dotnet-LICENSE.txt"),
        (tools / "dotnet/ThirdPartyNotices.txt", "dotnet-THIRD-PARTY-NOTICES.txt"),
        (
            tools
            / "nuget/microsoft.windowsdesktop.app.runtime.win-x64"
            / pins["windows_runtime"]
            / "LICENSE",
            "windowsdesktop-LICENSE.txt",
        ),
    ]:
        shutil.copyfile(source, tools / name)
    artifacts = build(output, tools, allow_dirty=allow_dirty)
    windows = next(p for p in artifacts if "windows" in p.name)
    publish = tools / ("publish-" + output.name)
    subprocess.run(
        [
            dotnet,
            "publish",
            project,
            "--no-restore",
            "-c",
            "Release",
            *properties,
            f"-p:Version={version}",
            f"-p:BundlePath={windows}",
            "--output",
            str(publish),
        ],
        env=environment,
        check=True,
    )
    wizard = output / f"EwP-Setup-{version}.exe"
    shutil.copyfile(publish / "EwP-Setup.exe", wizard)
    artifacts.append(wizard)
    ubuntu_zip = next(p for p in artifacts if p.name.endswith("ubuntu-x64.zip"))
    ubuntu_tar = output / f"EwP-{version}-ubuntu-x64.tar.gz"
    # tar needs no unzip/Python on a fresh Ubuntu host. Only the bootstrap files are duplicated.
    import zipfile

    with (
        zipfile.ZipFile(ubuntu_zip) as archive,
        ubuntu_tar.open("wb") as target,
        gzip.GzipFile(filename="", mode="wb", fileobj=target, mtime=0) as compressed,
        tarfile.open(fileobj=compressed, mode="w") as tar,
    ):
        names = [n for n in archive.namelist() if n.startswith(("control/", "tools/", "licenses/"))]
        for name in names:
            data = archive.read(name)
            member = tarfile.TarInfo(name)
            member.size = len(data)
            member.mode = 0o700 if name.endswith(("/uv", ".sh")) else 0o600
            tar.addfile(member, io.BytesIO(data))
        data = ubuntu_zip.read_bytes()
        member = tarfile.TarInfo("bundle.zip")
        member.size = len(data)
        tar.addfile(member, io.BytesIO(data))
    artifacts.append(ubuntu_tar)
    windows_sha = hashlib.sha256(windows.read_bytes()).hexdigest()
    ubuntu_sha = hashlib.sha256(ubuntu_tar.read_bytes()).hexdigest()
    for extension in ("ps1", "sh"):
        template = (ROOT / f"installer/bootstrap.{extension}.in").read_text()
        entry = output / f"Install-EwP-{version}.{extension}"
        entry.write_text(
            template.replace("@VERSION@", version)
            .replace("@WINDOWS_SHA@", windows_sha)
            .replace("@UBUNTU_SHA@", ubuntu_sha)
        )
        artifacts.append(entry)
    (output / "SHA256SUMS.txt").write_text(
        "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in artifacts)
    )
    instructions = [
        "EwP Transcripts installer test package / Paczka testowa instalatora",
        f"Version / Wersja: {version}",
        "",
        "Windows: run the EXE / uruchom EXE.",
        "This test build is unsigned / Ta wersja testowa nie jest podpisana.",
        "Terminal: extract the ZIP or tar.gz and follow docs/gui/installation.md.",
        "Terminal: rozpakuj ZIP lub tar.gz i wykonaj docs/gui/pl/installation.md.",
        "Online bootstrap scripts require publication of the matching GitHub release first.",
        "Skrypty pobierania online wymagają wcześniejszej publikacji pasującego wydania GitHub.",
        "No models or private media are bundled. Installing deps/models needs network access.",
        "Paczka nie zawiera modeli ani prywatnych mediów; ich instalacja wymaga internetu.",
        "Publication, native Win11 acceptance and code-signing are separate from build success.",
    ]
    (output / "README.txt").write_text("\n".join(instructions) + "\n")
    print("Ready:", output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tools", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()
    build_setup(args.tools.resolve(), args.output.resolve(), allow_dirty=args.allow_dirty)
