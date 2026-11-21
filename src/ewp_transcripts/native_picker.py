"""Optional desktop file picker, with direct-entry fallback and no CLI shell interpolation."""

from __future__ import annotations

import base64
import platform
import shutil
import subprocess
import sys


def select_native_file() -> str | None:
    commands: list[list[str]] = []
    if sys.platform == "win32" or "microsoft" in platform.release().lower():
        powershell = shutil.which("powershell.exe")
        if powershell:
            script = (
                "[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false); "
                "Add-Type -AssemblyName System.Windows.Forms; "
                "[System.Windows.Forms.Application]::EnableVisualStyles(); "
                "$d = New-Object System.Windows.Forms.OpenFileDialog; "
                "$d.Multiselect = $false; $d.CheckFileExists = $true; "
                "if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) "
                "{ [Console]::Out.Write($d.FileName) } else { exit 3 }"
            )
            encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
            commands.append([powershell, "-NoProfile", "-STA", "-EncodedCommand", encoded])
    for tool, args in [
        ("zenity", ["--file-selection"]),
        ("kdialog", ["--getopenfilename", "."]),
        ("yad", ["--file-selection"]),
    ]:
        executable = shutil.which(tool)
        if executable:
            commands.append([executable, *args])
    for command in commands:
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, encoding="utf-8", check=False, timeout=600
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if result.returncode in {1, 3}:
            return None
        if result.returncode == 0:
            return result.stdout.strip() or None
    raise ValueError("Native file picker is unavailable. Enter the path directly.")
