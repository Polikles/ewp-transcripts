"""Explicit cross-platform preparation of configured immutable model snapshots."""

from __future__ import annotations

import argparse
import getpass
import os
import subprocess
import sys
import tempfile
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
    args = parser.parse_args()
    if not args.yes and input("Download pinned models/language data? [y/N] ").lower() != "y":
        raise SystemExit("Cancelled")
    from huggingface_hub import snapshot_download

    prepare_language_data()

    config = load_config()
    models = config.models
    entries = [
        (models.asr_repository, models.asr_revision, models.asr_snapshot_path),
        (models.alignment_model, models.alignment_revision, models.alignment_snapshot_path),
        (
            models.english_alignment_model,
            models.english_alignment_revision,
            models.english_alignment_snapshot_path,
        ),
    ]
    if not args.public_only:
        entries.append(
            (
                config.diarization.model,
                config.diarization.model_revision,
                config.diarization.local_model_path,
            )
        )
    for repository, revision, target in entries:
        token = os.environ.get("HF_TOKEN")
        if repository == config.diarization.model and not token:
            token = getpass.getpass("Hugging Face read token (accept model terms first): ")
            if not token:
                raise SystemExit("A read token is required for the gated model")
        snapshot_download(repo_id=repository, revision=revision, local_dir=target, token=token)
    print("Pinned model preparation complete. Run transcriber doctor.")


if __name__ == "__main__":
    main()
