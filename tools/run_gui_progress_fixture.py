"""Serve a disposable model-free GUI with real queue/polling and a synthetic progress service.

Use a dedicated mktemp directory. No real media, credentials, models or provider calls are used.
Run check_gui_windows_startup.py with that directory and --confirm-synthetic-service.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import wave
from pathlib import Path
from types import SimpleNamespace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--port", default=8876, type=int)
    parser.add_argument("--empty-queue", action="store_true")
    parser.add_argument("--default-output", action="store_true")
    args = parser.parse_args()
    args.root.mkdir(parents=True, exist_ok=True)
    os.environ["XDG_STATE_HOME"] = str(args.root / "state")
    os.environ.pop("OPENROUTER_API_KEY", None)
    if args.default_output:
        default_output = args.root / "outputs"
        default_output.mkdir(exist_ok=True)
        os.environ["EWP_GUI_DEFAULT_OUTPUT_DIR"] = str(default_output)
    from ewp_transcripts import web_jobs, web_server, web_workflows
    from ewp_transcripts.config import ApplicationConfig
    from ewp_transcripts.progress import ProgressEvent

    config = ApplicationConfig.model_validate({"runtime": {"work_root": str(args.root / "work")}})
    web_server.load_config = lambda: config
    web_workflows.load_config = lambda: config
    web_jobs.runtime_profile = lambda *args: "synthetic-test-profile"
    server = web_server.LocalGuiServer(web_server.WebConfiguration.create(port=args.port))
    audio = args.root / "episode.wav"
    with wave.open(str(audio), "wb") as handle:
        handle.setparams((1, 2, 16000, 0, "NONE", ""))
        handle.writeframes(b"\0\0" * 64000)
    output = args.root / "output"
    output.mkdir(exist_ok=True)

    def service(path, **kwargs):
        tracker, cancel = kwargs["progress"], kwargs["cancellation"]
        assert kwargs["config"].speech.provider != "openrouter"
        tracker(
            ProgressEvent(
                "plan",
                "planned",
                phases=("prepare_audio", "transcribe", "align", "publish"),
                media_duration_ms=4000,
            )
        )
        for phase in ["prepare_audio", "transcribe", "align"]:
            tracker(ProgressEvent(phase, "started"))
            for _ in range(12):
                cancel.check()
                time.sleep(0.25)
            tracker(ProgressEvent(phase, "completed", duration_ms=3000))
        cancel.check()
        identity = "fixture" if path.name == "episode.wav" else path.stem
        result = output / f"{identity}_results.json"
        document = json.loads(
            (Path(__file__).resolve().parents[1] / "examples/results.example.json").read_text()
        )
        document["job_id"] = document["episode"]["episode_id"] = identity
        result.write_text(json.dumps(document))
        return SimpleNamespace(result_path=result)

    server.gui_transcriptions._service = service
    for name, identity in (
        []
        if args.empty_queue
        else [
            ("episode", "fixture"),
            ("cancel-waiting", "cancel-waiting"),
            ("cancel-active", "cancel-active"),
        ]
    ):
        source = args.root / f"{name}.wav"
        if source != audio:
            source.write_bytes(audio.read_bytes())
        server.gui_transcriptions.stage(
            source,
            output,
            planned_job_id=identity,
            planned_result_path=str(output / f"{identity}_results.json"),
        )
    print(f"Synthetic progress fixture: http://127.0.0.1:{args.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
