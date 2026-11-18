"""Private runtime is optional, lazy and fails visibly when incomplete."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from ewp_transcripts.engines import ffmpeg_compat


def test_no_private_runtime_keeps_system_loading(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("EWP_FFMPEG_PREFIX", str(tmp_path / "absent"))
    load = Mock()
    monkeypatch.setattr(ffmpeg_compat.ctypes, "CDLL", load)
    ffmpeg_compat.prepare_speech_libraries()
    load.assert_not_called()


def test_private_runtime_is_loaded_once_and_before_consumers(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("EWP_FFMPEG_PREFIX", str(tmp_path))
    loaded = []

    def load(path, *, mode):
        loaded.append(Path(path).name)
        assert mode == ffmpeg_compat.ctypes.RTLD_GLOBAL
        return object()

    monkeypatch.setattr(ffmpeg_compat.ctypes, "CDLL", load)
    ffmpeg_compat.prepare_speech_libraries()
    ffmpeg_compat.prepare_speech_libraries()
    assert len(loaded) == len(set(loaded)) == 7
    assert loaded.index("libavutil.so.59") < loaded.index("libavcodec.so.61")
    assert loaded.index("libavcodec.so.61") < loaded.index("libavformat.so.61")


def test_broken_private_install_has_repair_guidance(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("EWP_FFMPEG_PREFIX", str(tmp_path))
    monkeypatch.setattr(ffmpeg_compat.ctypes, "CDLL", Mock(side_effect=OSError("missing library")))
    with pytest.raises(RuntimeError, match="repair-dependencies.sh"):
        ffmpeg_compat.prepare_speech_libraries()


@pytest.mark.parametrize("data_home", ["", "relative-directory"])
def test_unset_or_relative_xdg_path_never_installs_into_checkout(monkeypatch, data_home) -> None:
    monkeypatch.delenv("EWP_FFMPEG_PREFIX", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", data_home)
    assert ffmpeg_compat.compatibility_prefix().is_relative_to(Path.home() / ".local/share")
