"""Model-free transcript review operations for the local browser GUI."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ewp_transcripts.application import (
    ExportFormat,
    apply_review_file,
    export_result,
    prepare_review_file,
    preview_review_file,
)
from ewp_transcripts.config import ApplicationConfig
from ewp_transcripts.domain.canonical import load_canonical_result
from ewp_transcripts.domain.errors import ApplicationError
from ewp_transcripts.domain.review import ReviewAnchor, ReviewSpeakerBlock
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.review_format import load_review, render_review


class GuiReviewError(ApplicationError):
    """Controlled browser review failure with one stable diagnostic code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


PathResolver = Callable[..., Path]


class GuiReviewController:
    """Prepare, edit, preview, and immutably apply transcript reviews."""

    def __init__(self, *, config: ApplicationConfig, resolve_path: PathResolver) -> None:
        self._config = config
        self._resolve_path = resolve_path
        self._previewed: dict[str, str] = {}

    def prepare(
        self, result: str, output_directory: str, source_revision: str = ""
    ) -> dict[str, Any]:
        result_path = self._resolve_path(result)
        output_path = self._resolve_path(output_directory, directory=True)
        if not result_path.is_file():
            raise GuiReviewError("GUI_REVIEW_RESULT_INVALID", "Result path must be one file")
        outcome = prepare_review_file(
            result_path,
            output_directory=output_path,
            source_revision_path=(self._resolve_path(source_revision) if source_revision else None),
            anchor_target_words=self._config.revision.anchor_target_words,
            lock_timeout_seconds=self._config.runtime.lock_timeout_seconds,
        )
        return self.document(outcome.path, result_path)

    def document(self, review: str | Path, result: str | Path) -> dict[str, Any]:
        review_path = self._resolve_path(str(review))
        result_path = self._resolve_path(str(result))
        parsed = load_review(review_path)
        base = load_canonical_result(result_path)
        if parsed.header.base_result_sha256 != sha256_file(result_path):
            raise GuiReviewError(
                "GUI_REVIEW_RESULT_MISMATCH",
                "The saved review does not belong to the selected canonical result.",
            )
        verification = next(
            (
                extension.value
                for extension in parsed.header.extensions
                if extension.key == "x_source_verification"
            ),
            "canonical_asr" if parsed.header.source_revision_number is None else "revision",
        )
        base_speakers = [speaker.speaker_id for speaker in base.speakers]
        speakers = [
            *base_speakers,
            *sorted(set(parsed.header.speaker_labels) - set(base_speakers)),
        ]
        base_labels = {speaker.speaker_id: speaker.speaker_label for speaker in base.speakers}
        return {
            "review_path": str(review_path),
            "result_path": str(result_path),
            "review_sha256": sha256_file(review_path),
            "job_id": parsed.header.job_id,
            "language": parsed.header.language,
            "source_verification": verification,
            "speakers": speakers,
            "speaker_labels": {
                **base_labels,
                **parsed.header.speaker_labels,
            },
            "anchors": [
                {
                    "first_word_id": anchor.first_word_id,
                    "last_word_id": anchor.last_word_id,
                    "blocks": [block.model_dump(mode="json") for block in anchor.speaker_blocks],
                }
                for anchor in parsed.anchors
            ],
        }

    def save(
        self,
        review: str,
        result: str,
        *,
        expected_sha256: str,
        anchors: list[dict[str, Any]],
        speaker_labels: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        review_path = self._resolve_path(review)
        result_path = self._resolve_path(result)
        if sha256_file(review_path) != expected_sha256:
            raise GuiReviewError(
                "GUI_REVIEW_CONFLICT",
                "The review changed after it was loaded; reload before saving.",
            )
        parsed = load_review(review_path)
        base = load_canonical_result(result_path)
        known_speakers = {speaker.speaker_id for speaker in base.speakers}
        base_labels = {speaker.speaker_id: speaker.speaker_label for speaker in base.speakers}
        revised_labels = dict(parsed.header.speaker_labels)
        if speaker_labels is not None:
            if not isinstance(speaker_labels, dict):
                raise GuiReviewError(
                    "GUI_REVIEW_STRUCTURE_INVALID", "Speaker labels must be an object"
                )
            for speaker_id, label in speaker_labels.items():
                if re.fullmatch(r"speaker_[0-9]{3,}", speaker_id) is None or not isinstance(
                    label, str
                ):
                    raise GuiReviewError(
                        "GUI_REVIEW_STRUCTURE_INVALID", "A speaker label is malformed"
                    )
                normalized = " ".join(label.split())
                if not normalized:
                    raise GuiReviewError(
                        "GUI_REVIEW_STRUCTURE_INVALID", "Speaker labels cannot be empty"
                    )
                if speaker_id in base_labels and normalized == base_labels[speaker_id]:
                    revised_labels.pop(speaker_id, None)
                else:
                    revised_labels[speaker_id] = normalized
        allowed_speakers = known_speakers | set(revised_labels)
        if len(anchors) != len(parsed.anchors):
            raise GuiReviewError("GUI_REVIEW_STRUCTURE_INVALID", "Review anchors cannot change")
        updated: list[ReviewAnchor] = []
        for original, supplied in zip(parsed.anchors, anchors, strict=True):
            if (
                supplied.get("first_word_id") != original.first_word_id
                or supplied.get("last_word_id") != original.last_word_id
            ):
                raise GuiReviewError(
                    "GUI_REVIEW_STRUCTURE_INVALID", "Review anchor identity cannot change"
                )
            raw_blocks = supplied.get("blocks")
            if not isinstance(raw_blocks, list) or not raw_blocks:
                raise GuiReviewError(
                    "GUI_REVIEW_STRUCTURE_INVALID", "Every review anchor needs at least one block"
                )
            blocks: list[ReviewSpeakerBlock] = []
            for block in raw_blocks:
                if not isinstance(block, dict):
                    raise GuiReviewError(
                        "GUI_REVIEW_STRUCTURE_INVALID", "Every review block must be an object"
                    )
                normalized_text = " ".join(str(block.get("text", "")).split())
                if not normalized_text:
                    raise GuiReviewError(
                        "GUI_REVIEW_STRUCTURE_INVALID", "Review blocks cannot be empty"
                    )
                try:
                    parsed_block = ReviewSpeakerBlock.model_validate(
                        {**block, "text": normalized_text}
                    )
                except ValueError as error:
                    raise GuiReviewError(
                        "GUI_REVIEW_STRUCTURE_INVALID", "A review block is malformed"
                    ) from error
                if parsed_block.speaker_id not in allowed_speakers:
                    raise GuiReviewError(
                        "GUI_REVIEW_STRUCTURE_INVALID", "Review references an unknown speaker"
                    )
                blocks.append(parsed_block)
            updated.append(original.model_copy(update={"speaker_blocks": tuple(blocks)}))
        revised = parsed.model_copy(
            update={
                "header": parsed.header.model_copy(update={"speaker_labels": revised_labels}),
                "anchors": tuple(updated),
            }
        )
        self._atomic_replace(review_path, render_review(revised).encode("utf-8"))
        self._previewed.pop(str(review_path), None)
        return self.document(review_path, result_path)

    def preview(self, review: str, result: str) -> dict[str, Any]:
        review_path = self._resolve_path(review)
        result_path = self._resolve_path(result)
        outcome = preview_review_file(
            review_path,
            results_directory=result_path.parent,
            long_gap_warning_ms=self._config.revision.long_gap_warning_ms,
        )
        digest = sha256_file(review_path)
        self._previewed[str(review_path)] = digest
        return {
            "review_path": str(review_path),
            "review_sha256": digest,
            "job_id": outcome.revision.job_id,
            "revision_number": outcome.revision.revision_number,
            "statistics": outcome.revision.statistics.model_dump(mode="json"),
            "warnings": [warning.model_dump(mode="json") for warning in outcome.revision.warnings],
        }

    def apply(self, review: str, result: str, output_directory: str) -> dict[str, Any]:
        review_path = self._resolve_path(review)
        result_path = self._resolve_path(result)
        output_path = self._resolve_path(output_directory, directory=True)
        digest = sha256_file(review_path)
        if self._previewed.get(str(review_path)) != digest:
            raise GuiReviewError(
                "GUI_REVIEW_PREVIEW_REQUIRED",
                "Preview the current saved review before applying it.",
            )
        outcome = apply_review_file(
            review_path,
            config=self._config,
            results_directory=result_path.parent,
            output_directory=output_path,
        )
        return {
            "revision_path": str(outcome.revision_path),
            "revision_number": outcome.revision.revision_number,
            "job_id": outcome.revision.job_id,
            "warnings": [warning.model_dump(mode="json") for warning in outcome.revision.warnings],
        }

    def export(
        self,
        result: str,
        revision: str,
        output_directory: str,
        formats: list[str],
    ) -> dict[str, Any]:
        result_path = self._resolve_path(result)
        revision_path = self._resolve_path(revision)
        output_path = self._resolve_path(output_directory, directory=True)
        try:
            selected = tuple(ExportFormat(item) for item in formats)
        except ValueError as error:
            raise GuiReviewError("GUI_EXPORT_FORMAT_INVALID", "Unknown export format") from error
        outcome = export_result(
            result_path,
            formats=selected,
            output_directory=output_path,
            subtitles_config=self._config.subtitles,
            revision=revision_path,
        )
        return {
            "revision_number": outcome.revision_number,
            "written": [str(path) for path in outcome.written],
            "skipped": [str(path) for path in outcome.skipped],
        }

    def remember_session(
        self,
        *,
        project_output_directory: str,
        result: str,
        review: str,
        review_output_directory: str,
        revision_output_directory: str,
        export_output_directory: str,
        applied_revision: str = "",
    ) -> dict[str, Any]:
        """Persist one non-secret review pointer set inside its project output root."""

        root = self._resolve_path(project_output_directory, directory=True)
        root.mkdir(parents=True, exist_ok=True)
        document = {
            "session_version": 1,
            "result_path": str(self._resolve_path(result)),
            "review_path": str(self._resolve_path(review)),
            "review_output_directory": str(
                self._resolve_path(review_output_directory, directory=True)
            ),
            "revision_output_directory": str(
                self._resolve_path(revision_output_directory, directory=True)
            ),
            "export_output_directory": str(
                self._resolve_path(export_output_directory, directory=True)
            ),
            "applied_revision_path": (
                str(self._resolve_path(applied_revision)) if applied_revision else ""
            ),
        }
        path = root / ".ewp-gui-review-session.json"
        self._atomic_replace(
            path,
            (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )
        return {"session_path": str(path)}

    def restore_session(self, project_output_directory: str) -> dict[str, Any]:
        """Reload the last review pointer set recorded under one persistent output root."""

        root = self._resolve_path(project_output_directory, directory=True)
        path = root / ".ewp-gui-review-session.json"
        if not path.is_file() or path.is_symlink():
            raise GuiReviewError(
                "GUI_REVIEW_SESSION_NOT_FOUND",
                "No saved GUI review session exists under this output root.",
            )
        try:
            session = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise GuiReviewError(
                "GUI_REVIEW_SESSION_INVALID", "The saved GUI review session is invalid."
            ) from error
        if not isinstance(session, dict) or session.get("session_version") != 1:
            raise GuiReviewError(
                "GUI_REVIEW_SESSION_INVALID", "The saved GUI review session is invalid."
            )
        required = (
            "result_path",
            "review_path",
            "review_output_directory",
            "revision_output_directory",
            "export_output_directory",
        )
        if not all(isinstance(session.get(key), str) and session[key] for key in required):
            raise GuiReviewError(
                "GUI_REVIEW_SESSION_INVALID", "The saved GUI review session is incomplete."
            )
        review_document = self.document(session["review_path"], session["result_path"])
        applied = session.get("applied_revision_path", "")
        if not isinstance(applied, str):
            raise GuiReviewError(
                "GUI_REVIEW_SESSION_INVALID", "The saved GUI review session is invalid."
            )
        if applied:
            self._resolve_path(applied)
        return {**review_document, "session": session, "session_path": str(path)}

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
