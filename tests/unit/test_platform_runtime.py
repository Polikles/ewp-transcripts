"""Native ownership probes must never use Windows TerminateProcess via os.kill."""

from unittest.mock import Mock

import pytest

from ewp_transcripts import platform_runtime


@pytest.mark.parametrize(("exit_code", "alive"), [(259, True), (0, False), (17, False)])
def test_windows_owner_probe_reads_exit_code_without_sending_signal(monkeypatch, exit_code, alive):
    kernel = Mock()
    kernel.OpenProcess.return_value = 9876543210

    def exit_status(_handle, output):
        output._obj.value = exit_code
        return True

    kernel.GetExitCodeProcess.side_effect = exit_status
    monkeypatch.setattr(platform_runtime, "WINDOWS", True)
    monkeypatch.setattr(platform_runtime.ctypes, "WinDLL", Mock(return_value=kernel), raising=False)
    kill = Mock(side_effect=AssertionError("must not signal Windows process"))
    monkeypatch.setattr(platform_runtime.os, "kill", kill)
    assert platform_runtime.process_is_alive(123) is alive
    kernel.CloseHandle.assert_called_once_with(9876543210)
    kill.assert_not_called()


@pytest.mark.parametrize(("last_error", "alive"), [(87, False), (5, True)])
def test_windows_unknown_or_denied_owner_is_protected(monkeypatch, last_error, alive):
    kernel = Mock()
    kernel.OpenProcess.return_value = None
    monkeypatch.setattr(platform_runtime, "WINDOWS", True)
    monkeypatch.setattr(platform_runtime.ctypes, "WinDLL", Mock(return_value=kernel), raising=False)
    monkeypatch.setattr(
        platform_runtime.ctypes, "get_last_error", lambda: last_error, raising=False
    )
    assert platform_runtime.process_is_alive(123) is alive
    kernel.CloseHandle.assert_not_called()


def test_windows_directory_sync_never_opens_crt_directory_descriptor(tmp_path, monkeypatch):
    monkeypatch.setattr(platform_runtime, "WINDOWS", True)
    opener = Mock(side_effect=PermissionError("Windows CRT rejects directories"))
    monkeypatch.setattr(platform_runtime, "os", Mock(open=opener))
    platform_runtime.fsync_directory(tmp_path)
    opener.assert_not_called()


def test_posix_directory_sync_keeps_flush_and_closes_on_error(tmp_path, monkeypatch):
    monkeypatch.setattr(platform_runtime, "WINDOWS", False)
    runtime_os = Mock(O_RDONLY=0, O_DIRECTORY=1)
    runtime_os.open.return_value = 42
    runtime_os.fsync.side_effect = OSError("flush failed")
    monkeypatch.setattr(platform_runtime, "os", runtime_os)
    with pytest.raises(OSError, match="flush failed"):
        platform_runtime.fsync_directory(tmp_path)
    runtime_os.fsync.assert_called_once_with(42)
    runtime_os.close.assert_called_once_with(42)


@pytest.mark.parametrize("windows", [False, True])
@pytest.mark.parametrize("desktop", ["", "0", "1"])
def test_only_owned_windows_desktop_hides_helper_consoles(monkeypatch, windows, desktop):
    monkeypatch.setattr(platform_runtime, "WINDOWS", windows)
    monkeypatch.setenv("EWP_DESKTOP_MODE", desktop)
    assert platform_runtime.background_creation_flags() == (
        0x08000000 if windows and desktop == "1" else 0
    )
