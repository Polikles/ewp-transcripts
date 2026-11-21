"""Media inspection, group compatibility validation, and episode identity."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from hashlib import sha256
from pathlib import Path

from ewp_transcripts.config import ChannelsConfig, QualityConfig
from ewp_transcripts.domain import (
    ApplicationWarning,
    AudioStream,
    ChannelMetrics,
    EpisodeCandidate,
    EpisodeInspection,
    InspectedSource,
    InspectionResult,
    MediaProbeResult,
    WarningCode,
)
from ewp_transcripts.domain.enums import ChannelMode
from ewp_transcripts.domain.errors import (
    DurationMismatchError,
    InvalidConfigurationError,
    MultipleAudioStreamsError,
    SampleRateMismatchError,
)
from ewp_transcripts.media import probe_media
from ewp_transcripts.media.channels import classify_channels
from ewp_transcripts.media.quality import quality_warnings

MediaProbe = Callable[[Path], MediaProbeResult]
ChannelAnalyzer = Callable[[Path], ChannelMetrics]


def _select_audio_stream(
    result: MediaProbeResult,
    selected_streams: Mapping[Path, int],
) -> AudioStream:
    requested = selected_streams.get(result.path)
    if requested is not None:
        for stream in result.audio_streams:
            if stream.index == requested:
                return stream
        raise MultipleAudioStreamsError(
            f"Selected audio stream {requested} is unavailable: {result.path}"
        )
    if len(result.audio_streams) != 1:
        raise MultipleAudioStreamsError(
            f"Input has multiple audio streams and requires an explicit selection: {result.path}. "
            "Choose its stream in GUI audio options. Export the intended audio track "
            "to a separate file, "
            "then inspect and process that file."
        )
    return result.audio_streams[0]


def calculate_episode_signature(
    job_id: str,
    sources: tuple[InspectedSource, ...],
) -> str:
    """Hash the canonical ordered source descriptors used by one episode."""

    descriptor = {
        "job_id": job_id,
        "sources": [
            {
                "channel_mode": source.channel_mode.value,
                "sha256": source.fingerprint.sha256,
                "speaker_id": source.speaker_id,
                "speaker_label": source.speaker_label,
                "stream_index": source.stream.index,
                **({"speaker_source": "explicit"} if source.speaker_source == "explicit" else {}),
            }
            for source in sources
        ],
    }
    serialized = json.dumps(
        descriptor,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(serialized).hexdigest()


def apply_explicit_speaker_labels(
    inspection: InspectionResult,
    *,
    speaker_label: str | None = None,
    speaker_map: dict[str, str] | None = None,
) -> InspectionResult:
    """Apply explicit labels before planning so signatures retain their provenance."""

    mapping = speaker_map or {}
    if speaker_label is not None and mapping:
        raise InvalidConfigurationError("--speaker and --speaker-map cannot be combined")
    if speaker_label is not None:
        if len(inspection.episodes) != 1 or len(inspection.episodes[0].sources) != 1:
            raise InvalidConfigurationError("--speaker requires exactly one source")
        source = inspection.episodes[0].sources[0]
        if source.channel_classification.processing_mode is ChannelMode.SPLIT_SPEAKERS:
            raise InvalidConfigurationError("--speaker cannot label a split-speaker source")
        mapping = {source.fingerprint.filename: speaker_label}
    if not mapping:
        return inspection

    source_counts: dict[str, int] = {}
    for episode in inspection.episodes:
        for source in episode.sources:
            filename = source.fingerprint.filename
            source_counts[filename] = source_counts.get(filename, 0) + 1
    unknown = sorted(set(mapping) - set(source_counts))
    if unknown:
        raise InvalidConfigurationError(f"Speaker map source was not found: {unknown[0]}")
    ambiguous = sorted(name for name in mapping if source_counts[name] != 1)
    if ambiguous:
        raise InvalidConfigurationError(f"Speaker map source is ambiguous: {ambiguous[0]}")

    episodes: list[EpisodeInspection] = []
    for episode in inspection.episodes:
        sources: list[InspectedSource] = []
        for source in episode.sources:
            label = mapping.get(source.fingerprint.filename)
            if label is not None:
                if source.channel_classification.processing_mode is ChannelMode.SPLIT_SPEAKERS:
                    raise InvalidConfigurationError(
                        "--speaker-map cannot assign one label to a split-speaker source"
                    )
                source = source.model_copy(
                    update={"speaker_label": label, "speaker_source": "explicit"}
                )
            sources.append(source)
        updated_sources = tuple(sources)
        episodes.append(
            episode.model_copy(
                update={
                    "sources": updated_sources,
                    "episode_signature_sha256": calculate_episode_signature(
                        episode.job_id, updated_sources
                    ),
                }
            )
        )
    return inspection.model_copy(update={"episodes": tuple(episodes)})


def inspect_episode(
    episode: EpisodeCandidate,
    *,
    probe: MediaProbe = probe_media,
    selected_streams: Mapping[Path, int] | None = None,
    channel_analyzer: ChannelAnalyzer | None = None,
    channels_config: ChannelsConfig | None = None,
    quality_config: QualityConfig | None = None,
    duration_warning_ms: int = 100,
    duration_error_ms: int = 500,
    allow_duration_mismatch: bool = False,
) -> EpisodeInspection:
    """Probe and validate one candidate without modifying source files."""

    if duration_warning_ms < 0 or duration_error_ms < duration_warning_ms:
        raise ValueError("invalid duration thresholds")
    stream_selection = selected_streams or {}
    effective_channels_config = channels_config or ChannelsConfig()
    effective_quality_config = quality_config or QualityConfig()
    inspected: list[InspectedSource] = []
    channel_warnings: list[ApplicationWarning] = []
    for position, grouped_source in enumerate(episode.sources, start=1):
        result = probe(grouped_source.fingerprint.path)
        if any(character.isspace() for character in grouped_source.fingerprint.filename):
            channel_warnings.append(
                ApplicationWarning(
                    code=WarningCode.INPUT_FILENAME_WHITESPACE,
                    message=(
                        "The source filename contains whitespace; it is accepted unchanged. "
                        "Quote the complete path in CLI commands."
                    ),
                    context={"filename": grouped_source.fingerprint.filename},
                )
            )
        stream = _select_audio_stream(result, stream_selection)
        metrics = channel_analyzer(result.path) if channel_analyzer is not None else None
        classification = classify_channels(
            original_channels=stream.channels,
            metrics=metrics,
            config=effective_channels_config,
        )
        channel_warnings.extend(classification.warnings)
        if metrics is not None:
            channel_warnings.extend(
                quality_warnings(
                    metrics,
                    original_channels=stream.channels,
                    config=effective_quality_config,
                )
            )
        inspected.append(
            InspectedSource(
                fingerprint=grouped_source.fingerprint,
                media_type="video" if result.has_video else "audio",
                stream=stream,
                duration_ms=(
                    stream.duration_ms if stream.duration_ms is not None else result.duration_ms
                ),
                channel_mode=classification.processing_mode,
                channel_metrics=metrics,
                channel_classification=classification,
                speaker_id=f"speaker_{position:03d}",
                speaker_label=grouped_source.speaker_label or stream.title,
                speaker_source=(
                    grouped_source.speaker_source
                    if grouped_source.speaker_label is not None
                    else "channel_metadata"
                    if stream.title is not None
                    else grouped_source.speaker_source
                ),
            )
        )

    sample_rates = {source.stream.sample_rate_hz for source in inspected}
    if len(sample_rates) != 1:
        raise SampleRateMismatchError(
            f"Grouped sources have different sample rates: {episode.job_id}"
        )

    durations = [source.duration_ms for source in inspected]
    duration_difference = max(durations) - min(durations)
    if duration_difference > duration_error_ms and not allow_duration_mismatch:
        raise DurationMismatchError(
            f"Grouped-source duration difference exceeds {duration_error_ms} ms: {episode.job_id}"
        )

    warnings: list[ApplicationWarning] = list(channel_warnings)
    if duration_difference > duration_warning_ms:
        warnings.append(
            ApplicationWarning(
                code=WarningCode.INPUT_DURATION_MISMATCH,
                message="Grouped sources have different durations.",
                context={
                    "difference_ms": duration_difference,
                    "override_used": duration_difference > duration_error_ms,
                },
            )
        )

    sources = tuple(inspected)
    return EpisodeInspection(
        job_id=episode.job_id,
        episode_signature_sha256=calculate_episode_signature(episode.job_id, sources),
        duration_ms=max(durations),
        sample_rate_hz=next(iter(sample_rates)),
        sources=sources,
        warnings=tuple(warnings),
    )
