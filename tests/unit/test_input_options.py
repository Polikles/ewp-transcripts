"""Selected source descriptors and IDs remain exact and portable across systems."""

import pytest

from ewp_transcripts.input_options import recording_identity, stream_choices


@pytest.mark.parametrize(
    "identity", ["../out", "a/b", "a\\b", "C:drive", "NUL.txt", "COM1", "a.", "a "]
)
def test_recording_id_rejects_unsafe_or_windows_reserved_components(identity):
    with pytest.raises(ValueError):
        recording_identity(identity)


def test_recording_id_preserves_unicode_and_original_names():
    assert recording_identity("S01E01 Żółć-EN") == "S01E01 Żółć-EN"
    assert recording_identity("") is None


@pytest.mark.parametrize(
    "selection", [{"source": True}, {"source": -1}, {"source": "2"}, {"other": 2}]
)
def test_stream_selection_rejects_ambiguous_values_and_foreign_sources(selection):
    with pytest.raises(ValueError):
        stream_choices(selection, ["source"])
