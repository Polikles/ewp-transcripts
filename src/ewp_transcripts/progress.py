"""Optional, failure-isolated pipeline events and local approximate runtime estimates."""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import statistics
import subprocess
import threading
import time
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal


@dataclass(frozen=True)
class ProgressEvent:
    phase: str
    state: Literal["started", "completed", "planned"]
    stream_index: int = 1
    stream_count: int = 1
    duration_ms: int = 0
    media_duration_ms: int = 0
    phases: tuple[str, ...] = ()


ProgressObserver = Callable[[ProgressEvent], None]


def emit_progress(
    observer: ProgressObserver | None,
    phase: str,
    state: Literal["started", "completed", "planned"],
    **details: Any,
) -> None:
    if observer is not None:
        with suppress(Exception):
            observer(ProgressEvent(phase, state, **details))


# First-run phase weights are explicit heuristics, not measured percent of audio decoded.
PHASE_WEIGHTS = {
    "inspect": 1,
    "plan": 1,
    "prepare_audio": 3,
    "transcribe": 55,
    "align": 22,
    "normalize": 1,
    "diarize": 20,
    "reconcile_speakers": 2,
    "compose": 2,
    "publish": 1,
    "export": 1,
    "cleanup": 1,
}


@lru_cache(maxsize=1)
def _gpu_identity() -> str:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,uuid,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else "unavailable"
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def runtime_profile(config: Any, streams: int, topology: str) -> str:
    """Separate estimates across hosts/hardware/runtime/config without retaining host names."""
    cpu = ""
    with suppress(OSError):
        cpu = next(
            (
                line
                for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")
            ),
            "",
        )
    descriptor = [
        "phase-estimate-v1",
        config.speech.model_dump(mode="json"),
        platform.node(),
        platform.release(),
        platform.machine(),
        cpu,
        platform.python_version(),
        _gpu_identity() if config.models.device.startswith("cuda") else "cpu",
        config.models.model_dump(mode="json"),
        config.general.language.value,
        str(config.diarization.speaker_count),
        streams,
        topology,
    ]
    return hashlib.sha256(json.dumps(descriptor, sort_keys=True).encode()).hexdigest()


MIN_ETA_RUNS = 3


class ProgressHistory:
    """Bounded content-free timing cache. Failure to read/write it never fails a job."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.data: dict[str, dict[str, list[float]]] = {}
        self.lock = threading.Lock()
        self.counts: dict[str, int] = {}
        if path is not None:
            try:
                raw = json.loads(path.read_text())
                if isinstance(raw, dict) and len(raw) <= 32:
                    for profile, phases in raw.items():
                        if len(profile) != 64 or not isinstance(phases, dict):
                            continue
                        runs = phases.get("_runs", [0])
                        if isinstance(runs, list) and runs and type(runs[0]) is int:
                            self.counts[profile] = max(0, min(1000000, runs[0]))
                        self.data[profile] = {
                            phase: [
                                float(value)
                                for value in values[-12:]
                                if isinstance(value, (int, float))
                                and math.isfinite(value)
                                and 0 < value < 1e6
                            ]
                            for phase, values in phases.items()
                            if phase in PHASE_WEIGHTS and isinstance(values, list)
                        }
            except (OSError, ValueError, TypeError):
                self.data = {}

    def samples(self, profile: str) -> dict[str, list[float]]:
        with self.lock:
            return {key: list(values) for key, values in self.data.get(profile, {}).items()}

    def completed_runs(self, profile: str) -> int:
        with self.lock:
            return self.counts.get(profile, 0)

    def record(self, profile: str, factors: dict[str, list[float]]) -> None:
        with self.lock:
            self.counts[profile] = self.counts.get(profile, 0) + 1
            phases = self.data.setdefault(profile, {})
            for phase, values in factors.items():
                phases[phase] = [*phases.get(phase, []), *values][-12:]
            self.data = dict(list(self.data.items())[-32:])
            self.counts = {key: self.counts.get(key, 0) for key in self.data}
            if self.path is not None:
                temporary = self.path.with_suffix(".tmp")
                try:
                    self.path.parent.mkdir(parents=True, exist_ok=True)
                    with temporary.open("w", encoding="utf-8") as handle:
                        os.chmod(temporary, 0o600)
                        json.dump(
                            {
                                key: {**value, "_runs": [self.counts.get(key, 0)]}
                                for key, value in self.data.items()
                            },
                            handle,
                        )
                    temporary.replace(self.path)
                except OSError:
                    pass


class RuntimeProgress:
    """Monotonic-clock snapshots with event-based completion and calibrated ETA fallback."""

    def __init__(
        self, history: ProgressHistory, profile: str, *, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.history, self.profile, self.clock = history, profile, clock
        self.started = self.phase_started = clock()
        self.lock = threading.RLock()
        self.phase = "inspect"
        self.current = "inspect"
        self.work: tuple[str, ...] = ()
        self.completed: set[str] = set()
        self.duration = 1.0
        self.samples = history.samples(profile)
        self.observed: dict[str, list[float]] = {}
        self.stream_index = self.stream_count = 1
        self.finished: bool | None = None
        self.ended: float | None = None
        self.max_percent = 0

    def __call__(self, event: ProgressEvent) -> None:
        with self.lock:
            if event.state == "planned":
                self.work = event.phases
                self.profile = hashlib.sha256(
                    (self.profile + repr(event.phases)).encode()
                ).hexdigest()
                self.samples = self.history.samples(self.profile)
                self.duration = max(1.0, event.media_duration_ms / 1000)
                self.stream_count = event.stream_count
                return
            key = (
                f"{event.phase}:{event.stream_index}"
                if event.phase
                in {
                    "prepare_audio",
                    "transcribe",
                    "align",
                    "normalize",
                    "diarize",
                    "reconcile_speakers",
                }
                else event.phase
            )
            if event.state == "started":
                self.phase, self.current, self.phase_started = event.phase, key, self.clock()
                self.stream_index, self.stream_count = event.stream_index, event.stream_count
            else:
                self.completed.add(key)
                if event.phase in PHASE_WEIGHTS:
                    self.observed.setdefault(event.phase, []).append(
                        max(0.001, event.duration_ms / 1000)
                    )

    def finish(self, success: bool) -> None:
        with self.lock:
            self.finished = success
            self.ended = self.clock()
            if success and self.work and all(key in self.completed for key in self.work):
                self.history.record(
                    self.profile,
                    {
                        phase: [value / self.duration for value in values]
                        for phase, values in self.observed.items()
                    },
                )

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            now = self.ended if self.ended is not None else self.clock()
            elapsed = max(0, now - self.started)
            phase_elapsed = max(0, now - self.phase_started)

            def weight(key: str) -> int:
                return PHASE_WEIGHTS.get(key.split(":")[0], 1)

            total = sum(weight(key) for key in self.work)
            done = float(sum(weight(key) for key in self.work if key in self.completed))
            predictions = {
                key: statistics.median(self.samples.get(key.split(":")[0], [0])) * self.duration
                for key in self.work
            }
            runs = self.history.completed_runs(self.profile)
            known = (
                runs >= MIN_ETA_RUNS
                and bool(self.work)
                and all(predictions[key] > 0 for key in self.work if key not in self.completed)
            )
            expected = predictions.get(self.current, 0)
            overdue = expected > 0 and phase_elapsed > expected * 1.75
            if expected and self.current not in self.completed:
                done += weight(self.current) * min(0.9, phase_elapsed / expected)
            percent = min(99, int(done / total * 100)) if total else 0
            self.max_percent = max(self.max_percent, percent)
            remaining = sum(
                value
                for key, value in predictions.items()
                if key not in self.completed and key != self.current
            )
            if self.current not in self.completed:
                remaining += max(expected * 0.1, expected - phase_elapsed)
            return {
                "phase": self.phase,
                "percent": 100 if self.finished is True else self.max_percent,
                "estimated": True,
                "elapsed_seconds": int(elapsed),
                "phase_elapsed_seconds": int(phase_elapsed),
                "eta_seconds": max(1, round(remaining))
                if known and not overdue and self.finished is None
                else None,
                "eta_min_seconds": max(1, round(remaining * 0.5))
                if known and not overdue and self.finished is None
                else None,
                "eta_max_seconds": max(1, round(remaining * 1.75))
                if known and not overdue and self.finished is None
                else None,
                "calibrated": known,
                "calibration_runs": runs,
                "calibration_required": MIN_ETA_RUNS,
                "overdue": overdue,
                "stream_index": self.stream_index,
                "stream_count": self.stream_count,
            }


def stream_progress(
    observer: ProgressObserver | None, index: int, count: int
) -> ProgressObserver | None:
    if observer is None:
        return None

    def forward(event: ProgressEvent) -> None:
        observer(replace(event, stream_index=index, stream_count=count))

    return forward
