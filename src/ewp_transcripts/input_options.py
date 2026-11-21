"""Strict, portable recording identities and selected audio-stream descriptors."""

from __future__ import annotations

import re
from collections.abc import Iterable


def recording_identity(raw: object) -> str | None:
    if raw in (None, ""):
        return None
    if (
        not isinstance(raw, str)
        or not re.fullmatch(r'[^\x00-\x1f<>:"/\\|?*]{1,100}', raw)
        or raw in {".", ".."}
        or raw[-1] in {".", " "}
        or raw.split(".", 1)[0].upper()
        in {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *(f"COM{x}" for x in range(1, 10)),
            *(f"LPT{x}" for x in range(1, 10)),
        }
    ):
        raise ValueError(
            "Recording ID must be a portable filename without path separators "
            "or reserved characters"
        )
    return raw


def stream_choices(raw: object, known: Iterable[str] | None = None) -> dict[str, int]:
    if (
        not isinstance(raw, dict)
        or len(raw) > 6
        or any(
            not isinstance(path, str)
            or not path
            or len(path) > 4096
            or type(index) is not int
            or not 0 <= index <= 10000
            for path, index in raw.items()
        )
    ):
        raise ValueError("Audio stream selection is invalid")
    if known is not None and not set(raw).issubset(set(known)):
        raise ValueError("Audio stream selection refers to a different source")
    return dict(raw)
