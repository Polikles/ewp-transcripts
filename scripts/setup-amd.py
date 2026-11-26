"""Install the separately pinned AMD HIP overlay into a managed Windows Python environment."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

PINS = (
    Path(__file__).resolve().parents[1] / "src/ewp_transcripts/resources/amd-windows-runtime.json"
)


def download(item: dict[str, Any], directory: Path) -> Path:
    target = directory / item["file"]
    digest = hashlib.sha256()
    started = last = time.monotonic()
    count = 0
    with urllib.request.urlopen(item["url"], timeout=60) as response, target.open("xb") as stream:
        while block := response.read(1024 * 1024):
            stream.write(block)
            digest.update(block)
            count += len(block)
            now = time.monotonic()
            if now - last >= 0.5 or count == item["size"]:
                rate = count / max(0.001, now - started)
                print(
                    json.dumps(
                        {
                            "stage": "download",
                            "message": item["file"],
                            "bytes": count,
                            "total": item["size"],
                            "unit": "B",
                            "rate": rate,
                            "eta_seconds": max(0, (item["size"] - count) / rate),
                        }
                    ),
                    flush=True,
                )
                last = now
    if count != item["size"] or digest.hexdigest() != item["sha256"]:
        raise ValueError("AMD runtime download does not match its pinned size/SHA-256")
    return target


def install(uv: str, python: str) -> None:
    if sys.platform != "win32":
        raise ValueError("The experimental AMD overlay currently supports Windows x64 only")
    pins = json.loads(PINS.read_text())
    with tempfile.TemporaryDirectory(prefix="ewp-amd-runtime-") as temporary:
        directory = Path(temporary)
        # Install one at a time to bound compressed temporary storage. uv verifies its own cache.
        for item in pins["packages"]:
            wheel = download(item, directory)
            subprocess.run(
                [uv, "pip", "install", "--python", python, "--no-deps", str(wheel)], check=True
            )
            wheel.unlink()
        item = pins["ctranslate2"]
        archive_path = download(item, directory)
        wheel = directory / Path(item["member"]).name
        with zipfile.ZipFile(archive_path) as archive:
            data = archive.read(item["member"])
            if hashlib.sha256(data).hexdigest() != item["wheel_sha256"]:
                raise ValueError("AMD CTranslate2 wheel SHA-256 mismatch")
            wheel.write_bytes(data)
        subprocess.run(
            [uv, "pip", "install", "--python", python, "--no-deps", "--reinstall", str(wheel)],
            check=True,
        )
    print(
        json.dumps(
            {
                "stage": "dependencies",
                "message": (
                    "AMD ROCm runtime installed (experimental); alignment and diarization use CPU"
                ),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uv", default="uv")
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    install(args.uv, args.python)
