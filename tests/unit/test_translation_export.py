"""Tests for deterministic translation TXT export."""

import json
from pathlib import Path

from ewp_transcripts.domain.translation import TranslationDirection, load_transcript_translation
from ewp_transcripts.translation_export import (
    TranslationExportFormat,
    build_translation_subtitle_cues,
    export_translation,
    export_translation_text,
    render_translation_text,
)

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/translation.example.json"


def test_render_translation_text_uses_stable_speaker_blocks() -> None:
    translation = load_transcript_translation(EXAMPLE)

    rendered = render_translation_text(translation)

    assert rendered == (
        "speaker_001:\nWitamy w kolejnym odcinku.\n\n"
        "speaker_002:\nDzisiaj rozmawiamy o transkrypcji.\n"
    )


def test_export_translation_text_writes_then_skips_identical(tmp_path: Path) -> None:
    first = export_translation_text(EXAMPLE, output_directory=tmp_path)
    second = export_translation_text(EXAMPLE, output_directory=tmp_path)

    expected = tmp_path / "S01E01_pl_translation_001.txt"
    provenance = tmp_path / "S01E01_pl_translation_001.provenance.json"
    assert first.written == (expected, provenance)
    assert second.skipped == (expected, provenance)
    assert expected.read_text(encoding="utf-8").startswith("speaker_001:")
    assert json.loads(provenance.read_text(encoding="utf-8"))["dictionary"] is None


def test_translation_subtitles_stay_inside_unit_timing_and_render(tmp_path: Path) -> None:
    translation = load_transcript_translation(EXAMPLE)

    cues = build_translation_subtitle_cues(translation)
    outcome = export_translation(
        EXAMPLE,
        formats=(TranslationExportFormat.SRT, TranslationExportFormat.VTT),
        output_directory=tmp_path,
    )

    assert cues[0].start_ms == translation.units[0].start_ms
    assert cues[0].end_ms <= translation.units[0].end_ms
    assert cues[-1].end_ms == translation.units[-1].end_ms
    assert {path.suffix for path in outcome.written} == {".srt", ".vtt", ".json"}
    assert "00:00:01,240 --> 00:00:03,900" in next(
        path for path in outcome.written if path.suffix == ".srt"
    ).read_text(encoding="utf-8")


def test_translation_html_uses_target_language_text_and_unit_timing(tmp_path: Path) -> None:
    outcome = export_translation(
        EXAMPLE,
        formats=(TranslationExportFormat.HTML,),
        output_directory=tmp_path,
    )

    html_path = tmp_path / "S01E01_pl_translation_001.html"
    assert html_path in outcome.written
    rendered = html_path.read_text(encoding="utf-8")
    assert rendered.startswith('<section class="ewp-transcript" lang="pl">')
    assert "Witamy w kolejnym odcinku." in rendered
    assert 'data-start-ms="1240" data-end-ms="3900"' in rendered
    assert 'data-speaker-id="speaker_001"' in rendered


def test_english_quote_punctuation_is_preserved_in_text_and_subtitles() -> None:
    translation = load_transcript_translation(EXAMPLE)
    units = (
        translation.units[0].model_copy(update={"target_text": 'He said "This works."'}),
        translation.units[1].model_copy(update={"target_text": "Then he left."}),
    )
    changed = translation.model_copy(
        update={
            "direction": TranslationDirection(source_language="pl", target_language="en"),
            "units": units,
            "statistics": translation.statistics.model_copy(update={"target_tokens": 7}),
        }
    )
    changed = type(translation).model_validate(changed.model_dump())

    text = render_translation_text(changed)
    cues = build_translation_subtitle_cues(changed)

    assert 'He said "This works."' in text
    assert 'He said "This works."' in " ".join(cues[0].lines)


def test_intentionally_empty_units_are_omitted_from_derived_exports(tmp_path: Path) -> None:
    translation = load_transcript_translation(EXAMPLE)
    omitted = translation.units[0].model_copy(
        update={"target_text": "", "target_status": "intentionally_empty"}
    )
    changed = type(translation).model_validate(
        translation.model_dump()
        | {
            "schema_version": "1.1",
            "units": (omitted, translation.units[1]),
            "statistics": translation.statistics.model_copy(
                update={"target_tokens": 4, "intentionally_empty_units": 1}
            ),
        }
    )

    assert "Witamy" not in render_translation_text(changed)
    assert len(build_translation_subtitle_cues(changed)) == 1

    artifact = tmp_path / "translation.json"
    artifact.write_text(changed.model_dump_json(), encoding="utf-8")
    output = tmp_path / "exports"
    output.mkdir()
    export_translation(
        artifact,
        formats=(TranslationExportFormat.HTML,),
        output_directory=output,
    )
    rendered = (output / "S01E01_pl_translation_001.html").read_text(encoding="utf-8")
    assert "Witamy" not in rendered
