"""Explicit cross-platform preparation of configured immutable model snapshots."""

from __future__ import annotations

import argparse
import getpass
import importlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from ewp_transcripts.config import load_config


def prepare_language_data() -> None:
    """Keep NLTK's import guard active without treating the checkout's .venv as CWD code."""
    environment = dict(os.environ)
    if environment.get("NLTK_DATA"):
        # The child has a different cwd. Preserve caller-relative data search directories.
        environment["NLTK_DATA"] = os.pathsep.join(
            str(Path(path).expanduser().resolve())
            for path in environment["NLTK_DATA"].split(os.pathsep)
            if path
        )
    script = (
        "from nltk import download; "
        "raise SystemExit(0 if download('punkt_tab', quiet=True, raise_on_error=True) else 1)"
    )
    with tempfile.TemporaryDirectory(prefix="ewp-nltk-setup-") as directory:
        result = subprocess.run(
            [sys.executable, "-I", "-c", script],
            cwd=directory,
            env=environment,
            check=False,
        )
    if result.returncode:
        raise SystemExit("Language data setup failed; see the NLTK diagnostic above and retry.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-only", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument(
        "--model", action="append", choices=("asr", "alignment_pl", "alignment_en", "diarization")
    )
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--progress-json", action="store_true")
    args = parser.parse_args()
    if not args.yes and input("Download pinned models/language data? [y/N] ").lower() != "y":
        raise SystemExit("Cancelled")
    from huggingface_hub import snapshot_download
    from tqdm.auto import tqdm

    class DownloadProgress(tqdm):
        """Report only measured per-file bytes/rate; no fabricated total-install ETA."""

        def __init__(self, *values, **options):
            self.last_report = 0.0
            options.pop("name", None)  # HF groups byte streams using a named progress bar.
            if args.progress_json:
                options["disable"] = False
                options["file"] = io.StringIO()
            super().__init__(*values, **options)

        def update(self, amount=1):
            result = super().update(amount)
            now = time.monotonic()
            if (
                args.progress_json
                and self.unit == "B"
                and (now - self.last_report >= 0.5 or self.total and self.n >= self.total)
            ):
                self.last_report = now
                elapsed = max(0.001, time.time() - self.start_t)
                rate = max(0, self.n - self.initial) / elapsed
                print(
                    json.dumps(
                        {
                            "stage": "download",
                            "message": str(self.desc),
                            "bytes": self.n,
                            "total": self.total,
                            "unit": self.unit,
                            "rate": rate,
                            "eta_seconds": max(0, (self.total - self.n) / rate)
                            if self.total and rate
                            else None,
                        }
                    ),
                    flush=True,
                )
            return result

    if args.progress_json:
        # snapshot_download's tqdm_class covers file counts only. The pinned hub downloader's
        # byte-stream context resolves this module global for both HTTP and Xet transfers.
        hub_progress = importlib.import_module("huggingface_hub.utils.tqdm")
        hub_progress.tqdm = DownloadProgress

    prepare_language_data()

    config = load_config()
    models = config.models
    entries = [
        ("asr", models.asr_repository, models.asr_revision, models.asr_snapshot_path),
        (
            "alignment_pl",
            models.alignment_model,
            models.alignment_revision,
            models.alignment_snapshot_path,
        ),
        (
            "alignment_en",
            models.english_alignment_model,
            models.english_alignment_revision,
            models.english_alignment_snapshot_path,
        ),
    ]
    if not args.public_only:
        entries.append(
            (
                "diarization",
                config.diarization.model,
                config.diarization.model_revision,
                config.diarization.local_model_path,
            )
        )
    for code, repository, revision, target in entries:
        if args.model is not None and code not in args.model:
            continue
        token = os.environ.get("HF_TOKEN")
        if repository == config.diarization.model and not token:
            token = getpass.getpass("Hugging Face read token (accept model terms first): ")
            if not token:
                raise SystemExit("A read token is required for the gated model")
        snapshot_download(
            repo_id=repository,
            revision=revision,
            local_dir=target,
            token=token,
            force_download=args.force_download,
            tqdm_class=DownloadProgress,
        )
    print("Pinned model preparation complete.")


if __name__ == "__main__":
    main()
