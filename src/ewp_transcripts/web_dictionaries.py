"""Project correction-dictionary proposal and approval for the local GUI."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ewp_transcripts.correction_dictionary import (
    CorrectionDictionaryProposal,
    approve_correction_dictionary,
    load_project_correction_dictionary,
    propose_correction_dictionary,
    write_correction_dictionary_proposal,
)
from ewp_transcripts.domain.errors import ApplicationError
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.gui_library import GuiLibrary
from ewp_transcripts.translation_dictionary import load_project_translation_dictionary


class GuiDictionaryError(ApplicationError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


PathResolver = Callable[..., Path]


class GuiDictionaryController:
    def __init__(self, *, resolve_path: PathResolver, library: GuiLibrary | None = None) -> None:
        self._resolve_path = resolve_path
        self._library = library

    def propose(
        self,
        *,
        canonical_directory: str,
        revision_directory: str,
        output_root: str,
        project_id: str,
        minimum_occurrences: int,
        previous_dictionary: str,
    ) -> dict[str, Any]:
        if not project_id.strip():
            raise GuiDictionaryError("GUI_DICTIONARY_PROJECT_REQUIRED", "Project ID is required.")
        previous = None
        previous_sha = None
        if previous_dictionary:
            previous, previous_sha = load_project_correction_dictionary(
                self._resolve_path(previous_dictionary)
            )
        proposal = propose_correction_dictionary(
            canonical_directory=self._resolve_path(canonical_directory, directory=True),
            revision_directory=self._resolve_path(revision_directory, directory=True),
            project_id=project_id.strip(),
            minimum_occurrences=minimum_occurrences,
            previous_dictionary=previous,
            previous_dictionary_sha256=previous_sha,
        )
        root = self._resolve_path(output_root, directory=True)
        path = root / "dictionary-proposals" / f"{project_id.strip()}-pl.proposal.json"
        write_correction_dictionary_proposal(proposal, path)
        return self.document(path)

    def document(self, proposal_path: str | Path) -> dict[str, Any]:
        path = self._resolve_path(str(proposal_path))
        proposal = CorrectionDictionaryProposal.model_validate_json(path.read_bytes())
        counts = {
            status: sum(item.status == status for item in proposal.candidates)
            for status in ("pending", "approved", "rejected")
        }
        return {
            "proposal_path": str(path),
            "proposal_sha256": sha256_file(path),
            "project_id": proposal.project_id,
            "case_count": proposal.case_count,
            "job_ids": list(proposal.job_ids),
            "minimum_occurrences": proposal.minimum_occurrences,
            "previous_dictionary_sha256": proposal.previous_dictionary_sha256,
            "counts": counts,
            "candidates": [item.model_dump(mode="json") for item in proposal.candidates],
        }

    def save(
        self, *, proposal_path: str, expected_sha256: str, decisions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        path = self._resolve_path(proposal_path)
        if sha256_file(path) != expected_sha256:
            raise GuiDictionaryError(
                "GUI_DICTIONARY_CONFLICT", "The proposal changed after it was loaded."
            )
        proposal = CorrectionDictionaryProposal.model_validate_json(path.read_bytes())
        supplied = {
            (str(item.get("source")), str(item.get("target"))): item.get("status")
            for item in decisions
            if isinstance(item, dict)
        }
        expected = {(item.source, item.target) for item in proposal.candidates}
        if set(supplied) != expected or not all(
            value in {"pending", "approved", "rejected"} for value in supplied.values()
        ):
            raise GuiDictionaryError(
                "GUI_DICTIONARY_DECISIONS_INVALID",
                "Every unchanged proposal mapping requires one valid decision.",
            )
        updated = proposal.model_copy(
            update={
                "candidates": tuple(
                    item.model_copy(update={"status": supplied[(item.source, item.target)]})
                    for item in proposal.candidates
                )
            }
        )
        self._atomic_replace(path, (updated.model_dump_json(indent=2) + "\n").encode("utf-8"))
        return self.document(path)

    def publish(
        self, *, proposal_path: str, dictionary_id: str, output_root: str
    ) -> dict[str, Any]:
        if not dictionary_id.strip():
            raise GuiDictionaryError("GUI_DICTIONARY_ID_REQUIRED", "Dictionary ID is required.")
        proposal = self._resolve_path(proposal_path)
        root = self._resolve_path(output_root, directory=True)
        output = root / "dictionaries" / f"{dictionary_id.strip()}.json"
        dictionary = approve_correction_dictionary(
            proposal_path=proposal, dictionary_id=dictionary_id.strip(), output_path=output
        )
        return {
            "dictionary_path": str(output),
            "dictionary_sha256": sha256_file(output),
            "dictionary": dictionary.model_dump(mode="json"),
        }

    def catalog(self, directory: str, *, include_hidden: bool = False) -> dict[str, Any]:
        root = self._resolve_path(directory, directory=True)
        paths = sorted(root.rglob("*.json"))
        if len(paths) > 1000:
            raise GuiDictionaryError(
                "GUI_DICTIONARY_CATALOG_TOO_LARGE",
                "Dictionary catalog contains more than 1,000 JSON files.",
            )
        items: list[dict[str, Any]] = []
        for path in paths:
            if path.is_symlink() or not path.is_file():
                continue
            try:
                dictionary, digest = load_project_correction_dictionary(path)
                items.append(
                    {
                        "kind": "correction",
                        "path": str(path),
                        "dictionary_id": dictionary.dictionary_id,
                        "project_id": dictionary.project_id,
                        "version": dictionary.dictionary_version,
                        "language": dictionary.language,
                        "sha256": digest,
                    }
                )
                continue
            except (ApplicationError, OSError, UnicodeError, ValueError):
                pass
            try:
                translation, digest = load_project_translation_dictionary(path)
                items.append(
                    {
                        "kind": "translation",
                        "path": str(path),
                        "dictionary_id": translation.dictionary_id,
                        "project_id": translation.project_id,
                        "version": translation.dictionary_version,
                        "source_language": translation.source_language,
                        "target_language": translation.target_language,
                        "sha256": digest,
                    }
                )
            except (ApplicationError, OSError, UnicodeError, ValueError):
                continue
        for item in items:
            item["hidden"] = bool(
                self._library and self._library.hidden(item["path"], item["sha256"])
            )
        if not include_hidden:
            items = [item for item in items if not item["hidden"]]
        return {"catalog_directory": str(root), "count": len(items), "items": items}

    @staticmethod
    def _atomic_replace(path: Path, payload: bytes) -> None:
        temporary = path.parent / f".{path.name}.{os.getpid()}.gui.tmp"
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()
