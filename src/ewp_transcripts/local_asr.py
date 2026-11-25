"""Pinned optional local ASR choices; metadata reads never download or load models."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any, cast

from ewp_transcripts.config import ApplicationConfig, ModelsConfig


def optional_asr_models() -> list[dict[str, Any]]:
    return cast(
        list[dict[str, Any]],
        json.loads(
            files("ewp_transcripts.resources").joinpath("local-asr-models.json").read_text()
        ),
    )


def selected_models(config: ApplicationConfig) -> ModelsConfig:
    if config.speech.provider != "local" or config.speech.local_model == "configured":
        return config.models
    entry = next(m for m in optional_asr_models() if m["name"] == config.speech.local_model)
    return config.models.model_copy(
        update={
            "asr_model": entry["name"],
            "asr_repository": entry["repository"],
            "asr_revision": entry["revision"],
            "asr_snapshot_path": Path(entry["path"]).expanduser(),
        }
    )


def resolve_local_asr(config: ApplicationConfig) -> ApplicationConfig:
    return config.model_copy(update={"models": selected_models(config)})


def local_model_options(config: ApplicationConfig) -> list[dict[str, Any]]:
    choices: list[dict[str, Any]] = [
        {
            "id": "configured",
            "name": config.models.asr_model,
            "path": config.models.asr_snapshot_path,
        }
    ]
    choices.extend(
        {"id": m["name"], "name": m["name"], "path": Path(m["path"]).expanduser()}
        for m in optional_asr_models()
    )
    return [
        {"id": m["id"], "name": m["name"], "installed": (m["path"] / "model.bin").is_file()}
        for m in choices
    ]
