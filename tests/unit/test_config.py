"""Tests for strict configuration loading and precedence."""

from pathlib import Path

import pytest

from ewp_transcripts.config import load_config
from ewp_transcripts.domain.enums import LanguageMode
from ewp_transcripts.domain.errors import InvalidConfigurationError

ROOT = Path(__file__).resolve().parents[2]


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_packaged_defaults_match_mvp_decisions(tmp_path: Path) -> None:
    config = load_config(cwd=tmp_path, home=tmp_path)

    assert config.general.language is LanguageMode.POLISH
    assert config.models.asr_model == "large-v2"
    assert config.models.asr_repository == "Systran/faster-whisper-large-v2"
    assert config.models.asr_revision == "f0fe81560cb8b68660e564f55dd99207059c092e"
    assert config.models.asr_snapshot_path.name == config.models.asr_revision
    assert config.models.alignment_snapshot_path.name == config.models.alignment_revision
    assert config.diarization.local_model_path.name == config.diarization.model_revision
    assert config.models.compute_type == "float16"
    assert config.models.batch_size == 4
    assert config.outputs.batch_output_directory_name == "output-ewp-transcripts"
    assert config.outputs.generate_txt is True
    assert config.outputs.generate_srt is False
    assert config.outputs.generate_vtt is False
    assert config.outputs.generate_segments_json is True
    assert config.revision.anchor_target_words == 200
    assert config.revision.anchor_target_speaker_blocks == 5
    assert config.revision.long_gap_warning_ms == 2000
    assert config.revision.generate_audit is False
    assert config.revision.editor == ""
    assert config.correction.target_tokens == 600
    assert config.correction.max_tokens == 800
    assert config.correction.context_tokens == 80
    assert config.correction.provider == ""
    assert config.correction.model == ""
    assert config.correction.endpoint == "http://127.0.0.1:1234/v1"
    assert config.correction.allow_remote_endpoint is False
    assert config.correction.output_mode == "json-schema"
    assert config.correction.prompt_id == "faithful-correction-v11"
    assert config.correction.timeout_seconds == 120
    assert config.correction.max_attempts == 3
    assert config.correction.temperature == 0
    assert config.quality.warn_only is True


def test_editable_example_exposes_correction_output_mode(tmp_path: Path) -> None:
    config = load_config(
        explicit_path=ROOT / "examples/config.example.toml",
        cwd=tmp_path,
        home=tmp_path,
    )

    assert config.correction.output_mode == "json-schema"


def test_documented_precedence_is_applied(tmp_path: Path) -> None:
    home = tmp_path / "home"
    project = tmp_path / "project"
    explicit = tmp_path / "selected.toml"
    _write(home / ".config/ewp-transcripts/config.toml", "[models]\nbatch_size = 2\n")
    _write(project / "transcriber.toml", "[models]\nbatch_size = 4\n")
    _write(explicit, "[models]\nbatch_size = 8\n")

    config = load_config(
        explicit_path=explicit,
        cwd=project,
        home=home,
        cli_overrides={"models": {"batch_size": 12}},
    )

    assert config.models.batch_size == 12


def test_unknown_key_is_rejected(tmp_path: Path) -> None:
    selected = _write(tmp_path / "selected.toml", "[general]\nunknown = true\n")

    with pytest.raises(InvalidConfigurationError, match="validation failed"):
        load_config(explicit_path=selected, cwd=tmp_path, home=tmp_path)


def test_invalid_threshold_order_is_rejected(tmp_path: Path) -> None:
    selected = _write(
        tmp_path / "selected.toml",
        "[grouping]\nduration_warning_ms = 501\nduration_error_ms = 500\n",
    )

    with pytest.raises(InvalidConfigurationError, match="validation failed"):
        load_config(explicit_path=selected, cwd=tmp_path, home=tmp_path)


def test_invalid_revision_anchor_size_is_rejected(tmp_path: Path) -> None:
    selected = _write(tmp_path / "selected.toml", "[revision]\nanchor_target_words = 0\n")

    with pytest.raises(InvalidConfigurationError, match="validation failed"):
        load_config(explicit_path=selected, cwd=tmp_path, home=tmp_path)


def test_invalid_correction_chunk_order_is_rejected(tmp_path: Path) -> None:
    selected = _write(
        tmp_path / "selected.toml",
        "[correction]\ntarget_tokens = 20\nmax_tokens = 19\n",
    )

    with pytest.raises(InvalidConfigurationError, match="validation failed"):
        load_config(explicit_path=selected, cwd=tmp_path, home=tmp_path)


def test_configured_correction_provider_requires_model(tmp_path: Path) -> None:
    selected = _write(tmp_path / "selected.toml", '[correction]\nprovider = "lm-studio"\n')

    with pytest.raises(InvalidConfigurationError, match="validation failed"):
        load_config(explicit_path=selected, cwd=tmp_path, home=tmp_path)


def test_following_symlinks_cannot_be_enabled_in_mvp(tmp_path: Path) -> None:
    selected = _write(tmp_path / "selected.toml", "[input]\nfollow_symlinks = true\n")

    with pytest.raises(InvalidConfigurationError, match="validation failed"):
        load_config(explicit_path=selected, cwd=tmp_path, home=tmp_path)


def test_missing_explicit_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(InvalidConfigurationError, match="does not exist"):
        load_config(
            explicit_path=tmp_path / "missing.toml",
            cwd=tmp_path,
            home=tmp_path,
        )


def test_snapshot_path_must_end_with_configured_revision(tmp_path: Path) -> None:
    selected = _write(
        tmp_path / "selected.toml",
        '[models]\nasr_snapshot_path = "/models/wrong-revision"\n',
    )

    with pytest.raises(InvalidConfigurationError, match="validation failed"):
        load_config(explicit_path=selected, cwd=tmp_path, home=tmp_path)


def test_diarization_path_must_end_with_configured_revision(tmp_path: Path) -> None:
    selected = _write(
        tmp_path / "selected.toml",
        '[diarization]\nlocal_model_path = "/models/wrong-revision"\n',
    )

    with pytest.raises(InvalidConfigurationError, match="validation failed"):
        load_config(explicit_path=selected, cwd=tmp_path, home=tmp_path)
