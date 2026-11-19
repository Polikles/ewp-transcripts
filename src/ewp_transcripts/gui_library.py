"""Local dictionary editions and named color profiles, without changing past artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Callable
from pathlib import Path
from threading import RLock
from typing import Any

from ewp_transcripts.config import (
    EWP_BRAND_PROFILE,
    EWP_BRAND_PROFILE_ALIASES,
    EXAMPLE_YTT_PALETTE,
    SubtitlesConfig,
)
from ewp_transcripts.correction_dictionary import ProjectCorrectionDictionary
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.translation_dictionary import ProjectTranslationDictionary


class GuiLibrary:
    def __init__(
        self,
        *,
        state_directory: Path,
        resolve_path: Callable[..., Path],
        subtitles: SubtitlesConfig,
    ) -> None:
        self._state = state_directory / "library.json"
        self._resolve = resolve_path
        self._subtitles = subtitles
        self._lock = RLock()

    def _read(self) -> dict[str, Any]:
        if not self._state.exists():
            return {"hidden": [], "profiles": {}}
        document: dict[str, Any] = json.loads(self._state.read_text(encoding="utf-8"))
        return document

    def _write(self, document: dict[str, Any]) -> None:
        self._state.parent.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(dir=self._state.parent, prefix=".library-")
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(document, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self._state)
        finally:
            temporary.unlink(missing_ok=True)

    def hidden(self, path: str, digest: str) -> bool:
        with self._lock:
            return [path, digest] in self._read()["hidden"]

    def visibility(self, *, path: str, digest: str, visible: bool) -> dict[str, Any]:
        source = self._resolve(path)
        self.view(str(source))  # Only valid dictionary documents may be hidden.
        if sha256_file(source) != digest:
            raise ValueError("Dictionary changed; refresh the library before removing it")
        with self._lock:
            document = self._read()
            key = [str(source), digest]
            document["hidden"] = [item for item in document["hidden"] if item != key]
            if not visible:
                document["hidden"].append(key)
            self._write(document)
        return {"path": str(source), "visible": visible}

    def view(self, path: str) -> dict[str, Any]:
        source = self._resolve(path)
        payload = source.read_bytes()
        raw = json.loads(payload)
        if not isinstance(raw, dict):
            raise ValueError("Dictionary document must be a JSON object")
        kind = "translation" if "source_language" in raw else "correction"
        model = (
            ProjectTranslationDictionary if kind == "translation" else ProjectCorrectionDictionary
        )
        dictionary = model.model_validate_json(payload)
        return {
            "path": str(source),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "kind": kind,
            "document": dictionary.model_dump(mode="json"),
        }

    def edition(
        self, *, document: dict[str, Any], directory: str, previous_path: str, previous_sha256: str
    ) -> dict[str, Any]:
        """Publish a distinct validated ID with a manual-edit provenance manifest."""
        previous = self.view(previous_path) if previous_path else None
        if previous and previous["sha256"] != previous_sha256:
            raise ValueError("Dictionary changed; reopen it before saving a new version")
        kind = "translation" if "source_language" in document else "correction"
        if previous and kind != previous["kind"]:
            raise ValueError("An edited edition must keep the dictionary kind")
        if previous and document.get("dictionary_id") == previous["document"]["dictionary_id"]:
            raise ValueError(
                "Use a new dictionary ID for this version; existing editions are immutable"
            )
        if kind == "translation" and document.get("source_language") == document.get(
            "target_language"
        ):
            raise ValueError("Translation dictionary languages must differ")
        manifest = {
            "method": "manual-dictionary-edit",
            "previous_sha256": previous_sha256 or None,
            "document": document,
        }
        manifest_bytes = (
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        ).encode()
        manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
        edited = dict(document)
        if kind == "correction":
            edited["proposal_sha256"] = manifest_hash
        model = (
            ProjectTranslationDictionary if kind == "translation" else ProjectCorrectionDictionary
        )
        dictionary = model.model_validate_json(json.dumps(edited))
        root = self._resolve(directory, directory=True)
        root.mkdir(parents=True, exist_ok=True)
        output = root / f"{dictionary.dictionary_id}.json"
        # Serialize GUI writers and never replace published bytes, even after a race.
        with self._lock:
            if output.exists():
                raise ValueError("That dictionary ID already exists; choose a new version ID")
            provenance = root / ".edits"
            provenance.mkdir(exist_ok=True)
            manifest_path = provenance / f"{manifest_hash}.json"
            try:
                self._publish(manifest_path, manifest_bytes)
            except FileExistsError:
                if manifest_path.read_bytes() != manifest_bytes:
                    raise ValueError("Dictionary edit provenance conflict") from None
            self._publish(output, (dictionary.model_dump_json(indent=2) + "\n").encode())
        return self.view(str(output))

    @staticmethod
    def _publish(path: Path, payload: bytes) -> None:
        """Publish complete immutable bytes atomically; link never overwrites an edition."""
        descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=".edition-")
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.link(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def profiles(self) -> dict[str, Any]:
        with self._lock:
            custom = self._read()["profiles"]
        profiles: list[dict[str, Any]] = []
        used_ids = set(custom)
        used_names: set[str] = set()

        def configured(name: str, identifier: str, colors: tuple[str, ...]) -> None:
            while identifier in used_ids:
                identifier = "configured:" + identifier
            used_ids.add(identifier)
            used_names.add(name)
            profiles.append(
                {"id": identifier, "name": name, "colors": list(colors), "custom": False}
            )

        # Stable configured/brand IDs preserve old workspaces; the example is independent
        # of explicitly configured production colors, which remain a separate choice.
        configured("Example default", "configured", EXAMPLE_YTT_PALETTE)
        if self._subtitles.ytt_speaker_palette != EXAMPLE_YTT_PALETTE:
            configured("Configured palette", "production", self._subtitles.ytt_speaker_palette)
        brand_key = next(
            (
                name
                for name in EWP_BRAND_PROFILE_ALIASES
                if name in self._subtitles.ytt_color_profiles
            ),
            None,
        )
        for name, colors in self._subtitles.ytt_color_profiles.items():
            configured(
                EWP_BRAND_PROFILE if name == brand_key else name,
                "brand" if name == brand_key else name,
                colors,
            )
        for name, colors in custom.items():
            profiles.append(
                {
                    "id": name,
                    "name": f"{name} (saved)" if name in used_names else name,
                    "colors": colors,
                    "custom": True,
                }
            )
        return {"profiles": profiles}

    def save_profile(self, *, name: str, colors: list[str]) -> dict[str, Any]:
        name = name.strip()
        if not name or len(name) > 80 or any(ord(char) < 32 for char in name):
            raise ValueError("Profile name must contain 1–80 printable characters")
        if name in {
            "Example default",
            "Configured palette",
            "Configured production",
            *EWP_BRAND_PROFILE_ALIASES,
            "configured",
            "brand",
            *self._subtitles.ytt_color_profiles,
        }:
            raise ValueError("Use a custom name to preserve configured profiles")
        if name in {
            profile["id"] for profile in self.profiles()["profiles"] if not profile["custom"]
        }:
            raise ValueError("Use a custom name to preserve configured profiles")
        if not 1 <= len(colors) <= 32 or not all(
            re.fullmatch(r"#[0-9a-fA-F]{6}", color) for color in colors
        ):
            raise ValueError("A profile needs 1–32 colors in #RRGGBB format")
        with self._lock:
            document = self._read()
            document["profiles"][name] = [color.upper() for color in colors]
            self._write(document)
        return self.profiles()
