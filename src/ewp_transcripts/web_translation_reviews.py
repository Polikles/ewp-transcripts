"""Model-free semantic translation review operations for the local GUI."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from ewp_transcripts.application import (
    TranslationExportFormat,
    apply_translation_review_file,
    audit_translation_file,
    export_translation,
    prepare_translation_review_file,
    preview_translation_review_file,
)
from ewp_transcripts.config import ApplicationConfig
from ewp_transcripts.domain.errors import ApplicationError
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.domain.translation import Language, load_transcript_translation
from ewp_transcripts.translation_review_format import (
    load_translation_review,
    render_translation_review,
)


class GuiTranslationReviewError(ApplicationError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


PathResolver = Callable[..., Path]


class GuiTranslationReviewController:
    def __init__(self, *, config: ApplicationConfig, resolve_path: PathResolver) -> None:
        self._config = config
        self._resolve_path = resolve_path
        self._previewed: dict[str, str] = {}

    def prepare(
        self,
        *,
        result: str,
        revision: str,
        parent: str,
        output: str,
        target_language: str,
    ) -> dict[str, Any]:
        result_path = self._resolve_path(result)
        revision_path = self._resolve_path(revision) if revision else None
        parent_path = self._resolve_path(parent) if parent else None
        destination = self._resolve_path(output, directory=True)
        candidate = load_transcript_translation(parent_path) if parent_path else None
        if candidate is None and target_language not in {"pl", "en"}:
            raise GuiTranslationReviewError(
                "GUI_TRANSLATION_REVIEW_TARGET_REQUIRED",
                "Choose Polish or English before starting a manual translation review.",
            )
        outcome = prepare_translation_review_file(
            result_path,
            target_language=(
                candidate.direction.target_language
                if candidate
                else cast(Language, target_language)
            ),
            config=self._config,
            revision_path=revision_path,
            parent_translation_path=parent_path,
            output_directory=destination,
            style=candidate.style if candidate else None,
        )
        return self.document(outcome.path, result_path, revision_path, parent_path)

    def document(
        self,
        review: str | Path,
        result: str | Path,
        revision: str | Path | None,
        parent: str | Path | None,
    ) -> dict[str, Any]:
        review_path = self._resolve_path(str(review))
        parsed = load_translation_review(review_path)
        return {
            "review_path": str(review_path),
            "review_sha256": sha256_file(review_path),
            "result_path": str(self._resolve_path(str(result))),
            "revision_path": str(self._resolve_path(str(revision))) if revision else "",
            "parent_translation_path": str(self._resolve_path(str(parent))) if parent else "",
            "job_id": parsed.header.job_id,
            "direction": {
                "source_language": parsed.header.source_language,
                "target_language": parsed.header.target_language,
            },
            "source_verification": parsed.header.source.verification,
            "dictionary": parsed.header.dictionary.model_dump(mode="json")
            if parsed.header.dictionary
            else None,
            "units": [unit.model_dump(mode="json") for unit in parsed.units],
        }

    def save(
        self,
        *,
        review: str,
        result: str,
        revision: str,
        parent: str,
        expected_sha256: str,
        targets: list[dict[str, Any]],
    ) -> dict[str, Any]:
        review_path = self._resolve_path(review)
        if sha256_file(review_path) != expected_sha256:
            raise GuiTranslationReviewError(
                "GUI_TRANSLATION_REVIEW_CONFLICT",
                "The translation review changed after it was loaded.",
            )
        parsed = load_translation_review(review_path)
        supplied = {
            str(item.get("unit_id")): item.get("target_text")
            for item in targets
            if isinstance(item, dict)
        }
        if set(supplied) != {unit.unit_id for unit in parsed.units} or not all(
            isinstance(value, str) for value in supplied.values()
        ):
            raise GuiTranslationReviewError(
                "GUI_TRANSLATION_REVIEW_STRUCTURE_INVALID",
                "Translation unit identity cannot change.",
            )
        updated = parsed.model_copy(
            update={
                "units": tuple(
                    unit.model_copy(
                        update={"target_text": " ".join(cast(str, supplied[unit.unit_id]).split())}
                    )
                    for unit in parsed.units
                )
            }
        )
        self._atomic_replace(review_path, render_translation_review(updated).encode("utf-8"))
        self._previewed.pop(str(review_path), None)
        return self.document(review_path, result, revision or None, parent)

    def preview(self, *, review: str, result: str, revision: str, parent: str) -> dict[str, Any]:
        review_path = self._resolve_path(review)
        outcome = preview_translation_review_file(
            review_path,
            result_path=self._resolve_path(result),
            revision_path=self._resolve_path(revision) if revision else None,
            parent_translation_path=self._resolve_path(parent) if parent else None,
        )
        digest = sha256_file(review_path)
        self._previewed[str(review_path)] = digest
        return {
            "review_sha256": digest,
            "translation_number": outcome.translation.translation_number,
            "statistics": outcome.translation.statistics.model_dump(mode="json"),
            "warnings": [item.model_dump(mode="json") for item in outcome.translation.warnings],
        }

    def apply(
        self, *, review: str, result: str, revision: str, parent: str, output: str
    ) -> dict[str, Any]:
        review_path = self._resolve_path(review)
        if self._previewed.get(str(review_path)) != sha256_file(review_path):
            raise GuiTranslationReviewError(
                "GUI_TRANSLATION_REVIEW_PREVIEW_REQUIRED",
                "Preview the current saved translation review before applying it.",
            )
        outcome = apply_translation_review_file(
            review_path,
            result_path=self._resolve_path(result),
            config=self._config,
            revision_path=self._resolve_path(revision) if revision else None,
            parent_translation_path=self._resolve_path(parent) if parent else None,
            output_directory=self._resolve_path(output, directory=True),
        )
        return {
            "translation_path": str(outcome.translation_path),
            "translation_number": outcome.translation.translation_number,
            "final": True,
        }

    def audit_export(
        self,
        *,
        translation: str,
        result: str,
        revision: str,
        audit_output: str,
        export_output: str,
        formats: list[str],
    ) -> dict[str, Any]:
        translation_path = self._resolve_path(translation)
        result_path = self._resolve_path(result)
        revision_path = self._resolve_path(revision) if revision else None
        audit = audit_translation_file(
            translation_path,
            config=self._config,
            results_directory=result_path.parent,
            revisions_directory=revision_path.parent if revision_path else None,
            output_directory=self._resolve_path(audit_output, directory=True),
        )
        try:
            selected = tuple(TranslationExportFormat(item) for item in formats)
        except ValueError as error:
            raise GuiTranslationReviewError(
                "GUI_TRANSLATION_EXPORT_FORMAT_INVALID", "Unknown translation export format."
            ) from error
        exported = export_translation(
            translation_path,
            config=self._config,
            formats=selected,
            output_directory=self._resolve_path(export_output, directory=True),
        )
        return {
            "audit_path": str(audit.audit_path),
            "audit_written": audit.written,
            "written": [str(path) for path in exported.written],
            "skipped": [str(path) for path in exported.skipped],
        }

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
