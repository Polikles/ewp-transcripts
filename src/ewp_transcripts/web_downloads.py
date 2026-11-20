"""Hash-bound downloads of published, manually reviewed exports, including older versions."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ewp_transcripts.config import ApplicationConfig
from ewp_transcripts.domain.canonical import load_canonical_result
from ewp_transcripts.domain.errors import ApplicationError
from ewp_transcripts.domain.revision import load_transcript_revision, validate_revision_base
from ewp_transcripts.domain.translation import load_transcript_translation
from ewp_transcripts.export_service import verified_existing_revision_exports
from ewp_transcripts.translation_export import TranslationExportFormat, render_translation_exports

LIMIT = 64 * 1024 * 1024


class DownloadRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    path: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size: int = Field(ge=0, le=LIMIT)
    context: dict[str, str]

    @field_validator("context")
    @classmethod
    def validate_context(cls, value: dict[str, str]) -> dict[str, str]:
        pairs = {"result"}
        if "revision" in value:
            pairs.add("revision")
        if "translation" in value:
            pairs.add("translation")
        keys = pairs | {f"{key}_sha256" for key in pairs}
        if set(value) != keys or any(
            not Path(value[key]).is_absolute()
            or not re.fullmatch(r"[a-f0-9]{64}", value[f"{key}_sha256"])
            for key in pairs
        ):
            raise ValueError("Export download context is invalid")
        return value


class GuiExportDownloads:
    def __init__(
        self, *, config: ApplicationConfig, resolve_path: Callable[..., Path], registry: Path
    ) -> None:
        self._config = config
        self._resolve = resolve_path
        self._registry = registry
        self._lock = threading.RLock()
        self._tokens: dict[str, tuple[float, DownloadRecord]] = {}

    def _path(self, raw: str, *, directory: bool = False) -> Path:
        candidate = Path(raw).expanduser().absolute()
        if any(path.is_symlink() for path in (candidate, *candidate.parents)):
            raise ValueError("Symbolic-link export paths are not allowed")
        return self._resolve(raw, directory=directory)

    def _bytes(self, raw: str) -> bytes:
        path = self._path(raw)
        descriptor = os.open(
            path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        )
        with os.fdopen(descriptor, "rb") as handle:
            metadata = os.fstat(handle.fileno())
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > LIMIT:
                raise ValueError("Export file is not a bounded regular file")
            payload = handle.read(LIMIT + 1)
            if len(payload) > LIMIT:
                raise ValueError("Export file is too large")
            return payload

    def _context(self, result: str, revision: str, translation: str = "") -> dict[str, str]:
        result_path = self._path(result)
        self._bytes(str(result_path))
        canonical = load_canonical_result(result_path)
        context = {
            "result": str(result_path),
            "result_sha256": hashlib.sha256(self._bytes(str(result_path))).hexdigest(),
        }
        if revision:
            revision_path = self._path(revision)
            self._bytes(str(revision_path))
            document = load_transcript_revision(revision_path)
            validate_revision_base(document, canonical, base_sha256=context["result_sha256"])
            if document.provenance.method != "manual":
                raise ValueError("Only manually verified revision exports can be downloaded")
            context.update(
                revision=str(revision_path),
                revision_sha256=hashlib.sha256(self._bytes(str(revision_path))).hexdigest(),
            )
        elif not translation:
            raise ValueError("Choose an applied manual revision before downloading exports")
        if translation:
            translation_path = self._path(translation)
            self._bytes(str(translation_path))
            document_translation = load_transcript_translation(translation_path)
            source = document_translation.source
            if (
                source.canonical_result.job_id != canonical.job_id
                or source.canonical_result.result_version != canonical.result_version
                or source.canonical_result.schema_version != canonical.schema_version
                or source.canonical_result.filename != result_path.name
                or document_translation.provenance.method != "manual"
                or source.canonical_result.sha256 != context["result_sha256"]
            ):
                raise ValueError("Choose a verified manual translation of this canonical result")
            if (
                source.transcript_revision is not None
                and source.transcript_revision.sha256 != context.get("revision_sha256")
            ):
                raise ValueError("Translation revision identity differs from the selected revision")
            if source.transcript_revision is None and revision:
                raise ValueError("Translation revision identity differs from the selected revision")
            context.update(
                translation=str(translation_path),
                translation_sha256=hashlib.sha256(self._bytes(str(translation_path))).hexdigest(),
            )
        return context

    def _records(self) -> list[DownloadRecord]:
        if not self._registry.exists():
            return []
        document = json.loads(self._bytes(str(self._registry)))
        if (
            not isinstance(document, dict)
            or document.get("schema_version") != "1.0"
            or not isinstance(document.get("exports"), list)
            or len(document["exports"]) > 10000
        ):
            raise ValueError("Export download registry is invalid")
        return [DownloadRecord.model_validate(item) for item in document["exports"]]

    def _save(self, records: list[DownloadRecord]) -> None:
        self._registry.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = self._registry.with_name(f".{uuid4()}.downloads.tmp")
        try:
            with temporary.open("x", encoding="utf-8") as handle:
                os.chmod(temporary, 0o600)
                json.dump(
                    {"schema_version": "1.0", "exports": [item.model_dump() for item in records]},
                    handle,
                )
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(self._registry)
        finally:
            temporary.unlink(missing_ok=True)

    def register(
        self, *, result: str, revision: str, translation: str = "", paths: list[str]
    ) -> None:
        """Called only with artifacts just written or byte-validated by trusted export services."""
        context = self._context(result, revision, translation)
        with self._lock:
            records = self._records()
            by_path = {item.path: item for item in records}
            for raw in paths:
                path = self._path(raw)
                if path.suffix.lower() not in {".txt", ".srt", ".vtt", ".ytt", ".html", ".json"}:
                    raise ValueError("Unsupported export artifact type")
                data = self._bytes(str(path))
                record = DownloadRecord(
                    path=str(path),
                    sha256=hashlib.sha256(data).hexdigest(),
                    size=len(data),
                    context=context,
                )
                previous = by_path.get(record.path)
                if previous is not None and previous != record:
                    raise ValueError(
                        "Published export identity changed; download registration rejected"
                    )
                by_path[record.path] = record
            if len(by_path) > 10000:
                raise ValueError("Export download registry is full")
            self._save(list(by_path.values()))

    def list(
        self, *, result: str, revision: str, directory: str, translation: str = ""
    ) -> dict[str, Any]:
        context = self._context(result, revision, translation)
        output = self._path(directory, directory=True)
        with self._lock:
            records = self._records()
            known = {item.path for item in records}
            # Read-only migration: verify legacy exports against the same deterministic renderers.
            # Historic custom palettes require their recorded manifest or their original settings.
            candidates: tuple[Path, ...] = ()
            try:
                if output.exists():
                    if translation:
                        translated = load_transcript_translation(Path(context["translation"]))
                        stem = (
                            f"{translated.job_id}_{translated.direction.target_language}_translation_"
                            f"{translated.translation_number:03d}"
                        )
                        formats = tuple(
                            format_
                            for format_ in TranslationExportFormat
                            if (output / f"{stem}.{format_.value}").is_file()
                        )
                        if formats:
                            for format_ in formats:
                                self._bytes(str(output / f"{stem}.{format_.value}"))
                            provenance = output / f"{stem}.provenance.json"
                            if provenance.exists() or provenance.is_symlink():
                                self._bytes(str(provenance))
                            payloads = render_translation_exports(
                                Path(context["translation"]),
                                formats=formats,
                                output_directory=output,
                                subtitles_config=self._config.subtitles,
                            )
                            candidates = tuple(
                                path
                                for path, expected in payloads
                                if self._bytes(str(path)) == expected
                            )
                    else:
                        candidates = verified_existing_revision_exports(
                            Path(context["result"]),
                            Path(context["revision"]),
                            output,
                            self._config.subtitles,
                        )
            except (OSError, ValueError, ApplicationError):
                candidates = ()
            new_paths = [str(path) for path in candidates if str(path) not in known]
            if new_paths:
                self.register(
                    result=result, revision=revision, translation=translation, paths=new_paths
                )
                records = self._records()
            now = time.monotonic()
            self._tokens = {
                key: value for key, value in self._tokens.items() if now - value[0] < 1800
            }
            if len(self._tokens) > 2000:
                self._tokens.clear()
            exports = []
            unavailable = []
            for record in records:
                if record.context != context or Path(record.path).parent != output:
                    continue
                try:
                    self._verify(record)
                except (OSError, ValueError):
                    unavailable.append(Path(record.path).name)
                    continue
                token = secrets.token_urlsafe(32)
                self._tokens[token] = (now, record)
                exports.append(
                    {
                        "filename": Path(record.path).name,
                        "size_bytes": record.size,
                        "sha256": record.sha256,
                        "url": f"/api/v1/export-downloads/{token}",
                    }
                )
            return {"exports": exports, "unavailable": unavailable}

    def _verify(self, record: DownloadRecord) -> bytes:
        context = record.context
        current = self._context(
            context["result"], context.get("revision", ""), context.get("translation", "")
        )
        if current != context:
            raise ValueError("Export lineage changed; refresh the export list")
        payload = self._bytes(record.path)
        if len(payload) != record.size or hashlib.sha256(payload).hexdigest() != record.sha256:
            raise ValueError("Published export bytes changed; download rejected")
        return payload

    def open(self, token: str) -> tuple[str, bytes]:
        with self._lock:
            item = self._tokens.get(token)
            if item is None or time.monotonic() - item[0] >= 1800:
                raise ValueError("Download link expired; refresh the export list")
            return Path(item[1].path).name, self._verify(item[1])
