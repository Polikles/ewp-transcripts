"""Guarded inventory and cleanup for durable GUI-selected source copies."""

from __future__ import annotations

import re
from collections.abc import Iterable
from contextlib import suppress
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.web_jobs import GuiTranscriptionJob
from ewp_transcripts.web_workspaces import GuiWorkspaceDocument

_DIGEST = re.compile(r"[0-9a-f]{64}")
_CATEGORIES = frozenset({"canonical", "media"})
_LINEAGE_DIRECTORIES = (
    "correction-candidates",
    "reviews",
    "revisions",
    "translation-candidates",
    "translation-reviews",
    "accepted-translations",
    "translation-audits",
)
_LINEAGE_SUFFIXES = frozenset({".json", ".txt"})


class GuiManagedSource(BaseModel):
    """One durable GUI source and the reasons it must be retained."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    relative_path: str
    path: str
    category: str
    filename: str
    sha256: str
    size_bytes: int = Field(ge=0)
    removable: bool
    references: tuple[str, ...]


class GuiManagedSourceCleanupError(ValueError):
    """A cleanup request failed its final reference or structure audit."""


def inventory_managed_sources(
    output_directory: Path,
    *,
    queue_jobs: Iterable[GuiTranscriptionJob],
    workspaces: Iterable[GuiWorkspaceDocument],
) -> tuple[GuiManagedSource, ...]:
    """Inventory exact managed files and conservatively identify live references."""

    root = output_directory / ".ewp-gui-sources"
    if not root.exists():
        return ()
    if root.is_symlink() or not root.is_dir():
        raise GuiManagedSourceCleanupError("Managed source root is not a safe directory")

    exact_references = _exact_references(queue_jobs, workspaces)
    candidates: list[tuple[Path, str, str, str, list[str]]] = []
    canonical_digests: set[str] = set()
    for category in sorted(_CATEGORIES):
        category_root = root / category
        if not category_root.exists():
            continue
        if category_root.is_symlink() or not category_root.is_dir():
            raise GuiManagedSourceCleanupError(f"Managed source category is unsafe: {category}")
        for digest_root in sorted(category_root.iterdir()):
            if (
                digest_root.is_symlink()
                or not digest_root.is_dir()
                or _DIGEST.fullmatch(digest_root.name) is None
            ):
                continue
            for path in sorted(digest_root.iterdir()):
                if not path.is_file() or path.is_symlink():
                    continue
                references = list(exact_references.get(path.resolve(strict=False), ()))
                try:
                    if sha256_file(path) != digest_root.name:
                        references.append("content hash no longer matches its managed path")
                except OSError:
                    references.append("source could not be read for its final safety check")
                candidates.append((path, category, digest_root.name, path.name, references))
                if category == "canonical":
                    canonical_digests.add(digest_root.name)

    lineage_references = _lineage_references(output_directory, canonical_digests)
    inventory: list[GuiManagedSource] = []
    for path, category, digest, filename, references in candidates:
        if category == "canonical":
            references.extend(lineage_references.get(digest, ()))
        unique_references = tuple(dict.fromkeys(references))
        inventory.append(
            GuiManagedSource(
                relative_path=path.relative_to(root).as_posix(),
                path=str(path),
                category=category,
                filename=filename,
                sha256=digest,
                size_bytes=path.stat().st_size,
                removable=not unique_references,
                references=unique_references,
            )
        )
    return tuple(inventory)


def cleanup_managed_sources(
    output_directory: Path,
    relative_paths: tuple[str, ...],
    *,
    queue_jobs: Iterable[GuiTranscriptionJob],
    workspaces: Iterable[GuiWorkspaceDocument],
) -> tuple[str, ...]:
    """Delete only selected copies that remain unreferenced after a fresh complete audit."""

    inventory = {
        item.relative_path: item
        for item in inventory_managed_sources(
            output_directory, queue_jobs=queue_jobs, workspaces=workspaces
        )
    }
    if not relative_paths or len(set(relative_paths)) != len(relative_paths):
        raise GuiManagedSourceCleanupError("Select one or more unique managed source copies")
    selected: list[GuiManagedSource] = []
    for relative_path in relative_paths:
        item = inventory.get(relative_path)
        if item is None:
            raise GuiManagedSourceCleanupError(
                "A selected managed source no longer exists; refresh the inventory"
            )
        if not item.removable:
            raise GuiManagedSourceCleanupError(
                f"Managed source is still referenced and cannot be removed: {item.filename}"
            )
        selected.append(item)

    root = output_directory / ".ewp-gui-sources"
    paths_to_delete: list[tuple[GuiManagedSource, Path]] = []
    for item in selected:
        path = root / Path(item.relative_path)
        if path.is_symlink() or not path.is_file() or sha256_file(path) != item.sha256:
            raise GuiManagedSourceCleanupError(
                "A selected managed source changed during cleanup; refresh the inventory"
            )
        paths_to_delete.append((item, path))
    removed: list[str] = []
    for item, path in paths_to_delete:
        path.unlink()
        removed.append(item.relative_path)
        _remove_empty_managed_parents(path.parent, root)
    return tuple(removed)


def _exact_references(
    queue_jobs: Iterable[GuiTranscriptionJob],
    workspaces: Iterable[GuiWorkspaceDocument],
) -> dict[Path, tuple[str, ...]]:
    references: dict[Path, list[str]] = {}

    def add(value: object, label: str) -> None:
        if not isinstance(value, str) or not value.strip():
            return
        path = Path(value)
        if path.is_absolute():
            references.setdefault(path.resolve(strict=False), []).append(label)

    for queue_job in queue_jobs:
        label = f"current queue: {queue_job.planned_job_id} ({queue_job.status})"
        for queue_path in (
            queue_job.input_path,
            queue_job.planned_result_path,
            queue_job.result_path,
        ):
            add(queue_path, label)
    seen_workspaces: set[str] = set()
    for workspace in workspaces:
        if workspace.workspace_id in seen_workspaces:
            continue
        seen_workspaces.add(workspace.workspace_id)
        label = f"saved workspace: {workspace.name}"
        for workspace_field_value in workspace.fields.values():
            add(workspace_field_value, label)
        for staged_job in workspace.staged_jobs:
            for key in ("input_path", "planned_result_path", "output_directory"):
                add(staged_job.get(key), label)
        for terminal_job in workspace.terminal_jobs:
            for terminal_path in (
                terminal_job.input_path,
                terminal_job.planned_result_path,
                terminal_job.result_path,
            ):
                add(terminal_path, label)
    return {path: tuple(labels) for path, labels in references.items()}


def _lineage_references(output_directory: Path, digests: set[str]) -> dict[str, tuple[str, ...]]:
    references: dict[str, list[str]] = {digest: [] for digest in digests}
    if not digests:
        return {}
    encoded = {digest: digest.encode("ascii") for digest in digests}
    lineage_files: list[Path] = []
    for directory_name in _LINEAGE_DIRECTORIES:
        directory = output_directory / directory_name
        if not directory.is_dir() or directory.is_symlink():
            continue
        lineage_files.extend(directory.rglob("*"))
    latest_review_session = output_directory / ".ewp-gui-review-session.json"
    if latest_review_session.exists():
        lineage_files.append(latest_review_session)
    review_sessions = output_directory / ".ewp-gui-review-sessions"
    if review_sessions.is_dir() and not review_sessions.is_symlink():
        lineage_files.extend(review_sessions.glob("*.json"))
    for path in lineage_files:
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in _LINEAGE_SUFFIXES:
            continue
        try:
            content = path.read_bytes()
        except OSError:
            continue
        try:
            relative = path.relative_to(output_directory).as_posix()
        except ValueError:
            continue
        for digest, marker in encoded.items():
            if marker in content:
                references[digest].append(f"workflow lineage: {relative}")
    return {digest: tuple(labels) for digest, labels in references.items() if labels}


def _remove_empty_managed_parents(directory: Path, root: Path) -> None:
    current = directory
    while current != root:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent
    with suppress(OSError):
        root.rmdir()
