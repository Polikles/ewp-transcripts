"Build deterministic, content-verified source/runtime bundles without models or private data."

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINS = json.loads((ROOT / "installer/toolchain.json").read_text())
UV_VERSION = PINS["uv"]["version"]
UV_HASHES = {
    target: (PINS["uv"][key]["file"], PINS["uv"][key]["sha256"])
    for target, key in (("windows-x64", "windows"), ("ubuntu-x64", "ubuntu"))
}


def build(output: Path, downloads: Path, *, allow_dirty: bool = False) -> list[Path]:
    text = (ROOT / "src/ewp_transcripts/_version.py").read_text()
    version = next(
        ast.literal_eval(n.value) for n in ast.parse(text).body if isinstance(n, ast.Assign)
    )
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
    if dirty and not allow_dirty:
        raise ValueError(
            "Commit reviewed sources first, or explicitly allow a disposable dirty test build"
        )
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")

    def source_bytes(name: str) -> bytes:
        # Git's clean checkout can still have platform-configured CRLF bytes. Final bundles
        # use the committed blob so one source SHA yields one source payload on every builder.
        if dirty:
            return (ROOT / name).read_bytes()
        return subprocess.check_output(["git", "show", f"{source}:{name}"], cwd=ROOT)

    output.mkdir(parents=True, exist_ok=True)
    sources: dict[str, bytes] = {}
    for directory in ("src", "scripts"):
        for name in sorted(n for n in tracked if n.startswith(directory + "/")):
            path = ROOT / name
            if (
                path.is_file()
                and not path.is_symlink()
                and "__pycache__" not in path.parts
                and path.suffix not in {".pyc", ".log"}
            ):
                sources["app/" + path.relative_to(ROOT).as_posix()] = source_bytes(name)
    for name in ("pyproject.toml", "uv.lock", "README.md", "LICENSE", "LICENSING.md"):
        sources["app/" + name] = source_bytes(name)
    for name in ("manager.py", "Install-EwP.ps1", "Install-EwP.sh", "Remove-EwP.ps1"):
        sources["control/" + name] = source_bytes("installer/" + name)
    artifacts = []
    for target, (archive_name, digest) in UV_HASHES.items():
        archive = downloads / archive_name
        if hashlib.sha256(archive.read_bytes()).hexdigest() != digest:
            raise ValueError("Pinned uv archive digest mismatch")
        if target == "windows-x64":
            with zipfile.ZipFile(archive) as zipped:
                name = next(n for n in zipped.namelist() if n.endswith("uv.exe"))
                binary = zipped.read(name)
        else:
            with tarfile.open(archive) as tar:
                member = next(m for m in tar.getmembers() if m.name.endswith("/uv"))
                stream = tar.extractfile(member)
                assert stream
                binary = stream.read()
        files = {**sources, "tools/" + ("uv.exe" if target == "windows-x64" else "uv"): binary}
        for name in ("LICENSE-MIT", "LICENSE-APACHE"):
            license_path = downloads / name
            if not license_path.exists():
                raise ValueError("Download uv upstream license notices before packaging")
            files["licenses/uv-" + name + ".txt"] = license_path.read_bytes()
        if target == "windows-x64":
            for name in (
                "dotnet-LICENSE.txt",
                "dotnet-THIRD-PARTY-NOTICES.txt",
                "windowsdesktop-LICENSE.txt",
            ):
                files["licenses/" + name] = (downloads / name).read_bytes()
        meta = {
            "format": 1,
            "version": version,
            "platform": target,
            "source_commit": source,
            "source_dirty": dirty,
            "uv_version": UV_VERSION,
            "sha256": {n: hashlib.sha256(data).hexdigest() for n, data in sorted(files.items())},
        }
        files["bundle.json"] = (json.dumps(meta, indent=2) + "\n").encode()
        artifact = output / f"EwP-{version}-{target}.zip"
        if artifact.exists():
            raise ValueError("Choose a fresh output directory; delivered artifacts are immutable")
        with zipfile.ZipFile(artifact, "x", compression=zipfile.ZIP_DEFLATED) as zipped:
            for name, data in sorted(files.items()):
                info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                zipped.writestr(info, data)
        artifacts.append(artifact)
    (output / "SHA256SUMS.txt").write_text(
        "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in artifacts)
    )
    return artifacts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--downloads", type=Path, required=True)
    parser.add_argument(
        "--allow-dirty", action="store_true", help="Disposable development builds only"
    )
    args = parser.parse_args()
    for artifact in build(args.output, args.downloads, allow_dirty=args.allow_dirty):
        print(artifact)
