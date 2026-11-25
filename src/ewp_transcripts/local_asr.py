"""Pinned optional local ASR choices; metadata reads never download or load models."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any, cast

from ewp_transcripts.config import ApplicationConfig, ModelsConfig
from ewp_transcripts.domain.errors import ApplicationError


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
    choices = []
    for name in ["configured", "large-v3", "large-v3-turbo"]:
        candidate = config.model_copy(
            update={
                "speech": config.speech.model_copy(
                    update={"provider": "local", "local_model": name}
                )
            }
        )
        models = selected_models(candidate)
        choices.append(
            {"id": name, "name": models.asr_model, "installed": local_asr_available(models)}
        )
    return choices


class LocalAsrUnavailable(ApplicationError, ValueError):
    code = "GUI_LOCAL_ASR_MODEL_REQUIRED"

    def __init__(self) -> None:
        super().__init__(
            "The selected model is not installed. "
            "Install the model, restart the program and try again."
        )


def local_asr_available(models: ModelsConfig) -> bool:
    """Cheap offline snapshot checks, without hashes, model imports or network access."""
    target = models.asr_snapshot_path
    if target.name != models.asr_revision:
        return False
    sizes: dict[str, int | None] = {"model.bin": None, "config.json": None, "tokenizer.json": None}
    for entry in optional_asr_models():
        if (
            entry["repository"] == models.asr_repository
            and entry["revision"] == models.asr_revision
        ):
            sizes = entry["files"]
            break
    try:
        return all(
            (target / name).is_file()
            and (
                (target / name).stat().st_size == size
                if size is not None
                else (target / name).stat().st_size > 0
            )
            for name, size in sizes.items()
        )
    except OSError:
        return False


def require_local_asr(config: ApplicationConfig) -> None:
    if config.speech.provider == "local" and not local_asr_available(selected_models(config)):
        raise LocalAsrUnavailable()
