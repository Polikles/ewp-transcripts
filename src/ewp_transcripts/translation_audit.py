"""Exact-source reconstruction and publication of translation audits."""

from __future__ import annotations

import json
from pathlib import Path

from ewp_transcripts.domain.errors import InvalidTranslationError
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.domain.translation import load_transcript_translation
from ewp_transcripts.translation_review_service import prepare_translation_review
from ewp_transcripts.translation_storage import publish_translation_bytes


def build_translation_audit(
    translation_path: Path,
    *,
    results_directory: Path,
    revisions_directory: Path | None = None,
) -> dict[str, object]:
    """Reconstruct source text and fail unless every mapping remains exact."""

    translation = load_transcript_translation(translation_path)
    canonical = translation.source.canonical_result
    result_path = results_directory / canonical.filename
    if not result_path.is_file() or sha256_file(result_path) != canonical.sha256:
        raise InvalidTranslationError("Cannot locate the translation's exact canonical result")
    revision_path = None
    revision_source = translation.source.transcript_revision
    if revision_source is not None:
        revision_path = (revisions_directory or results_directory) / revision_source.filename
        if not revision_path.is_file() or sha256_file(revision_path) != revision_source.sha256:
            raise InvalidTranslationError(
                "Cannot locate the translation's exact transcript revision"
            )
    expected = prepare_translation_review(
        result_path,
        target_language=translation.direction.target_language,
        revision_path=revision_path,
        style=translation.style,
    )
    if expected.header.source != translation.source:
        raise InvalidTranslationError("Translation source identity cannot be reconstructed")
    if len(expected.units) != len(translation.units):
        raise InvalidTranslationError("Translation unit count does not match reconstructed source")
    audited_units: list[dict[str, object]] = []
    for source_unit, target_unit in zip(expected.units, translation.units, strict=True):
        source_fields = source_unit.model_dump(exclude={"source_text", "target_text"})
        target_fields = target_unit.model_dump(exclude={"target_text", "target_status"})
        if source_fields != target_fields:
            raise InvalidTranslationError(
                f"Translation unit does not match reconstructed source: {target_unit.unit_id}"
            )
        audited_units.append(
            {
                "unit_id": target_unit.unit_id,
                "speaker_id": target_unit.speaker_id,
                "start_ms": target_unit.start_ms,
                "end_ms": target_unit.end_ms,
                "source_token_ids": list(target_unit.source_token_ids),
                "source_text": source_unit.source_text,
                "target_text": target_unit.target_text,
                "target_status": target_unit.target_status,
            }
        )
    return {
        "schema_version": "1.1",
        "translation": {
            "translation_id": str(translation.translation_id),
            "translation_number": translation.translation_number,
            "filename": translation_path.name,
            "sha256": sha256_file(translation_path),
        },
        "direction": translation.direction.model_dump(mode="json"),
        "style": translation.style.model_dump(mode="json", by_alias=True),
        "source": translation.source.model_dump(mode="json"),
        "dictionary": (
            translation.dictionary.model_dump(mode="json")
            if translation.dictionary is not None
            else None
        ),
        "units": audited_units,
        "statistics": {
            "unit_count": len(audited_units),
            "source_tokens": sum(len(unit.source_token_ids) for unit in translation.units),
            "target_tokens": translation.statistics.target_tokens,
            "intentionally_empty_units": translation.statistics.intentionally_empty_units,
        },
    }


def publish_translation_audit(
    audit: dict[str, object],
    *,
    output_directory: Path,
    lock_timeout_seconds: float = 0,
) -> tuple[Path, bool]:
    translation = audit["translation"]
    assert isinstance(translation, dict)
    filename = translation["filename"]
    assert isinstance(filename, str)
    path = output_directory / f"{filename.removesuffix('.json')}_audit.json"
    payload = (json.dumps(audit, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    written = publish_translation_bytes(
        path,
        payload,
        lock_timeout_seconds=lock_timeout_seconds,
    )
    return path, written
