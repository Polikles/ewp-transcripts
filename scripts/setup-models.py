"""Explicit cross-platform preparation of configured immutable model snapshots."""

from __future__ import annotations

import argparse
import getpass
import os

from ewp_transcripts.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-only", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    if not args.yes and input("Download pinned models/language data? [y/N] ").lower() != "y":
        raise SystemExit("Cancelled")
    from huggingface_hub import snapshot_download
    from nltk import download

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
    if not download("punkt_tab", quiet=True, raise_on_error=True):
        raise SystemExit("Language data setup failed")
    print("Pinned model preparation complete. Run transcriber doctor.")


if __name__ == "__main__":
    main()
