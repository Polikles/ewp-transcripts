"""Fetch digest-pinned build tools into an explicitly chosen disposable directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def download(path: Path, item: dict[str, str], algorithm: str = "sha256") -> None:
    if (
        path.exists()
        and hashlib.file_digest(path.open("rb"), algorithm).hexdigest() == item[algorithm]
    ):
        return
    partial = path.with_name(path.name + ".part")
    with urllib.request.urlopen(item["url"], timeout=90) as source, partial.open("wb") as out:
        while chunk := source.read(1024 * 1024):
            out.write(chunk)
    with partial.open("rb") as source:
        if hashlib.file_digest(source, algorithm).hexdigest() != item[algorithm]:
            raise ValueError("Build-tool digest mismatch; nothing is executed")
    partial.replace(path)


def prepare(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    pins = json.loads((ROOT / "installer/toolchain.json").read_text())
    download(directory / "dotnet.tar.gz", pins["dotnet"], "sha512")
    if not (directory / "dotnet/dotnet").exists():
        with tarfile.open(directory / "dotnet.tar.gz") as archive:
            archive.extractall(directory / "dotnet", filter="data")
    for item in (pins["uv"]["windows"], pins["uv"]["ubuntu"]):
        download(directory / item["file"], item)
    for name, item in pins["licenses"].items():
        download(directory / name, item)
    print("Verified SDK/uv/license tools ready (no app/model installation).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    prepare(parser.parse_args().directory.resolve())
