"""Bounded non-secret project/location catalog and read-only canonical discovery."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from itertools import islice
from pathlib import Path
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.web_workflows import require_completed_canonical_result


class NamedLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=80, pattern=r"^[^\x00-\x1f]+$")
    kind: Literal["input", "output"]
    path: str = Field(min_length=1, max_length=4096)


class RecentProject(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-f0-9]{24}$")
    name: str = Field(min_length=1, max_length=100)
    output_root: str = Field(min_length=1, max_length=4096)
    result_path: str = Field(default="", max_length=4096)
    updated_at: AwareDatetime


class ProjectCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1] = 1
    locations: tuple[NamedLocation, ...] = Field(default=(), max_length=50)
    recent: tuple[RecentProject, ...] = Field(default=(), max_length=30)


class GuiProjects:
    def __init__(self, path: Path, resolve_path: Callable[..., Path]) -> None:
        self.path, self.resolve = path, resolve_path
        self._lock = threading.RLock()

    def catalog(self) -> ProjectCatalog:
        with self._lock:
            if not self.path.exists():
                return ProjectCatalog()
            if self.path.is_symlink() or self.path.stat().st_size > 256 * 1024:
                raise ValueError("Project catalog is invalid")
            return ProjectCatalog.model_validate_json(self.path.read_text(encoding="utf-8"))

    def merge(self, incoming: ProjectCatalog) -> None:
        """Import references without granting path authority or touching those locations."""
        with self._lock:
            current = self.catalog()
            locations = {(x.kind, x.name): x for x in current.locations}
            for item in incoming.locations:
                key = (item.kind, item.name)
                if key in locations and locations[key].path != item.path:
                    name = (
                        f"{item.name[:60]} ({hashlib.sha256(item.path.encode()).hexdigest()[:8]})"
                    )
                    item = item.model_copy(update={"name": name})
                locations[(item.kind, item.name)] = item
            recent = {item.id: item for item in current.recent}
            recent.update({item.id: item for item in incoming.recent})
            self._write(
                ProjectCatalog(
                    locations=tuple(locations.values())[:50],
                    recent=tuple(sorted(recent.values(), key=lambda x: x.updated_at, reverse=True))[
                        :30
                    ],
                )
            )

    def listing(self) -> dict[str, Any]:
        catalog = self.catalog()
        locations = []
        for item in catalog.locations:
            available = self._available(item.path, directory=True)
            locations.append({**item.model_dump(mode="json"), "available": available})
        recent = []
        for project in catalog.recent:
            available = self._available(project.output_root, directory=True) and (
                not project.result_path or self._available(project.result_path, directory=False)
            )
            recent.append({**project.model_dump(mode="json"), "available": available})
        return {"locations": locations, "recent": recent}

    def _available(self, raw: str, *, directory: bool) -> bool:
        try:
            path = self.resolve(raw, directory=directory)
            return path.is_dir() if directory else path.is_file()
        except (ValueError, OSError):
            return False

    def location(self, *, name: str, kind: str, path: str, remove: bool = False) -> None:
        item = NamedLocation(name=name.strip(), kind=kind, path=path)  # type: ignore[arg-type]
        if not remove:
            resolved = self.resolve(path, directory=True)
            if kind == "input" and not resolved.is_dir():
                raise ValueError("Named input directory is unavailable")
            item = item.model_copy(update={"path": str(resolved)})
        with self._lock:
            current = self.catalog()
            locations = tuple(x for x in current.locations if (x.kind, x.name) != (kind, item.name))
            self._write(
                current.model_copy(
                    update={"locations": locations if remove else (*locations, item)}
                )
            )

    def remember(self, *, output_root: str, result_path: str = "", name: str = "") -> None:
        root = self.resolve(output_root, directory=True)
        result = self.resolve(result_path) if result_path else None
        if result is not None:
            require_completed_canonical_result(result)
        identity = hashlib.sha256(f"{root}\0{result or ''}".encode()).hexdigest()[:24]
        with self._lock:
            current = self.catalog()
            previous = next((x for x in current.recent if x.id == identity), None)
            item = RecentProject(
                id=identity,
                name=name.strip() or (previous.name if previous else root.name) or "Project",
                output_root=str(root),
                result_path=str(result or ""),
                updated_at=datetime.now(UTC),
            )
            self._write(
                current.model_copy(
                    update={"recent": (item, *(x for x in current.recent if x.id != identity))[:30]}
                )
            )

    def forget(self, identity: str) -> None:
        with self._lock:
            current = self.catalog()
            self._write(
                current.model_copy(
                    update={"recent": tuple(x for x in current.recent if x.id != identity)}
                )
            )

    def scan(self, raw: str) -> dict[str, Any]:
        directory = self.resolve(raw, directory=True)
        if not directory.is_dir():
            raise ValueError("Canonical result directory is unavailable")
        entries = list(islice(directory.iterdir(), 501))
        items, rejected = [], 0
        for entry in sorted(entries[:500], key=lambda x: x.name.casefold()):
            if entry.suffix.lower() != ".json" or not entry.is_file():
                continue
            try:
                source = self.resolve(str(entry))
                if source.stat().st_size > 64 * 1024 * 1024:
                    raise ValueError("Canonical result exceeds scan limit")
                result = require_completed_canonical_result(source)
                items.append(
                    {
                        "path": str(source),
                        "sha256": sha256_file(source),
                        "job_id": result.job_id,
                        "language": result.episode.language,
                        "sources": len(result.sources),
                    }
                )
            except (ValueError, OSError):
                rejected += 1
        return {"items": items, "rejected": rejected, "truncated": len(entries) > 500}

    def _write(self, catalog: ProjectCatalog) -> None:
        # model_copy does not validate aggregate limits; validate before writing.
        catalog = ProjectCatalog.model_validate(catalog.model_dump())
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.path.is_symlink():
            raise ValueError("Project catalog must not be a symbolic link")
        fd, name = tempfile.mkstemp(dir=self.path.parent, prefix=".projects-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(catalog.model_dump(mode="json"), handle, ensure_ascii=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, self.path)
        finally:
            Path(name).unlink(missing_ok=True)
