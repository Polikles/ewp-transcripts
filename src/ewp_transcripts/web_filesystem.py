"""Read-only allowed-root filesystem browsing for the local GUI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ewp_transcripts.discovery import normalize_input_path

_ALLOWED_EXTENSIONS = frozenset(
    {
        "json",
        "txt",
        "toml",
        "wav",
        "mp3",
        "flac",
        "m4a",
        "ogg",
        "opus",
        "mp4",
        "mkv",
        "mov",
        "webm",
        "avi",
        "m4v",
    }
)
_MAX_ENTRIES = 500
_TEMP_RUNTIME_DIRECTORY_NAMES = frozenset({".X11-unix", ".ICE-unix", ".XIM-unix", ".font-unix"})
_TEMP_RUNTIME_DIRECTORY_PREFIXES = ("systemd-private-",)


class GuiFilesystemEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    path: str
    kind: Literal["directory", "file"]


class GuiFilesystemListing(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    current_path: str | None
    parent_path: str | None
    roots: tuple[str, ...]
    entries: tuple[GuiFilesystemEntry, ...]
    truncated: bool


class GuiFilesystemController:
    """List bounded filesystem entries without crossing configured roots."""

    def __init__(self, allowed_roots: tuple[Path, ...]) -> None:
        self._roots = allowed_roots

    def list(
        self,
        raw_path: str,
        *,
        select: Literal["file", "directory"],
        extensions: tuple[str, ...] = (),
    ) -> GuiFilesystemListing:
        normalized_extensions = tuple(extension.casefold().lstrip(".") for extension in extensions)
        if len(normalized_extensions) > len(_ALLOWED_EXTENSIONS) or any(
            extension not in _ALLOWED_EXTENSIONS for extension in normalized_extensions
        ):
            raise ValueError("Filesystem browser extensions are invalid")
        if not raw_path.strip():
            return GuiFilesystemListing(
                current_path=None,
                parent_path=None,
                roots=tuple(str(root) for root in self._roots),
                entries=tuple(
                    GuiFilesystemEntry(name=str(root), path=str(root), kind="directory")
                    for root in self._roots
                ),
                truncated=False,
            )

        candidate = normalize_input_path(raw_path)
        if candidate.is_symlink():
            raise ValueError("Symbolic-link paths are not available in the filesystem browser")
        resolved = candidate.resolve(strict=True)
        if resolved.is_file():
            resolved = resolved.parent
        if not resolved.is_dir():
            raise ValueError("Filesystem browser path must resolve to a directory")
        containing_root = next(
            (root for root in self._roots if resolved == root or resolved.is_relative_to(root)),
            None,
        )
        if containing_root is None:
            raise ValueError("Path is outside the configured allowed roots")

        entries: list[GuiFilesystemEntry] = []
        for child in sorted(
            resolved.iterdir(),
            key=lambda item: (not item.is_dir(), item.name.casefold(), item.name),
        ):
            if child.is_symlink():
                continue
            try:
                if child.is_dir():
                    if resolved == Path("/tmp") and (
                        child.name in _TEMP_RUNTIME_DIRECTORY_NAMES
                        or child.name.startswith(_TEMP_RUNTIME_DIRECTORY_PREFIXES)
                    ):
                        continue
                    if not os.access(child, os.R_OK | os.X_OK):
                        continue
                    entries.append(
                        GuiFilesystemEntry(
                            name=child.name,
                            path=str(child.resolve(strict=True)),
                            kind="directory",
                        )
                    )
                elif (
                    select == "file"
                    and child.is_file()
                    and (
                        not normalized_extensions
                        or child.suffix.casefold().lstrip(".") in normalized_extensions
                    )
                ):
                    entries.append(
                        GuiFilesystemEntry(
                            name=child.name,
                            path=str(child.resolve(strict=True)),
                            kind="file",
                        )
                    )
            except OSError:
                continue

        parent = None if resolved == containing_root else str(resolved.parent)
        return GuiFilesystemListing(
            current_path=str(resolved),
            parent_path=parent,
            roots=tuple(str(root) for root in self._roots),
            entries=tuple(entries[:_MAX_ENTRIES]),
            truncated=len(entries) > _MAX_ENTRIES,
        )
