"""Strict parser and deterministic writer for the ``EWP-REVIEW 1`` text format."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from ewp_transcripts.domain.errors import InvalidReviewError
from ewp_transcripts.domain.review import (
    ReviewAnchor,
    ReviewExtensionHeader,
    ReviewHeader,
    ReviewSpeakerBlock,
    TranscriptReview,
)

MAGIC = "# EWP-REVIEW 1"
_HEADER = re.compile(r"^# (?P<key>[a-z_][a-z0-9_]*): (?P<value>.+)$")
_ANCHOR = re.compile(r"^@@ anchor (?P<first>word_[0-9]{6,})\.\.(?P<last>word_[0-9]{6,})$")
_SPEAKER = re.compile(r"^@@ speaker (?P<speaker>speaker_[0-9]{3,})$")
_REQUIRED_HEADERS = (
    "job_id",
    "base_result_file",
    "base_result_sha256",
    "base_result_schema_version",
    "base_result_version",
    "language",
    "generated_at",
    "application_version",
)
_SOURCE_REVISION_HEADERS = (
    "source_revision_id",
    "source_revision_sha256",
    "source_revision_number",
)
_OPTIONAL_HEADERS = (*_SOURCE_REVISION_HEADERS, "speaker_labels")


def _invalid(message: str, *, code: str = "REVISION_REVIEW_INVALID") -> InvalidReviewError:
    return InvalidReviewError(code, message)


def _parse_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise _invalid("generated_at must be an RFC 3339 timestamp") from error
    if parsed.tzinfo is None:
        raise _invalid("generated_at must contain an explicit timezone")
    return parsed


def _parse_positive_integer(key: str, value: str) -> int:
    if not value.isdigit() or int(value) < 1:
        raise _invalid(f"{key} must be a positive integer")
    return int(value)


def _parse_speaker_labels(value: str | None) -> dict[str, str]:
    if value is None:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise _invalid("speaker_labels must be one JSON object") from error
    if not isinstance(parsed, dict) or not all(
        isinstance(key, str) and isinstance(label, str) for key, label in parsed.items()
    ):
        raise _invalid("speaker_labels must map speaker IDs to labels")
    return parsed


def _parse_header(lines: list[str]) -> ReviewHeader:
    values: dict[str, str] = {}
    extensions: list[ReviewExtensionHeader] = []
    allowed = set(_REQUIRED_HEADERS) | set(_OPTIONAL_HEADERS)
    for line in lines:
        match = _HEADER.fullmatch(line)
        if match is None:
            raise _invalid(f"Malformed review header line: {line!r}")
        key = match.group("key")
        value = match.group("value")
        if not value.isprintable():
            raise _invalid(f"Review header {key!r} contains non-printable characters")
        if key in values:
            raise _invalid(f"Duplicate review header: {key}")
        if key not in allowed and not key.startswith("x_"):
            raise _invalid(f"Unknown review header: {key}")
        values[key] = value

    missing = [key for key in _REQUIRED_HEADERS if key not in values]
    if missing:
        raise _invalid(f"Missing required review header: {missing[0]}")
    source_present = [key in values for key in _SOURCE_REVISION_HEADERS]
    if any(source_present) and not all(source_present):
        raise _invalid("Source revision headers must be provided together")
    for key in sorted(key for key in values if key.startswith("x_")):
        extensions.append(ReviewExtensionHeader(key=key, value=values[key]))

    try:
        return ReviewHeader(
            job_id=values["job_id"],
            base_result_file=values["base_result_file"],
            base_result_sha256=values["base_result_sha256"],
            base_result_schema_version=values["base_result_schema_version"],
            base_result_version=_parse_positive_integer(
                "base_result_version", values["base_result_version"]
            ),
            language=values["language"],  # type: ignore[arg-type]
            generated_at=_parse_datetime(values["generated_at"]),
            application_version=values["application_version"],
            source_revision_id=(UUID(values["source_revision_id"]) if source_present[0] else None),
            source_revision_sha256=values.get("source_revision_sha256"),
            source_revision_number=(
                _parse_positive_integer("source_revision_number", values["source_revision_number"])
                if source_present[2]
                else None
            ),
            speaker_labels=_parse_speaker_labels(values.get("speaker_labels")),
            extensions=tuple(extensions),
        )
    except (ValidationError, ValueError) as error:
        raise _invalid("Review header contains an invalid value") from error


def _normalized_text(lines: list[str]) -> str:
    unescaped = [line[1:] if line.startswith("@@@ ") else line for line in lines]
    return " ".join(" ".join(unescaped).split())


def _parse_body(lines: list[str], *, first_line_number: int = 1) -> tuple[ReviewAnchor, ...]:
    anchors: list[ReviewAnchor] = []
    current_range: tuple[str, str] | None = None
    blocks: list[ReviewSpeakerBlock] = []
    speaker_id: str | None = None
    text_lines: list[str] = []

    def finish_block() -> None:
        nonlocal speaker_id, text_lines
        if speaker_id is not None:
            blocks.append(
                ReviewSpeakerBlock(speaker_id=speaker_id, text=_normalized_text(text_lines))
            )
        speaker_id = None
        text_lines = []

    def finish_anchor() -> None:
        nonlocal current_range, blocks
        if current_range is None:
            return
        finish_block()
        if not blocks:
            raise _invalid("Every review anchor requires a speaker directive")
        anchors.append(
            ReviewAnchor(
                first_word_id=current_range[0],
                last_word_id=current_range[1],
                speaker_blocks=tuple(blocks),
            )
        )
        current_range = None
        blocks = []

    for line_number, line in enumerate(lines, start=first_line_number):
        anchor_match = _ANCHOR.fullmatch(line)
        if anchor_match is not None:
            finish_anchor()
            current_range = (anchor_match.group("first"), anchor_match.group("last"))
            continue
        if line.startswith("@@ anchor "):
            raise _invalid(
                f"Malformed review anchor directive at line {line_number}",
                code="REVISION_ANCHOR_INVALID",
            )
        speaker_match = _SPEAKER.fullmatch(line)
        if speaker_match is not None:
            if current_range is None:
                raise _invalid(
                    f"Speaker directive appears before the first anchor at line {line_number}"
                )
            finish_block()
            speaker_id = speaker_match.group("speaker")
            continue
        if line.startswith("@@ speaker "):
            raise _invalid(
                f"Malformed review speaker directive at line {line_number}",
                code="REVISION_SPEAKER_INVALID",
            )
        if line.startswith("@@ "):
            raise _invalid(f"Unknown review directive at line {line_number}: {line}")
        if current_range is None:
            if line:
                raise _invalid(
                    f"Transcript text appears before the first anchor at line {line_number}"
                )
            continue
        if speaker_id is None:
            if line:
                raise _invalid(
                    f"Transcript text appears before a speaker directive at line {line_number}"
                )
            continue
        text_lines.append(line)

    finish_anchor()
    if not anchors:
        raise _invalid("Review file must contain at least one anchor")
    return tuple(anchors)


def parse_review(text: str) -> TranscriptReview:
    """Parse and structurally validate one complete review string."""

    if "\x00" in text:
        raise _invalid("Review file contains a NUL character")
    lines = text.splitlines()
    if not lines or lines[0] != MAGIC:
        raise _invalid(f"Review file must begin with {MAGIC!r}")
    try:
        header_end = lines.index("", 1)
    except ValueError as error:
        raise _invalid("Review header must end with a blank line") from error
    header = _parse_header(lines[1:header_end])
    anchors = _parse_body(lines[header_end + 1 :], first_line_number=header_end + 2)
    return TranscriptReview(format_version=1, header=header, anchors=anchors)


def load_review(path: Path) -> TranscriptReview:
    """Read one UTF-8 review file and expose controlled format errors."""

    try:
        return parse_review(path.read_text(encoding="utf-8"))
    except InvalidReviewError:
        raise
    except (OSError, UnicodeError) as error:
        raise _invalid(f"Cannot read transcript review: {path}") from error


def _timestamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def render_review(review: TranscriptReview) -> str:
    """Render a deterministic LF-terminated review representation."""

    header = review.header
    lines = [
        MAGIC,
        f"# job_id: {header.job_id}",
        f"# base_result_file: {header.base_result_file}",
        f"# base_result_sha256: {header.base_result_sha256}",
        f"# base_result_schema_version: {header.base_result_schema_version}",
        f"# base_result_version: {header.base_result_version}",
        f"# language: {header.language}",
        f"# generated_at: {_timestamp(header.generated_at)}",
        f"# application_version: {header.application_version}",
    ]
    if header.source_revision_id is not None:
        lines.extend(
            (
                f"# source_revision_id: {header.source_revision_id}",
                f"# source_revision_sha256: {header.source_revision_sha256}",
                f"# source_revision_number: {header.source_revision_number}",
            )
        )
    if header.speaker_labels:
        lines.append(
            "# speaker_labels: "
            + json.dumps(header.speaker_labels, ensure_ascii=False, separators=(",", ":"))
        )
    lines.extend(
        f"# {item.key}: {item.value}" for item in sorted(header.extensions, key=lambda x: x.key)
    )
    lines.append("")
    for anchor_index, anchor in enumerate(review.anchors):
        if anchor_index:
            lines.append("")
        lines.append(f"@@ anchor {anchor.first_word_id}..{anchor.last_word_id}")
        for block_index, block in enumerate(anchor.speaker_blocks):
            if block_index:
                lines.append("")
            lines.append(f"@@ speaker {block.speaker_id}")
            lines.append("")
            content = f"@{block.text}" if block.text.startswith("@@ ") else block.text
            if content:
                lines.append(content)
    return "\n".join(lines) + "\n"
