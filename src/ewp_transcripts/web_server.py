"""Loopback-only local web adapter for the browser GUI."""

from __future__ import annotations

import base64
import json
import os
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import webbrowser
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from io import BufferedIOBase
from pathlib import Path
from typing import ClassVar, cast
from urllib.parse import unquote, urlsplit
from uuid import uuid4

from ewp_transcripts import __version__
from ewp_transcripts.config import load_config
from ewp_transcripts.domain import WorkDirectory
from ewp_transcripts.domain.enums import LanguageMode
from ewp_transcripts.domain.errors import ApplicationError
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.storage import preserve_gui_selected_source
from ewp_transcripts.web_corrections import GuiCorrectionController, GuiCorrectionError
from ewp_transcripts.web_dictionaries import GuiDictionaryController
from ewp_transcripts.web_jobs import (
    GuiTranscriptionJob,
    GuiTranscriptionQueue,
    WorkflowStageName,
    workflow_progress,
)
from ewp_transcripts.web_reviews import GuiReviewController
from ewp_transcripts.web_translation_reviews import GuiTranslationReviewController
from ewp_transcripts.web_translations import GuiTranslationController, GuiTranslationError
from ewp_transcripts.web_workflows import (
    GuiWorkflowController,
    default_gui_prohibited_roots,
    require_completed_canonical_result,
)
from ewp_transcripts.web_workspaces import GuiWorkspaceController, default_workspace_directory
from ewp_transcripts.workdirs import allocate_work_directory, cleanup_work_directory

API_VERSION = "1.0"
REPOSITORY_URL = "https://github.com/Polikles/ewp-transcripts"
ISSUES_URL = f"{REPOSITORY_URL}/issues"
LICENSE_URL = f"{REPOSITORY_URL}/blob/main/LICENSE"
_ASSET_TYPES = {"app.css": "text/css; charset=utf-8", "app.js": "text/javascript; charset=utf-8"}
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; "
        "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    ),
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Cache-Control": "no-store",
}


def _is_canonical_result_filename(filename: str) -> bool:
    """Accept ordinary and force-versioned canonical result filenames."""

    return bool(re.search(r"_results(?:_v\d{3,})?\.json\Z", filename, re.IGNORECASE))


def _through_wsl_shell(command: list[str]) -> list[str]:
    """Use Bash's WSL interop path when Python cannot exec a Windows PE directly."""

    return ["/bin/bash", "-lc", shlex.join(command)]


def _select_local_directory() -> str | None:
    """Ask the local desktop for one folder without uploading its contents."""

    attempts: list[list[str]] = []
    if shutil.which("powershell.exe"):
        script = (
            "try { Add-Type -AssemblyName System.Windows.Forms; "
            "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
            "$dialog.Description = 'Choose EWP output folder'; "
            "if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) "
            "{ [Console]::Out.Write($dialog.SelectedPath) } else { exit 3 } "
            "} catch { [Console]::Error.Write($_.Exception.Message); exit 4 }"
        )
        encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
        arguments = ["powershell.exe", "-NoProfile", "-STA", "-EncodedCommand", encoded]
        attempts.append(arguments)
        attempts.append(_through_wsl_shell(arguments))
        if shutil.which("cmd.exe"):
            command_bridge = ["cmd.exe", "/C", *arguments]
            attempts.append(command_bridge)
            attempts.append(_through_wsl_shell(command_bridge))
    if shutil.which("zenity"):
        attempts.append(
            ["zenity", "--file-selection", "--directory", "--title=Choose EWP output folder"]
        )
    if not attempts:
        raise ValueError(
            "No desktop folder dialog is available. Enter the output directory path directly."
        )
    failures: list[str] = []
    for command in attempts:
        try:
            completed = subprocess.run(
                command, check=False, capture_output=True, text=True, timeout=600
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            failures.append(f"{command[0]}: {type(error).__name__} ({error})")
            continue
        if completed.returncode in {1, 3} and command[0] == "zenity":
            return None
        if completed.returncode == 3 and command[0] in {"powershell.exe", "cmd.exe", "/bin/bash"}:
            return None
        if completed.returncode == 0:
            return completed.stdout.strip() or None
        failures.append(
            f"{command[0]}: exit {completed.returncode}"
            + (f" ({completed.stderr.strip()[:180]})" if completed.stderr.strip() else "")
        )
    raise ValueError(
        "The local folder dialog could not start: "
        + "; ".join(failures)
        + ". Enter the path directly."
    )


class GuiSelectionCache:
    """Own session-only copies selected through browser file controls."""

    def __init__(self) -> None:
        self._root = Path(tempfile.gettempdir()) / "ewp-transcripts-gui-selections"
        self._run_id = uuid4()
        self._workspaces: list[WorkDirectory] = []

    @property
    def root(self) -> Path:
        """Top-level directory containing only browser-picked session copies."""

        return self._root

    def store(self, *, filename: str, content_length: int, source: BufferedIOBase) -> Path:
        """Copy one explicitly selected file in bounded chunks into an owned work directory."""

        safe_name = Path(filename).name
        if safe_name != filename or not safe_name or "\x00" in safe_name:
            raise ValueError("The selected filename is invalid.")
        if not 0 < content_length <= 16 * 1024 * 1024 * 1024:
            raise ValueError("The selected file size is invalid or exceeds the 16 GiB local limit.")
        workspace = allocate_work_directory(
            self._root, run_id=self._run_id, job_id=f"selection-{uuid4().hex}"
        )
        destination = workspace.path / safe_name
        remaining = content_length
        try:
            with destination.open("xb") as handle:
                while remaining:
                    chunk = source.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ValueError("The selected-file upload ended before all bytes arrived.")
                    handle.write(chunk)
                    remaining -= len(chunk)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(destination, 0o600)
        except Exception:
            cleanup_work_directory(workspace)
            raise
        self._workspaces.append(workspace)
        return destination

    def close(self) -> None:
        """Delete only this server's owned temporary selections."""

        for workspace in reversed(self._workspaces):
            try:
                cleanup_work_directory(workspace)
            except OSError:
                continue
        self._workspaces.clear()


@dataclass(frozen=True)
class WebConfiguration:
    """Validated runtime configuration exposed to the local web adapter."""

    host: str
    port: int
    prohibited_roots: tuple[Path, ...]

    @classmethod
    def create(cls, *, port: int) -> WebConfiguration:
        """Create the loopback configuration and its operating-system denylist."""

        if not 0 <= port <= 65535:
            raise ValueError("port must be between 0 and 65535")
        prohibited_roots = default_gui_prohibited_roots()
        return cls(
            host="127.0.0.1",
            port=port,
            prohibited_roots=prohibited_roots,
        )


@dataclass(frozen=True)
class WebResponse:
    status: HTTPStatus
    content_type: str | None
    body: bytes


def dispatch_get(
    config: WebConfiguration, *, server_port: int, host: str, target: str
) -> WebResponse:
    """Resolve one read-only GUI request without performing network I/O."""
    accepted = {f"127.0.0.1:{server_port}", f"localhost:{server_port}", f"[::1]:{server_port}"}
    if host not in accepted:
        return _json_response(
            HTTPStatus.MISDIRECTED_REQUEST,
            {
                "error": {
                    "code": "GUI_HOST_REJECTED",
                    "message": "The request Host is not allowed by the local GUI server.",
                }
            },
        )
    path = urlsplit(target).path
    if path == "/":
        return _asset_response("index.html", "text/html; charset=utf-8")
    if path == "/help":
        return _asset_response("help.html", "text/html; charset=utf-8")
    if path == "/favicon.ico":
        return WebResponse(HTTPStatus.NO_CONTENT, None, b"")
    if path.startswith("/assets/") and path.removeprefix("/assets/") in _ASSET_TYPES:
        name = path.removeprefix("/assets/")
        return _asset_response(name, _ASSET_TYPES[name])
    if path == "/api/v1/health":
        return _json_response(
            HTTPStatus.OK,
            {"status": "ok", "api_version": API_VERSION, "application_version": __version__},
        )
    if path == "/api/v1/about":
        return _json_response(
            HTTPStatus.OK,
            {
                "application": "EWP Transcriber",
                "application_version": __version__,
                "api_version": API_VERSION,
                "license": "AGPL-3.0-only",
                "warranty": "Provided without warranty; see the bundled license.",
                "repository_url": REPOSITORY_URL,
                "issues_url": ISSUES_URL,
                "license_url": LICENSE_URL,
            },
        )
    return _json_response(
        HTTPStatus.NOT_FOUND,
        {"error": {"code": "GUI_ROUTE_NOT_FOUND", "message": "No such GUI route."}},
    )


def _asset_response(name: str, content_type: str) -> WebResponse:
    assets = files("ewp_transcripts.web_assets")
    body = assets.joinpath(name).read_bytes()
    if name == "app.js":
        body += b"\n" + assets.joinpath("review_speakers.js").read_bytes()
        body += b"\n" + assets.joinpath("review_editor_recovery.js").read_bytes()
        body += b"\n" + assets.joinpath("review_editor_display.js").read_bytes()
        body += b"\n" + assets.joinpath("translation_review_editor.js").read_bytes()
        body += b"\n" + assets.joinpath("translation_provider_controls.js").read_bytes()
    if name == "app.css":
        body += b"\n" + assets.joinpath("review_editor_recovery.css").read_bytes()
        body += b"\n" + assets.joinpath("review_editor_display.css").read_bytes()
        body += b"\n" + assets.joinpath("translation_review_editor.css").read_bytes()
        body += b"\n" + assets.joinpath("workflow_tracker.css").read_bytes()
    return WebResponse(HTTPStatus.OK, content_type, body)


def _json_response(status: HTTPStatus, document: dict[str, object]) -> WebResponse:
    return WebResponse(
        status,
        "application/json; charset=utf-8",
        json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode(),
    )


class LocalGuiServer(ThreadingHTTPServer):
    """HTTP server carrying immutable GUI configuration."""

    daemon_threads = True

    def __init__(self, config: WebConfiguration) -> None:
        application_config = load_config()
        local_provider_lock = threading.Lock()
        self.gui_config = config
        self.gui_workflows = GuiWorkflowController(prohibited_roots=config.prohibited_roots)
        self.gui_selections = GuiSelectionCache()
        self.gui_workspaces = GuiWorkspaceController(
            state_directory=default_workspace_directory(),
            resolve_path=self.gui_workflows.resolve_allowed_path,
            temporary_selection_root=self.gui_selections.root,
        )
        self.gui_reviews = GuiReviewController(
            config=application_config,
            resolve_path=self.gui_workflows.resolve_allowed_path,
        )
        self.gui_dictionaries = GuiDictionaryController(
            resolve_path=self.gui_workflows.resolve_allowed_path
        )
        self.gui_corrections = GuiCorrectionController(
            config=application_config,
            resolve_path=self.gui_workflows.resolve_allowed_path,
            operation_lock=local_provider_lock,
        )
        self.gui_translations = GuiTranslationController(
            config=application_config,
            resolve_path=self.gui_workflows.resolve_allowed_path,
            operation_lock=local_provider_lock,
        )
        self.gui_translation_reviews = GuiTranslationReviewController(
            config=application_config,
            resolve_path=self.gui_workflows.resolve_allowed_path,
        )
        self.gui_csrf_token = secrets.token_urlsafe(32)
        self.gui_openrouter_api_key = ""
        self.gui_openrouter_api_key_env = application_config.correction.openrouter_api_key_env
        super().__init__((config.host, config.port), LocalGuiRequestHandler)
        self.gui_transcriptions = GuiTranscriptionQueue(config=application_config)

    def server_close(self) -> None:
        self.gui_openrouter_api_key = ""
        self.gui_transcriptions.close()
        self.gui_selections.close()
        super().server_close()

    def workspace_controller(self, storage_directory: str) -> GuiWorkspaceController:
        """Return the default or an explicitly selected user-space workspace catalog."""

        if not storage_directory.strip():
            return self.gui_workspaces
        directory = self.gui_workflows.resolve_allowed_path(storage_directory, directory=True)
        return GuiWorkspaceController(
            state_directory=directory,
            resolve_path=self.gui_workflows.resolve_allowed_path,
            temporary_selection_root=self.gui_selections.root,
        )


class LocalGuiRequestHandler(BaseHTTPRequestHandler):
    """Serve the bundled shell and a small versioned read-only API."""

    server: LocalGuiServer
    server_version = "EWPTranscriberGUI"
    sys_version = ""
    _security_headers: ClassVar[dict[str, str]] = SECURITY_HEADERS

    def do_GET(self) -> None:  # noqa: N802
        if urlsplit(self.path).path in {"/api/v1/session", "/api/v1/transcriptions"}:
            host = self.headers.get("Host", "")
            if host not in {
                f"127.0.0.1:{self.server.server_port}",
                f"localhost:{self.server.server_port}",
            }:
                self._write_response(
                    _json_response(
                        HTTPStatus.MISDIRECTED_REQUEST,
                        {
                            "error": {
                                "code": "GUI_HOST_REJECTED",
                                "message": (
                                    "The request Host is not allowed by the local GUI server."
                                ),
                            }
                        },
                    )
                )
                return
            if urlsplit(self.path).path == "/api/v1/session":
                payload: dict[str, object] = {
                    "csrf_token": self.server.gui_csrf_token,
                    "openrouter_key_configured": bool(
                        self.server.gui_openrouter_api_key
                        or os.environ.get(self.server.gui_openrouter_api_key_env, "").strip()
                    ),
                }
            else:
                payload = {
                    "jobs": [
                        {
                            **job.model_dump(mode="json"),
                            "workflow": workflow_progress(job).model_dump(mode="json"),
                        }
                        for job in self.server.gui_transcriptions.jobs()
                    ]
                }
            self._write_response(_json_response(HTTPStatus.OK, payload))
            return
        if urlsplit(self.path).path == "/api/v1/operations":
            host = self.headers.get("Host", "")
            if host not in {
                f"127.0.0.1:{self.server.server_port}",
                f"localhost:{self.server.server_port}",
            }:
                self._write_response(
                    _json_response(
                        HTTPStatus.MISDIRECTED_REQUEST,
                        {
                            "error": {
                                "code": "GUI_HOST_REJECTED",
                                "message": (
                                    "The request Host is not allowed by the local GUI server."
                                ),
                            }
                        },
                    )
                )
                return
            self._write_response(
                _json_response(
                    HTTPStatus.OK,
                    {
                        "operations": [
                            item.model_dump(mode="json")
                            for item in self.server.gui_workflows.operations()
                        ]
                    },
                )
            )
            return
        response = dispatch_get(
            self.server.gui_config,
            server_port=self.server.server_port,
            host=self.headers.get("Host", ""),
            target=self.path,
        )
        self.send_response(response.status)
        self._headers(content_type=response.content_type, content_length=len(response.body))
        self.end_headers()
        self.wfile.write(response.body)

    def do_POST(self) -> None:  # noqa: N802
        host = self.headers.get("Host", "")
        expected_origin = f"http://127.0.0.1:{self.server.server_port}"
        if host not in {
            f"127.0.0.1:{self.server.server_port}",
            f"localhost:{self.server.server_port}",
        }:
            self._write_response(
                _json_response(
                    HTTPStatus.MISDIRECTED_REQUEST,
                    {
                        "error": {
                            "code": "GUI_HOST_REJECTED",
                            "message": "The request Host is not allowed by the local GUI server.",
                        }
                    },
                )
            )
            return
        if self.headers.get("Origin") not in {
            expected_origin,
            f"http://localhost:{self.server.server_port}",
        }:
            self._write_response(
                _json_response(
                    HTTPStatus.FORBIDDEN,
                    {
                        "error": {
                            "code": "GUI_ORIGIN_REJECTED",
                            "message": "The request Origin is not allowed by the local GUI server.",
                        }
                    },
                )
            )
            return
        path = urlsplit(self.path).path
        if path in {
            "/api/v1/selected-media/upload",
            "/api/v1/import-canonical-file",
            "/api/v1/import-workspace-file",
        }:
            supplied = self.headers.get("X-EWP-CSRF", "")
            if not secrets.compare_digest(supplied, self.server.gui_csrf_token):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {
                            "error": {
                                "code": "GUI_CSRF_REJECTED",
                                "message": (
                                    "The selected-file request lacks the active session token."
                                ),
                            }
                        },
                    )
                )
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                filename = unquote(self.headers.get("X-EWP-Filename", ""))
                if path == "/api/v1/import-canonical-file" and not _is_canonical_result_filename(
                    filename
                ):
                    raise ValueError(
                        "Select a canonical *_results.json or *_results_vNNN.json file."
                    )
                if path == "/api/v1/import-canonical-file":
                    raw_output = unquote(self.headers.get("X-EWP-Output-Directory", ""))
                    if not raw_output.strip():
                        raise ValueError(
                            "Choose a durable shared output directory in Inspect and plan "
                            "before adding saved results."
                        )
                    output_directory = self.server.gui_workflows.resolve_allowed_path(
                        raw_output, directory=True
                    )
                if path == "/api/v1/import-workspace-file" and not filename.endswith(".json"):
                    raise ValueError("Select one saved workspace JSON file.")
                selected_path = self.server.gui_selections.store(
                    filename=filename, content_length=content_length, source=self.rfile
                )
                if path == "/api/v1/import-canonical-file":
                    canonical = require_completed_canonical_result(selected_path)
                    preserved_path, digest = preserve_gui_selected_source(
                        selected_path, output_directory=output_directory, category="canonical"
                    )
                    self.server.gui_workflows.resolve_allowed_path(str(preserved_path))
                    job, imported = self.server.gui_transcriptions.register_completed_result(
                        preserved_path,
                        output_directory=output_directory,
                        planned_job_id=canonical.job_id,
                        language=LanguageMode(canonical.episode.language),
                        source_sha256=digest,
                    )
                    selected_payload: dict[str, object] = {
                        "imported": imported,
                        "job": job.model_dump(mode="json"),
                    }
                elif path == "/api/v1/import-workspace-file":
                    storage_directory = unquote(self.headers.get("X-EWP-Workspace-Directory", ""))
                    workspace = self.server.workspace_controller(storage_directory)
                    saved = workspace.import_file(selected_path)
                    selected_payload = {"workspace": saved.model_dump(mode="json")}
                else:
                    selected_payload = {"path": str(selected_path)}
            except (FileNotFoundError, OSError, ValueError) as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": {
                                "code": "GUI_SELECTED_FILE_REJECTED",
                                "message": str(error),
                            }
                        },
                    )
                )
                return
            self._write_response(_json_response(HTTPStatus.OK, selected_payload))
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1_048_576:
                raise ValueError("Request body size is invalid")
            document = json.loads(self.rfile.read(length))
            if not isinstance(document, dict):
                raise ValueError("JSON body must be an object")
        except (ValueError, json.JSONDecodeError):
            self._write_response(
                _json_response(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "error": {
                            "code": "GUI_REQUEST_INVALID",
                            "message": "The request must contain a valid bounded JSON object.",
                        }
                    },
                )
            )
            return
        if path == "/api/v1/select-output-directory":
            supplied = self.headers.get("X-EWP-CSRF", "")
            if not secrets.compare_digest(supplied, self.server.gui_csrf_token):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {
                            "error": {
                                "code": "GUI_CSRF_REJECTED",
                                "message": "The folder request lacks the active session token.",
                            }
                        },
                    )
                )
                return
            try:
                selected = _select_local_directory()
                directory = (
                    str(self.server.gui_workflows.resolve_allowed_path(selected, directory=True))
                    if selected
                    else None
                )
            except (OSError, ValueError) as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {"error": {"code": "GUI_OUTPUT_DIRECTORY_INVALID", "message": str(error)}},
                    )
                )
                return
            self._write_response(_json_response(HTTPStatus.OK, {"path": directory}))
            return
        if path.startswith("/api/v1/workspaces/"):
            supplied = self.headers.get("X-EWP-CSRF", "")
            if not secrets.compare_digest(supplied, self.server.gui_csrf_token):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {
                            "error": {
                                "code": "GUI_CSRF_REJECTED",
                                "message": "The workspace request lacks the active session token.",
                            }
                        },
                    )
                )
                return
            try:
                storage_directory = document.get("storage_directory", "")
                if not isinstance(storage_directory, str):
                    raise ValueError("Workspace storage directory is invalid")
                workspaces = self.server.workspace_controller(storage_directory)
                if path == "/api/v1/workspaces/list":
                    payload: dict[str, object] = {
                        "workspaces": [item.model_dump(mode="json") for item in workspaces.list()]
                    }
                elif path == "/api/v1/workspaces/save":
                    fields = document.get("fields")
                    if not isinstance(fields, dict):
                        raise ValueError("Workspace fields must be an object")
                    queue_jobs = self.server.gui_transcriptions.jobs()
                    durable_staged = tuple(
                        job
                        for job in queue_jobs
                        if job.status == "staged"
                        and not workspaces.is_temporary_selection(job.input_path)
                    )
                    durable_terminal = tuple(
                        job
                        for job in queue_jobs
                        if job.status in {"completed", "failed"}
                        and job.source_sha256
                        and not workspaces.is_temporary_selection(job.input_path)
                        and not workspaces.is_temporary_selection(job.result_path or "")
                    )
                    saved = workspaces.save(
                        name=str(document.get("name", "")),
                        current_step=str(document.get("current_step", "")),
                        fields=fields,
                        staged_jobs=[
                            {
                                "input_path": job.input_path,
                                "output_directory": job.output_directory,
                                "planned_job_id": job.planned_job_id,
                                "planned_result_path": job.planned_result_path,
                                "source_sha256": job.source_sha256,
                                "language": job.language.value,
                                "speaker_count": job.speaker_count,
                            }
                            for job in durable_staged
                        ],
                        terminal_jobs=[job.model_dump(mode="json") for job in durable_terminal],
                        workspace_id=str(document.get("workspace_id", "")),
                    )
                    payload = {
                        "workspace": saved.model_dump(mode="json"),
                        "temporary_jobs_omitted": sum(
                            job.status in {"staged", "completed", "failed"} for job in queue_jobs
                        )
                        - len(durable_staged)
                        - len(durable_terminal),
                    }
                elif path == "/api/v1/workspaces/load":
                    loaded = workspaces.load(str(document.get("workspace_id", "")))
                    restored_terminal = self._restore_workspace_terminal_jobs(loaded.terminal_jobs)
                    restored = self._restore_workspace_staged_jobs(loaded.staged_jobs)
                    payload = {
                        "workspace": loaded.model_dump(mode="json"),
                        "restored_staged_jobs": restored,
                        "restored_terminal_jobs": restored_terminal,
                    }
                elif path == "/api/v1/workspaces/delete":
                    workspaces.delete(str(document.get("workspace_id", "")))
                    payload = {"deleted": True}
                else:
                    self._write_response(
                        _json_response(
                            HTTPStatus.NOT_FOUND,
                            {
                                "error": {
                                    "code": "GUI_ROUTE_NOT_FOUND",
                                    "message": "No such GUI route.",
                                }
                            },
                        )
                    )
                    return
            except (FileNotFoundError, OSError, ValueError) as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": {
                                "code": "GUI_WORKSPACE_REQUEST_INVALID",
                                "message": str(error),
                            }
                        },
                    )
                )
                return
            self._write_response(_json_response(HTTPStatus.OK, payload))
            return
        if path == "/api/v1/credentials/openrouter":
            supplied = self.headers.get("X-EWP-CSRF", "")
            if not secrets.compare_digest(supplied, self.server.gui_csrf_token):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {"error": {"code": "GUI_CSRF_REJECTED", "message": "Invalid session."}},
                    )
                )
                return
            key = document.get("api_key")
            if (
                not isinstance(key, str)
                or not key.strip()
                or len(key) > 512
                or any(character.isspace() for character in key)
            ):
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": {
                                "code": "GUI_CREDENTIAL_INVALID",
                                "message": "Enter one non-empty API key without whitespace.",
                            }
                        },
                    )
                )
                return
            self.server.gui_openrouter_api_key = key
            self._write_response(
                _json_response(
                    HTTPStatus.OK,
                    {"configured": True, "persistence": "server-session-only"},
                )
            )
            return
        if path.startswith("/api/v1/reviews/"):
            supplied = self.headers.get("X-EWP-CSRF", "")
            if not secrets.compare_digest(supplied, self.server.gui_csrf_token):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {
                            "error": {
                                "code": "GUI_CSRF_REJECTED",
                                "message": "The review request lacks the active session token.",
                            }
                        },
                    )
                )
                return
            try:
                result = str(document.get("result_path", ""))
                if path == "/api/v1/reviews/prepare":
                    payload = self.server.gui_reviews.prepare(
                        result,
                        str(document.get("review_output_directory", "")),
                        str(document.get("source_revision_path", "")),
                    )
                elif path == "/api/v1/reviews/load":
                    payload = self.server.gui_reviews.document(
                        str(document.get("review_path", "")), result
                    )
                elif path == "/api/v1/reviews/session/save":
                    payload = self.server.gui_reviews.remember_session(
                        project_output_directory=str(document.get("project_output_directory", "")),
                        result=result,
                        review=str(document.get("review_path", "")),
                        review_output_directory=str(document.get("review_output_directory", "")),
                        revision_output_directory=str(
                            document.get("revision_output_directory", "")
                        ),
                        export_output_directory=str(document.get("export_output_directory", "")),
                        applied_revision=str(document.get("applied_revision_path", "")),
                        source_revision=str(document.get("source_revision_path", "")),
                    )
                elif path == "/api/v1/reviews/session/restore":
                    payload = self.server.gui_reviews.restore_session(
                        str(document.get("project_output_directory", "")), result
                    )
                elif path == "/api/v1/reviews/save":
                    anchors = document.get("anchors")
                    if not isinstance(anchors, list):
                        raise ValueError("Review anchors must be an array")
                    speaker_labels = document.get("speaker_labels")
                    if speaker_labels is not None and not isinstance(speaker_labels, dict):
                        raise ValueError("Speaker labels must be an object")
                    payload = self.server.gui_reviews.save(
                        str(document.get("review_path", "")),
                        result,
                        expected_sha256=str(document.get("review_sha256", "")),
                        anchors=anchors,
                        speaker_labels=speaker_labels,
                    )
                elif path == "/api/v1/reviews/preview":
                    payload = self.server.gui_reviews.preview(
                        str(document.get("review_path", "")),
                        result,
                        str(document.get("source_revision_path", "")),
                    )
                elif path == "/api/v1/reviews/apply":
                    if document.get("confirmed") is not True:
                        raise ValueError("Manual verification confirmation is required")
                    payload = self.server.gui_reviews.apply(
                        str(document.get("review_path", "")),
                        result,
                        str(document.get("revision_output_directory", "")),
                        str(document.get("source_revision_path", "")),
                    )
                elif path == "/api/v1/reviews/export":
                    formats = document.get("formats")
                    if not isinstance(formats, list) or not all(
                        isinstance(item, str) for item in formats
                    ):
                        raise ValueError("Export formats must be an array of names")
                    payload = self.server.gui_reviews.export(
                        result,
                        str(document.get("revision_path", "")),
                        str(document.get("export_output_directory", "")),
                        formats,
                    )
                else:
                    self._write_response(
                        _json_response(
                            HTTPStatus.NOT_FOUND,
                            {
                                "error": {
                                    "code": "GUI_ROUTE_NOT_FOUND",
                                    "message": "No such GUI route.",
                                }
                            },
                        )
                    )
                    return
            except ApplicationError as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {"error": {"code": error.code, "message": str(error)}},
                    )
                )
                return
            except (FileNotFoundError, OSError, ValueError) as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {"error": {"code": "GUI_REVIEW_REQUEST_INVALID", "message": str(error)}},
                    )
                )
                return
            self._write_response(_json_response(HTTPStatus.OK, payload))
            return
        if path in {
            "/api/v1/corrections/check",
            "/api/v1/corrections/generate",
            "/api/v1/corrections/models",
        }:
            supplied = self.headers.get("X-EWP-CSRF", "")
            if not secrets.compare_digest(supplied, self.server.gui_csrf_token):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {
                            "error": {
                                "code": "GUI_CSRF_REJECTED",
                                "message": "The correction request lacks the active session token.",
                            }
                        },
                    )
                )
                return
            try:
                if document.get("provider") == "lm-studio" and any(
                    job.status in {"queued", "running"}
                    for job in self.server.gui_transcriptions.jobs()
                ):
                    raise GuiCorrectionError(
                        "GUI_GPU_BUSY",
                        "Wait for the active transcription before using local correction.",
                    )
                reasoning = document.get("reasoning_max_tokens")
                if reasoning is not None and (
                    not isinstance(reasoning, int) or isinstance(reasoning, bool) or reasoning < 0
                ):
                    raise ValueError("Reasoning-token budget must be a non-negative integer")
                if path == "/api/v1/corrections/models":
                    model_ids = document.get("model_ids")
                    if not isinstance(model_ids, list) or not all(
                        isinstance(item, str) for item in model_ids
                    ):
                        raise ValueError("Model IDs must be an array of strings")
                    payload = self.server.gui_corrections.model_pricing(
                        endpoint=str(document.get("endpoint", "")),
                        model_ids=model_ids,
                        api_key=self.server.gui_openrouter_api_key,
                    )
                elif path == "/api/v1/corrections/check":
                    payload = self.server.gui_corrections.check_provider(
                        provider_name=str(document.get("provider", "")),
                        model=str(document.get("model", "")),
                        endpoint=str(document.get("endpoint", "")),
                        allow_remote_endpoint=document.get("allow_remote_endpoint") is True,
                        reasoning_max_tokens=reasoning,
                        api_key=self.server.gui_openrouter_api_key,
                    )
                else:
                    payload = self.server.gui_corrections.generate(
                        result=str(document.get("result_path", "")),
                        output_directory=str(document.get("output_directory", "")),
                        resume_directory=str(document.get("resume_directory", "")),
                        allow_cloud=document.get("allow_cloud") is True,
                        dictionary_path=str(document.get("dictionary_path", "")),
                        project_id=str(document.get("project_id", "")),
                        confirmed=document.get("confirmed") is True,
                        provider_name=str(document.get("provider", "")),
                        model=str(document.get("model", "")),
                        endpoint=str(document.get("endpoint", "")),
                        allow_remote_endpoint=document.get("allow_remote_endpoint") is True,
                        reasoning_max_tokens=reasoning,
                        api_key=self.server.gui_openrouter_api_key,
                    )
            except ApplicationError as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {"error": {"code": error.code, "message": str(error)}},
                    )
                )
                return
            except (FileNotFoundError, OSError, ValueError) as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": {
                                "code": "GUI_CORRECTION_REQUEST_INVALID",
                                "message": str(error),
                            }
                        },
                    )
                )
                return
            self._write_response(_json_response(HTTPStatus.OK, payload))
            return
        if path in {"/api/v1/translations/check", "/api/v1/translations/generate"}:
            supplied = self.headers.get("X-EWP-CSRF", "")
            if not secrets.compare_digest(supplied, self.server.gui_csrf_token):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {
                            "error": {
                                "code": "GUI_CSRF_REJECTED",
                                "message": (
                                    "The translation request lacks the active session token."
                                ),
                            }
                        },
                    )
                )
                return
            try:
                if (
                    path == "/api/v1/translations/generate"
                    and document.get("provider") == "lm-studio"
                    and any(
                        job.status in {"queued", "running"}
                        for job in self.server.gui_transcriptions.jobs()
                    )
                ):
                    raise GuiTranslationError(
                        "GUI_GPU_BUSY",
                        "Wait for active transcription before using local translation.",
                    )
                reasoning = document.get("reasoning_max_tokens")
                if reasoning is not None and (
                    not isinstance(reasoning, int) or isinstance(reasoning, bool) or reasoning < 0
                ):
                    raise ValueError("Reasoning-token budget must be a non-negative integer")
                provider_name = str(document.get("provider", ""))
                model = str(document.get("model", ""))
                endpoint = str(document.get("endpoint", ""))
                allow_remote_endpoint = document.get("allow_remote_endpoint") is True
                api_key = self.server.gui_openrouter_api_key
                if path == "/api/v1/translations/check":
                    payload = self.server.gui_translations.check_provider(
                        provider_name=provider_name,
                        model=model,
                        endpoint=endpoint,
                        allow_remote_endpoint=allow_remote_endpoint,
                        reasoning_max_tokens=reasoning,
                        api_key=api_key,
                    )
                else:
                    payload = self.server.gui_translations.generate(
                        result=str(document.get("result_path", "")),
                        source_revision=str(document.get("source_revision_path", "")),
                        output_directory=str(document.get("output_directory", "")),
                        resume_directory=str(document.get("resume_directory", "")),
                        target_language=str(document.get("target_language", "")),
                        provider_name=provider_name,
                        model=model,
                        endpoint=endpoint,
                        allow_remote_endpoint=allow_remote_endpoint,
                        allow_cloud=document.get("allow_cloud") is True,
                        reasoning_max_tokens=reasoning,
                        output_mode=str(document.get("output_mode", "")),
                        dictionary_path=str(document.get("dictionary_path", "")),
                        confirmed=document.get("confirmed") is True,
                        api_key=api_key,
                    )
            except ApplicationError as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {"error": {"code": error.code, "message": str(error)}},
                    )
                )
                return
            except (FileNotFoundError, OSError, ValueError) as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": {
                                "code": "GUI_TRANSLATION_REQUEST_INVALID",
                                "message": str(error),
                            }
                        },
                    )
                )
                return
            self._write_response(_json_response(HTTPStatus.OK, payload))
            return
        if path.startswith("/api/v1/translation-reviews/"):
            supplied = self.headers.get("X-EWP-CSRF", "")
            if not secrets.compare_digest(supplied, self.server.gui_csrf_token):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {
                            "error": {
                                "code": "GUI_CSRF_REJECTED",
                                "message": (
                                    "The translation review request lacks the active session token."
                                ),
                            }
                        },
                    )
                )
                return
            common = {
                "review": str(document.get("review_path", "")),
                "result": str(document.get("result_path", "")),
                "revision": str(document.get("revision_path", "")),
                "parent": str(document.get("parent_translation_path", "")),
            }
            try:
                if path.endswith("/prepare"):
                    payload = self.server.gui_translation_reviews.prepare(
                        result=common["result"],
                        revision=common["revision"],
                        parent=common["parent"],
                        output=str(document.get("review_output_directory", "")),
                        target_language=str(document.get("target_language", "")),
                    )
                elif path.endswith("/load"):
                    payload = self.server.gui_translation_reviews.document(
                        common["review"],
                        common["result"],
                        common["revision"] or None,
                        common["parent"],
                    )
                elif path.endswith("/save"):
                    targets = document.get("targets")
                    if not isinstance(targets, list):
                        raise ValueError("Translation targets must be an array")
                    payload = self.server.gui_translation_reviews.save(
                        **common,
                        expected_sha256=str(document.get("review_sha256", "")),
                        targets=targets,
                    )
                elif path.endswith("/preview"):
                    payload = self.server.gui_translation_reviews.preview(**common)
                elif path.endswith("/apply"):
                    if document.get("confirmed") is not True:
                        raise ValueError("Semantic manual verification confirmation is required")
                    payload = self.server.gui_translation_reviews.apply(
                        **common, output=str(document.get("translation_output_directory", ""))
                    )
                elif path.endswith("/audit-export"):
                    formats = document.get("formats")
                    if not isinstance(formats, list) or not all(
                        isinstance(item, str) for item in formats
                    ):
                        raise ValueError("Export formats must be an array")
                    payload = self.server.gui_translation_reviews.audit_export(
                        translation=str(document.get("translation_path", "")),
                        result=common["result"],
                        revision=common["revision"],
                        audit_output=str(document.get("audit_output_directory", "")),
                        export_output=str(document.get("export_output_directory", "")),
                        formats=formats,
                    )
                else:
                    self._write_response(
                        _json_response(
                            HTTPStatus.NOT_FOUND,
                            {
                                "error": {
                                    "code": "GUI_ROUTE_NOT_FOUND",
                                    "message": "No such GUI route.",
                                }
                            },
                        )
                    )
                    return
            except ApplicationError as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {"error": {"code": error.code, "message": str(error)}},
                    )
                )
                return
            except (FileNotFoundError, OSError, ValueError) as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": {
                                "code": "GUI_TRANSLATION_REVIEW_REQUEST_INVALID",
                                "message": str(error),
                            }
                        },
                    )
                )
                return
            self._write_response(_json_response(HTTPStatus.OK, payload))
            return
        if path.startswith("/api/v1/dictionaries/"):
            supplied = self.headers.get("X-EWP-CSRF", "")
            if not secrets.compare_digest(supplied, self.server.gui_csrf_token):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {
                            "error": {
                                "code": "GUI_CSRF_REJECTED",
                                "message": "The dictionary request lacks the active session token.",
                            }
                        },
                    )
                )
                return
            try:
                if path.endswith("/catalog"):
                    payload = self.server.gui_dictionaries.catalog(
                        str(document.get("catalog_directory", ""))
                    )
                elif path.endswith("/propose"):
                    minimum = document.get("minimum_occurrences", 2)
                    if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 1:
                        raise ValueError("Minimum occurrences must be a positive integer")
                    payload = self.server.gui_dictionaries.propose(
                        canonical_directory=str(document.get("canonical_directory", "")),
                        revision_directory=str(document.get("revision_directory", "")),
                        output_root=str(document.get("output_root", "")),
                        project_id=str(document.get("project_id", "")),
                        minimum_occurrences=minimum,
                        previous_dictionary=str(document.get("previous_dictionary", "")),
                    )
                elif path.endswith("/save"):
                    decisions = document.get("decisions")
                    if not isinstance(decisions, list):
                        raise ValueError("Dictionary decisions must be an array")
                    payload = self.server.gui_dictionaries.save(
                        proposal_path=str(document.get("proposal_path", "")),
                        expected_sha256=str(document.get("proposal_sha256", "")),
                        decisions=decisions,
                    )
                elif path.endswith("/publish"):
                    if document.get("confirmed") is not True:
                        raise ValueError("Dictionary publication confirmation is required")
                    payload = self.server.gui_dictionaries.publish(
                        proposal_path=str(document.get("proposal_path", "")),
                        dictionary_id=str(document.get("dictionary_id", "")),
                        output_root=str(document.get("output_root", "")),
                    )
                else:
                    self._write_response(
                        _json_response(
                            HTTPStatus.NOT_FOUND,
                            {
                                "error": {
                                    "code": "GUI_ROUTE_NOT_FOUND",
                                    "message": "No such GUI route.",
                                }
                            },
                        )
                    )
                    return
            except ApplicationError as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {"error": {"code": error.code, "message": str(error)}},
                    )
                )
                return
            except (FileNotFoundError, OSError, ValueError) as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": {
                                "code": "GUI_DICTIONARY_REQUEST_INVALID",
                                "message": str(error),
                            }
                        },
                    )
                )
                return
            self._write_response(_json_response(HTTPStatus.OK, payload))
            return
        if path == "/api/v1/inspect":
            operation = self.server.gui_workflows.run("inspect", document)
        elif path == "/api/v1/dry-run":
            operation = self.server.gui_workflows.run("dry-run", document)
        elif path.startswith("/api/v1/transcriptions"):
            supplied = self.headers.get("X-EWP-CSRF", "")
            if not secrets.compare_digest(supplied, self.server.gui_csrf_token):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {
                            "error": {
                                "code": "GUI_CSRF_REJECTED",
                                "message": (
                                    "The transcription request lacks the active session token."
                                ),
                            }
                        },
                    )
                )
                return
            if path == "/api/v1/transcriptions/start":
                count = self.server.gui_transcriptions.start()
                self._write_response(_json_response(HTTPStatus.ACCEPTED, {"queued": count}))
                return
            if path == "/api/v1/transcriptions/clear-current":
                if document.get("confirmed") is not True:
                    self._write_response(
                        _json_response(
                            HTTPStatus.BAD_REQUEST,
                            {
                                "error": {
                                    "code": "GUI_CLEAR_CONFIRMATION_REQUIRED",
                                    "message": (
                                        "Confirm clearing the current queue and unsaved "
                                        "browser state."
                                    ),
                                }
                            },
                        )
                    )
                    return
                try:
                    cleared = self.server.gui_transcriptions.clear_current_state()
                except ValueError as error:
                    self._write_response(
                        _json_response(
                            HTTPStatus.CONFLICT,
                            {"error": {"code": "GUI_QUEUE_ACTIVE", "message": str(error)}},
                        )
                    )
                    return
                self._write_response(_json_response(HTTPStatus.OK, {"cleared": cleared}))
                return
            if path == "/api/v1/transcriptions/remove":
                job_id = document.get("job_id")
                removed = (
                    self.server.gui_transcriptions.remove(job_id)
                    if isinstance(job_id, str)
                    else False
                )
                if not removed:
                    self._write_response(
                        _json_response(
                            HTTPStatus.CONFLICT,
                            {
                                "error": {
                                    "code": "GUI_QUEUE_ITEM_IMMUTABLE",
                                    "message": "Only an existing staged queue item can be removed.",
                                }
                            },
                        )
                    )
                    return
                self._write_response(_json_response(HTTPStatus.OK, {"removed": job_id}))
                return
            if path == "/api/v1/transcriptions/workflow-error":
                result_path = document.get("result_path")
                stage = document.get("stage")
                code = document.get("code")
                allowed_stages = {
                    "correction",
                    "review",
                    "original_export",
                    "assisted_translation",
                    "translation",
                    "translated_export",
                }
                if (
                    not isinstance(result_path, str)
                    or not isinstance(stage, str)
                    or stage not in allowed_stages
                    or not isinstance(code, str)
                    or not code
                ):
                    self._write_response(
                        _json_response(
                            HTTPStatus.BAD_REQUEST,
                            {
                                "error": {
                                    "code": "GUI_WORKFLOW_ERROR_INVALID",
                                    "message": "The workflow error report is malformed.",
                                }
                            },
                        )
                    )
                    return
                recorded = self.server.gui_transcriptions.record_workflow_error(
                    result_path, cast(WorkflowStageName, stage), code
                )
                self._write_response(_json_response(HTTPStatus.OK, {"recorded": recorded}))
                return
            if path == "/api/v1/transcriptions/workflow-skip-batch":
                result_paths = document.get("result_paths")
                stage = document.get("stage")
                if (
                    not isinstance(result_paths, list)
                    or not 1 <= len(result_paths) <= 50
                    or any(not isinstance(item, str) or not item for item in result_paths)
                    or len(set(result_paths)) != len(result_paths)
                    or stage not in {"correction", "assisted_translation"}
                ):
                    self._write_response(
                        _json_response(
                            HTTPStatus.BAD_REQUEST,
                            {
                                "error": {
                                    "code": "GUI_WORKFLOW_SKIP_INVALID",
                                    "message": (
                                        "Select 1–50 distinct completed canonical results "
                                        "for one optional stage."
                                    ),
                                }
                            },
                        )
                    )
                    return
                try:
                    for result_path in result_paths:
                        canonical_path = self.server.gui_workflows.resolve_allowed_path(result_path)
                        require_completed_canonical_result(canonical_path)
                except (FileNotFoundError, OSError, ValueError) as error:
                    self._write_response(
                        _json_response(
                            HTTPStatus.BAD_REQUEST,
                            {
                                "error": {
                                    "code": "GUI_WORKFLOW_RESULT_INVALID",
                                    "message": str(error),
                                }
                            },
                        )
                    )
                    return
                skipped_paths = self.server.gui_transcriptions.skip_workflow_stages(
                    tuple(result_paths), cast(WorkflowStageName, stage)
                )
                self._write_response(
                    _json_response(
                        HTTPStatus.OK,
                        {
                            "skipped": list(skipped_paths),
                            "not_found": [
                                item for item in result_paths if item not in skipped_paths
                            ],
                        },
                    )
                )
                return
            if path in {
                "/api/v1/transcriptions/workflow-skip",
                "/api/v1/transcriptions/workflow-reopen",
            }:
                result_path = document.get("result_path")
                stage = document.get("stage")
                if (
                    not isinstance(result_path, str)
                    or not isinstance(stage, str)
                    or stage not in {"correction", "assisted_translation"}
                ):
                    self._write_response(
                        _json_response(
                            HTTPStatus.BAD_REQUEST,
                            {
                                "error": {
                                    "code": "GUI_WORKFLOW_SKIP_INVALID",
                                    "message": (
                                        "Only optional correction or LLM-assisted translation "
                                        "can be skipped."
                                    ),
                                }
                            },
                        )
                    )
                    return
                try:
                    canonical_path = self.server.gui_workflows.resolve_allowed_path(result_path)
                    require_completed_canonical_result(canonical_path)
                except (FileNotFoundError, OSError, ValueError):
                    self._write_response(
                        _json_response(
                            HTTPStatus.BAD_REQUEST,
                            {
                                "error": {
                                    "code": "GUI_WORKFLOW_RESULT_INVALID",
                                    "message": (
                                        "Choose a completed canonical result JSON file "
                                        "(for example, "
                                        "episode_results.json), not an audio or subtitle file."
                                    ),
                                }
                            },
                        )
                    )
                    return
                if path.endswith("workflow-reopen"):
                    reopened = self.server.gui_transcriptions.reopen_workflow_stage(
                        result_path, cast(WorkflowStageName, stage)
                    )
                    self._write_response(_json_response(HTTPStatus.OK, {"reopened": reopened}))
                else:
                    skipped = self.server.gui_transcriptions.skip_workflow_stage(
                        result_path, cast(WorkflowStageName, stage)
                    )
                    self._write_response(_json_response(HTTPStatus.OK, {"skipped": skipped}))
                return
            if path != "/api/v1/transcriptions":
                self._write_response(
                    _json_response(
                        HTTPStatus.NOT_FOUND,
                        {"error": {"code": "GUI_ROUTE_NOT_FOUND", "message": "No such GUI route."}},
                    )
                )
                return
            try:
                input_path = self.server.gui_workflows.resolve_allowed_path(
                    str(document.get("path", ""))
                )
                output_path = self.server.gui_workflows.resolve_allowed_path(
                    str(document.get("output_directory", "")), directory=True
                )
                if not input_path.is_file():
                    raise ValueError("The first transcription slice accepts one file")
                language, speaker_count = self.server.gui_workflows.resolve_transcription_options(
                    document
                )
                active_output = self.server.gui_transcriptions.active_output_directory()
                if active_output is not None and active_output != str(output_path):
                    self._write_response(
                        _json_response(
                            HTTPStatus.CONFLICT,
                            {
                                "error": {
                                    "code": "GUI_QUEUE_OUTPUT_MISMATCH",
                                    "message": (
                                        "All active queue jobs must use the same output directory."
                                    ),
                                }
                            },
                        )
                    )
                    return
                if self.server.gui_transcriptions.contains_active_input(input_path):
                    self._write_response(
                        _json_response(
                            HTTPStatus.CONFLICT,
                            {
                                "error": {
                                    "code": "GUI_QUEUE_DUPLICATE",
                                    "message": "This input is already staged, queued, or running.",
                                }
                            },
                        )
                    )
                    return
                plan = self.server.gui_workflows.completed_plan(
                    input_path,
                    output_path,
                    language=language,
                    speaker_count=speaker_count,
                )
                if plan is None:
                    self._write_response(
                        _json_response(
                            HTTPStatus.BAD_REQUEST,
                            {
                                "error": {
                                    "code": "GUI_DRY_RUN_REQUIRED",
                                    "message": (
                                        "Run and review dry-run for this exact input, output, "
                                        "language, and speaker count before adding it to the queue."
                                    ),
                                }
                            },
                        )
                    )
                    return
                if document.get("confirmed") is not True:
                    self._write_response(
                        _json_response(
                            HTTPStatus.BAD_REQUEST,
                            {
                                "error": {
                                    "code": "GUI_CONFIRMATION_REQUIRED",
                                    "message": (
                                        "Check 'I reviewed this exact dry-run' before adding "
                                        "the file to the queue."
                                    ),
                                }
                            },
                        )
                    )
                    return
                planned_jobs = plan.get("jobs")
                if not isinstance(planned_jobs, list) or len(planned_jobs) != 1:
                    raise ValueError("The staged dry-run must contain exactly one job")
                planned_job = planned_jobs[0]
                if not isinstance(planned_job, dict):
                    raise ValueError("The staged dry-run has no valid job plan")
                if planned_job.get("decision") == "skip":
                    existing = planned_job.get("existing_result")
                    existing_path = existing.get("path") if isinstance(existing, dict) else None
                    self._write_response(
                        _json_response(
                            HTTPStatus.CONFLICT,
                            {
                                "error": {
                                    "code": "GUI_TRANSCRIPTION_ALREADY_EXISTS",
                                    "message": (
                                        "A completed transcript already exists for this input"
                                        + (f": {existing_path}." if existing_path else ".")
                                        + " Use that result or choose a different output directory."
                                    ),
                                }
                            },
                        )
                    )
                    return
                planned_outputs = planned_job.get("outputs")
                if not isinstance(planned_outputs, dict):
                    raise ValueError("The staged dry-run has no valid output plan")
                planned_job_id = planned_job.get("job_id")
                planned_result_path = planned_outputs.get("results")
                if not isinstance(planned_job_id, str) or not isinstance(planned_result_path, str):
                    raise ValueError("The staged dry-run has no valid result identity")
                inspection = plan.get("inspection")
                episodes = inspection.get("episodes") if isinstance(inspection, dict) else None
                sources = (
                    episodes[0].get("sources")
                    if isinstance(episodes, list) and episodes and isinstance(episodes[0], dict)
                    else None
                )
                fingerprint = (
                    sources[0].get("fingerprint")
                    if isinstance(sources, list) and sources and isinstance(sources[0], dict)
                    else None
                )
                source_sha256 = fingerprint.get("sha256") if isinstance(fingerprint, dict) else None
                if not isinstance(source_sha256, str) or len(source_sha256) != 64:
                    raise ValueError("The staged dry-run has no valid source fingerprint")
                if self.server.gui_transcriptions.contains_active_planned_job(planned_job_id):
                    self._write_response(
                        _json_response(
                            HTTPStatus.CONFLICT,
                            {
                                "error": {
                                    "code": "GUI_QUEUE_JOB_ID_COLLISION",
                                    "message": (
                                        "An active queue item already uses this job ID. "
                                        "Rename one source before staging it."
                                    ),
                                }
                            },
                        )
                    )
                    return
                if self.server.gui_selections.root in input_path.parents:
                    input_path, preserved_sha256 = preserve_gui_selected_source(
                        input_path, output_directory=output_path, category="media"
                    )
                    self.server.gui_workflows.resolve_allowed_path(str(input_path))
                    if preserved_sha256 != source_sha256:
                        raise ValueError("The selected audio changed since the reviewed dry-run")
                    if self.server.gui_transcriptions.contains_active_input(input_path):
                        raise ValueError("This selected audio is already staged or running")
                job = self.server.gui_transcriptions.stage(
                    input_path,
                    output_path,
                    planned_job_id=planned_job_id,
                    planned_result_path=planned_result_path,
                    source_sha256=source_sha256,
                    language=language,
                    speaker_count=speaker_count,
                )
            except (FileNotFoundError, OSError, ValueError) as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {"error": {"code": "GUI_PATH_REJECTED", "message": str(error)}},
                    )
                )
                return
            self._write_response(_json_response(HTTPStatus.ACCEPTED, job.model_dump(mode="json")))
            return
        else:
            self._write_response(
                _json_response(
                    HTTPStatus.NOT_FOUND,
                    {"error": {"code": "GUI_ROUTE_NOT_FOUND", "message": "No such GUI route."}},
                )
            )
            return
        status = HTTPStatus.OK if operation.status == "completed" else HTTPStatus.BAD_REQUEST
        self._write_response(_json_response(status, operation.model_dump(mode="json")))

    def _restore_workspace_staged_jobs(self, staged_jobs: tuple[dict[str, str | int], ...]) -> int:
        """Rebuild only hash-validated staged jobs after a GUI restart."""

        if not staged_jobs:
            return 0
        active = [
            job
            for job in self.server.gui_transcriptions.jobs()
            if job.status in {"staged", "queued", "running"}
        ]
        expected = {(item["planned_job_id"], item["source_sha256"]) for item in staged_jobs}
        if active:
            actual = {(job.planned_job_id, job.source_sha256) for job in active}
            if actual == expected:
                return 0
            raise ValueError(
                "An active transcription queue cannot be replaced by saved workspace jobs"
            )
        for item in staged_jobs:
            input_path = self.server.gui_workflows.resolve_allowed_path(str(item["input_path"]))
            output_path = self.server.gui_workflows.resolve_allowed_path(
                str(item["output_directory"]), directory=True
            )
            if sha256_file(input_path) != item["source_sha256"]:
                raise ValueError("A staged source changed since this workspace was saved")
            language, speaker_count = self.server.gui_workflows.resolve_transcription_options(
                {"language": item["language"], "speaker_count": item["speaker_count"]}
            )
            operation = self.server.gui_workflows.run(
                "dry-run",
                {
                    "path": str(input_path),
                    "output_directory": str(output_path),
                    "language": language.value,
                    "speaker_count": speaker_count,
                },
            )
            jobs = operation.result.get("jobs") if operation.result else None
            if operation.status != "completed" or not isinstance(jobs, list) or len(jobs) != 1:
                raise ValueError("A staged job could not be safely replanned")
            planned = jobs[0]
            outputs = planned.get("outputs") if isinstance(planned, dict) else None
            if (
                not isinstance(planned, dict)
                or not isinstance(outputs, dict)
                or planned.get("job_id") != item["planned_job_id"]
                or outputs.get("results") != item["planned_result_path"]
            ):
                raise ValueError("A staged job plan changed since this workspace was saved")
            self.server.gui_transcriptions.stage(
                input_path,
                output_path,
                planned_job_id=str(item["planned_job_id"]),
                planned_result_path=str(item["planned_result_path"]),
                source_sha256=str(item["source_sha256"]),
                language=language,
                speaker_count=speaker_count,
            )
        return len(staged_jobs)

    def _restore_workspace_terminal_jobs(
        self, terminal_jobs: tuple[GuiTranscriptionJob, ...]
    ) -> int:
        """Restore validated completed/failed queue history before staged jobs are rebuilt."""

        if not terminal_jobs:
            return 0
        # Workspace validation already restricts these records. Re-validate at the boundary that
        # mutates the live queue, so an internal caller cannot bypass the persisted contract.
        jobs = tuple(
            GuiTranscriptionJob.model_validate(item.model_dump(mode="json"))
            for item in terminal_jobs
        )
        for job in jobs:
            self.server.gui_workflows.resolve_allowed_path(job.input_path)
            self.server.gui_workflows.resolve_allowed_path(job.output_directory, directory=True)
            self.server.gui_workflows.resolve_allowed_path(
                job.planned_result_path, directory=job.status == "failed"
            )
            if job.status == "completed":
                if not job.result_path:
                    raise ValueError("A completed saved queue job lacks its result")
                self.server.gui_workflows.resolve_allowed_path(job.result_path)
        return self.server.gui_transcriptions.replace_terminal_jobs(jobs)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _headers(self, *, content_type: str | None, content_length: int) -> None:
        if content_type is not None:
            self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        for name, value in self._security_headers.items():
            self.send_header(name, value)

    def _write_response(self, response: WebResponse) -> None:
        self.send_response(response.status)
        self._headers(content_type=response.content_type, content_length=len(response.body))
        self.end_headers()
        try:
            self.wfile.write(response.body)
        except (BrokenPipeError, ConnectionResetError):
            # A browser can abandon a completed request while navigating or refreshing.
            # The response has no stateful side effect, so the disconnect is not an error.
            return


def serve_gui(*, port: int, open_browser: bool = True) -> None:
    """Run the local GUI until interrupted."""

    server = LocalGuiServer(WebConfiguration.create(port=port))
    url = f"http://127.0.0.1:{server.server_port}/"
    print(f"GUI {url}")
    print("Press Ctrl+C to stop.")
    if open_browser:
        threading.Timer(0.1, _open_browser, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _open_browser(url: str) -> None:
    """Try host launchers in order and report a usable fallback URL on failure."""

    failures: list[str] = []
    try:
        release = Path("/proc/sys/kernel/osrelease").read_text(encoding="utf-8")
    except OSError:
        release = ""
    if "microsoft" in release.casefold() or os.environ.get("WSL_INTEROP"):
        commands = [
            ["cmd.exe", "/C", "start", "", url],
            ["powershell.exe", "-NoProfile", "-Command", "Start-Process", url],
        ]
        if shutil.which("wslview"):
            commands.append(["wslview", url])
        for command in commands:
            if not shutil.which(command[0]):
                failures.append(f"{command[0]} unavailable")
                continue
            attempts = (
                (command,) if command[0] == "wslview" else (command, _through_wsl_shell(command))
            )
            for attempt in attempts:
                try:
                    completed = subprocess.run(
                        attempt,
                        check=False,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        text=True,
                        errors="replace",
                        timeout=20,
                    )
                except (OSError, subprocess.TimeoutExpired) as error:
                    failures.append(f"{attempt[0]} {type(error).__name__}: {error}")
                    continue
                if completed.returncode == 0:
                    return
                failures.append(
                    f"{attempt[0]} exit {completed.returncode}"
                    + (f" ({completed.stderr.strip()[:180]})" if completed.stderr.strip() else "")
                )
        print(
            f"GUI_BROWSER_OPEN_FAILED: Open {url} manually. " + "; ".join(failures),
            file=sys.stderr,
        )
        return
    try:
        if webbrowser.open(url):
            return
    except (OSError, subprocess.SubprocessError) as error:
        failures.append(f"Linux browser {type(error).__name__}: {error}")
    print(
        f"GUI_BROWSER_OPEN_FAILED: Open {url} manually. " + "; ".join(failures),
        file=sys.stderr,
    )
