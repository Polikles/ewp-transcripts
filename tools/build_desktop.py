"""Build the owned Windows desktop host using the pinned distribution toolchain."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_desktop(tools: Path, version: str) -> Path:
    pins = json.loads((ROOT / "installer/toolchain.json").read_text())
    environment = {
        **os.environ,
        "DOTNET_CLI_HOME": str(tools / "dotnet-home"),
        "NUGET_PACKAGES": str(tools / "nuget"),
        "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
        "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1",
        "DOTNET_GENERATE_ASPNET_CERTIFICATE": "false",
    }
    dotnet = str(tools / "dotnet/dotnet")
    project = ROOT / "desktop/windows/EwP.Desktop.csproj"
    properties = [
        f"-p:BaseIntermediateOutputPath={tools / 'desktop-obj'}/",
        f"-p:BaseOutputPath={tools / 'desktop-bin'}/",
        f"-p:RuntimeFrameworkVersion={pins['windows_runtime']}",
        f"-p:PathMap={ROOT}=/_/source%2C{tools}=/_/tools",
    ]
    subprocess.run(
        [dotnet, "restore", str(project), "--locked-mode", *properties], env=environment, check=True
    )
    output = tools / "desktop-publish"
    subprocess.run(
        [
            dotnet,
            "publish",
            str(project),
            "--no-restore",
            "-c",
            "Release",
            *properties,
            f"-p:Version={version}",
            "--output",
            str(output),
        ],
        env=environment,
        check=True,
    )
    package = tools / "nuget/microsoft.web.webview2/1.0.4370.26"
    license_file = next(
        p for p in package.iterdir() if p.is_file() and p.name.lower().startswith("license")
    )
    shutil.copyfile(license_file, tools / "webview2-LICENSE.txt")
    return output / "EwP.Transcripts.exe"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tools", type=Path, required=True)
    parser.add_argument("--version", default="0.25.0")
    args = parser.parse_args()
    print(build_desktop(args.tools.resolve(), args.version))
