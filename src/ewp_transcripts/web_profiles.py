"""Portable, credential-free GUI preferences, workspace manifests and dictionary editions."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from urllib.parse import parse_qsl, urlsplit
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from ewp_transcripts.gui_library import GuiLibrary
from ewp_transcripts.web_workspaces import (
    _FIELD_NAMES,
    GuiWorkspaceController,
    GuiWorkspaceDocument,
)

PROFILE_LIMIT = 16 * 1024 * 1024


class GuiPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    locale: Literal["en", "pl"] = "en"
    theme: Literal["system", "light", "dark"] = "system"
    showEta: bool = False
    playbackSpeed: float = 1
    reviewLayout: Literal["one", "all"] = "one"
    translationLayout: Literal["few", "all"] = "few"
    dictionaryDirectory: str = Field(default="dictionaries", max_length=4096)

    @field_validator("playbackSpeed")
    @classmethod
    def supported_speed(cls, value: float) -> float:
        if not 0.25 <= value <= 4:
            raise ValueError("Unsupported playback speed")
        return value


class ProfileDictionary(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    source_path: str = Field(max_length=4096)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    payload: str = Field(max_length=PROFILE_LIMIT)
    hidden: bool = False


class GuiUserProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_version: Literal[1] = 1
    name: str = Field(min_length=1, max_length=100)
    saved_at: datetime
    preferences: GuiPreferences
    fields: dict[str, str | bool | int] = Field(default_factory=dict)
    workspaces: tuple[GuiWorkspaceDocument, ...] = Field(default=(), max_length=50)
    dictionaries: tuple[ProfileDictionary, ...] = Field(default=(), max_length=200)
    palettes: dict[str, list[str]] = Field(default_factory=dict, max_length=50)


def _portable_fields(fields: dict[str, Any]) -> None:
    for key, value in fields.items():
        if key not in _FIELD_NAMES or type(value) not in (str, int, bool):
            raise ValueError("Profile contains unsupported workspace fields")
        if isinstance(value, str) and len(value) > 4096:
            raise ValueError("Profile workspace field is too long")
        if key in {"correction-endpoint", "translation-endpoint"} and isinstance(value, str):
            url = urlsplit(value)
            if (
                url.username
                or url.password
                or any(
                    name.lower() in {"key", "api_key", "apikey", "token", "secret", "access_token"}
                    for name, _ in parse_qsl(url.query)
                )
            ):
                raise ValueError("Profile API endpoints must not contain credentials")


def _portable_workspace(workspace: GuiWorkspaceDocument) -> None:
    """Validate structure now; normal workspace Load still validates every live path/hash."""
    UUID(workspace.workspace_id)
    if not 1 <= len(workspace.name) <= 100 or len(workspace.current_step) > 100:
        raise ValueError("Profile workspace identity is invalid")
    _portable_fields(workspace.fields)
    if len(workspace.staged_jobs) > 50 or len(workspace.terminal_jobs) > 50:
        raise ValueError("Profile workspace queue is too large")
    required = {
        "input_path",
        "output_directory",
        "planned_job_id",
        "planned_result_path",
        "source_sha256",
        "language",
        "speaker_count",
    }
    for job in workspace.staged_jobs:
        if set(job) not in (required, required | {"group_sources"}):
            raise ValueError("Profile workspace staged job is invalid")
        if any(
            not isinstance(job[key], str) or len(job[key]) > 4096
            for key in required - {"speaker_count"}
        ):
            raise ValueError("Profile workspace staged job is invalid")
        if job["language"] not in {"pl", "en", "auto"} or len(job["source_sha256"]) != 64:
            raise ValueError("Profile workspace staged job is invalid")
        count = job["speaker_count"]
        if count != "auto" and (type(count) is not int or not 1 <= count <= 32):
            raise ValueError("Profile workspace staged job is invalid")
        group = job.get("group_sources", {})
        if (
            not isinstance(group, dict)
            or len(group) > 6
            or any(
                not isinstance(path, str)
                or not isinstance(digest, str)
                or len(path) > 4096
                or len(digest) != 64
                for path, digest in group.items()
            )
        ):
            raise ValueError("Profile workspace grouped source is invalid")
    if any(
        job.status not in {"completed", "failed", "cancelled"} for job in workspace.terminal_jobs
    ):
        raise ValueError("Profiles cannot contain running queue jobs")


def _without_runtime(workspace: GuiWorkspaceDocument) -> GuiWorkspaceDocument:
    return workspace.model_copy(
        update={
            "fields": {
                key: False
                if key in {"correction-allow-remote", "translation-allow-remote"}
                else value
                for key, value in workspace.fields.items()
            },
            "terminal_jobs": tuple(
                job.model_copy(update={"error": None, "runtime_progress": None})
                for job in workspace.terminal_jobs
            ),
        }
    )


class GuiProfileController:
    def __init__(
        self, *, state_directory: Path, workspaces: GuiWorkspaceController, library: GuiLibrary
    ) -> None:
        self.directory = state_directory
        self.path = state_directory / "user-profile.json"
        self.workspaces, self.library = workspaces, library

    @staticmethod
    def validate(document: dict[str, Any]) -> GuiUserProfile:
        if len(json.dumps(document, ensure_ascii=False).encode()) > PROFILE_LIMIT:
            raise ValueError("User profile exceeds the 16 MiB limit")
        try:
            profile = GuiUserProfile.model_validate(document)
        except ValidationError:
            raise ValueError("User profile contains invalid or unsupported settings") from None
        if not profile.name.strip() or any(ord(char) < 32 for char in profile.name):
            raise ValueError("User profile name is invalid")
        _portable_fields(profile.fields)
        for workspace in profile.workspaces:
            _portable_workspace(workspace)
        for item in profile.dictionaries:
            _, digest = GuiLibrary.dictionary_identity(item.payload)
            if digest != item.sha256:
                raise ValueError("Profile dictionary hash does not match its contents")
        for name, colors in profile.palettes.items():
            if not name.strip() or len(name) > 80 or not 1 <= len(colors) <= 32:
                raise ValueError("Profile palette is invalid")
            if any(not re.fullmatch(r"#[0-9a-fA-F]{6}", color) for color in colors):
                raise ValueError("Profile palette is invalid")
        return profile.model_copy(
            update={
                "fields": {
                    key: False
                    if key in {"correction-allow-remote", "translation-allow-remote"}
                    else value
                    for key, value in profile.fields.items()
                },
                "workspaces": tuple(_without_runtime(item) for item in profile.workspaces),
            }
        )

    def capture(
        self,
        *,
        name: str,
        preferences: dict[str, Any],
        fields: dict[str, Any],
        workspaces: tuple[GuiWorkspaceDocument, ...],
        dictionary_paths: list[str],
    ) -> GuiUserProfile:
        dictionaries = []
        for path in dict.fromkeys(dictionary_paths):
            exported = self.library.export_dictionary(path)
            dictionaries.append(
                {
                    "source_path": path,
                    "payload": exported["payload"],
                    "sha256": exported["sha256"],
                    "hidden": self.library.hidden(path, exported["sha256"]),
                }
            )
        palettes = {
            item["id"]: item["colors"]
            for item in self.library.profiles()["profiles"]
            if item["custom"]
        }
        profile = self.validate(
            {
                "name": name.strip(),
                "saved_at": datetime.now(UTC).isoformat(),
                "preferences": preferences,
                "fields": fields,
                "workspaces": [item.model_dump(mode="json") for item in workspaces],
                "dictionaries": dictionaries,
                "palettes": palettes,
            }
        )
        profile = profile.model_copy(
            update={"workspaces": tuple(_without_runtime(item) for item in profile.workspaces)}
        )
        self._write(self.path, profile.model_dump(mode="json"))
        return profile

    def load(self) -> dict[str, Any]:
        if self.path.is_symlink() or not self.path.is_file():
            raise ValueError("No user profile has been saved on this computer")
        return self.restore(json.loads(self.path.read_text(encoding="utf-8")))

    def restore(self, document: dict[str, Any]) -> dict[str, Any]:
        profile = self.validate(document)
        palette_names: dict[str, str] = {}
        existing = {item["id"]: item for item in self.library.profiles()["profiles"]}
        for name, colors in profile.palettes.items():
            target = name
            suffix = hashlib.sha256(json.dumps(colors).encode()).hexdigest()[:8]
            counter = 0
            while target in existing and (
                not existing[target]["custom"] or existing[target]["colors"] != colors
            ):
                counter += 1
                target = f"{name[:60]}-{suffix}" + (f"-{counter}" if counter > 1 else "")
            self.library.validate_profile(name=target, colors=colors)
            palette_names[name] = target
            existing[target] = {"custom": True, "colors": colors}

        paths: dict[str, str] = {}
        # Content-addressed destination directories preserve all original dictionary bytes,
        # even if a different edition with the same ID already exists on this computer.
        for item in profile.dictionaries:
            root = self.directory / "profile-dictionaries" / item.sha256
            opened = self.library.import_dictionary(payload=item.payload, directory=str(root))
            paths[item.source_path] = opened["path"]
            self.library.visibility(
                path=opened["path"], digest=item.sha256, visible=not item.hidden
            )

        for original, target in palette_names.items():
            self.library.save_profile(name=target, colors=profile.palettes[original])

        def remap(fields: dict[str, str | bool | int]) -> dict[str, str | bool | int]:
            result = dict(fields)
            for key in ("correction-dictionary", "translation-dictionary", "dictionary-previous"):
                value = fields.get(key)
                if isinstance(value, str):
                    result[key] = paths.get(value, value)
            value = fields.get("gui-palette-profile")
            if isinstance(value, str):
                result["gui-palette-profile"] = palette_names.get(value, value)
            return result

        imported = []
        snapshots = [*profile.workspaces]
        if profile.fields:
            snapshots.append(
                GuiWorkspaceDocument(
                    workspace_id=str(uuid5(NAMESPACE_URL, "ewp-profile-current-fields")),
                    name=profile.name[:80] + " · settings",
                    saved_at=profile.saved_at,
                    current_step="workspace-heading",
                    fields=profile.fields,
                )
            )
        for workspace in snapshots:
            sanitized = _without_runtime(workspace)
            serialized = sanitized.model_dump(mode="json")
            identifier = str(
                uuid5(NAMESPACE_URL, json.dumps(serialized, sort_keys=True, ensure_ascii=False))
            )
            imported_workspace = sanitized.model_copy(
                update={"workspace_id": identifier, "fields": remap(sanitized.fields)}
            )
            destination = self.workspaces.state_directory / f"{identifier}.json"
            if destination.is_symlink():
                raise ValueError("Imported workspace destination cannot be a symlink")
            if destination.exists():
                if json.loads(destination.read_text()) != imported_workspace.model_dump(
                    mode="json"
                ):
                    raise ValueError("Imported workspace conflicts with an existing saved record")
            else:
                self._write(destination, imported_workspace.model_dump(mode="json"))
            imported.append(identifier)
        preferences = profile.preferences.model_dump()
        if profile.dictionaries:
            preferences["dictionaryDirectory"] = str(self.directory / "profile-dictionaries")
        restored = profile.model_copy(
            update={
                "preferences": GuiPreferences.model_validate(preferences),
            }
        )
        self._write(self.path, restored.model_dump(mode="json"))
        return {
            "profile": restored.model_dump(mode="json"),
            "imported_workspaces": len(imported),
            "imported_dictionaries": len(paths),
        }

    @staticmethod
    def _write(path: Path, document: dict[str, Any]) -> None:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if path.is_symlink():
            raise ValueError("Profile destination cannot be a symlink")
        descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=".profile-")
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(document, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
