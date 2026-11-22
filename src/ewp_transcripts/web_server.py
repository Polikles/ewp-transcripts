"""Loopback-only local web adapter for the browser GUI."""

from __future__ import annotations

import base64
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from io import BufferedIOBase
from pathlib import Path
from typing import Any, ClassVar, cast
from urllib.parse import quote, unquote, urlsplit
from uuid import uuid4

from ewp_transcripts import __version__
from ewp_transcripts.application import doctor
from ewp_transcripts.config import SpeechConfig, load_config
from ewp_transcripts.credentials import OSCredentialStore, validate_api_key
from ewp_transcripts.domain import WorkDirectory
from ewp_transcripts.domain.enums import LanguageMode
from ewp_transcripts.domain.errors import ApplicationError, SpeechEngineError
from ewp_transcripts.domain.models import JobStateRecord
from ewp_transcripts.domain.revision import sha256_file
from ewp_transcripts.gui_library import GuiLibrary
from ewp_transcripts.native_picker import select_native_file
from ewp_transcripts.storage import preserve_gui_selected_source
from ewp_transcripts.web_corrections import GuiCorrectionController, GuiCorrectionError
from ewp_transcripts.web_dictionaries import GuiDictionaryController
from ewp_transcripts.web_downloads import GuiExportDownloads
from ewp_transcripts.web_guides import render_guide
from ewp_transcripts.web_inputs import GuiInputs
from ewp_transcripts.web_jobs import (
    GuiCloudKeyRequired,
    GuiCloudPreflightFailed,
    GuiTranscriptionJob,
    GuiTranscriptionQueue,
    WorkflowStageName,
    workflow_progress,
)
from ewp_transcripts.web_media import GuiMediaController, media_byte_range
from ewp_transcripts.web_profiles import PROFILE_LIMIT, GuiProfileController
from ewp_transcripts.web_projects import GuiProjects
from ewp_transcripts.web_restore import GuiRestoreProgress
from ewp_transcripts.web_reviews import GuiReviewController
from ewp_transcripts.web_source_cleanup import (
    GuiManagedSourceCleanupError,
    cleanup_managed_sources,
    inventory_managed_sources,
)
from ewp_transcripts.web_speech import GuiSpeechController
from ewp_transcripts.web_translation_reviews import GuiTranslationReviewController
from ewp_transcripts.web_translations import GuiTranslationController, GuiTranslationError
from ewp_transcripts.web_workdirs import GuiWorkdirController
from ewp_transcripts.web_workflows import (
    GuiWorkflowController,
    default_gui_prohibited_roots,
    require_completed_canonical_result,
)
from ewp_transcripts.web_workspaces import (
    GuiWorkspaceController,
    GuiWorkspaceLocations,
    GuiWorkspaceMedia,
    GuiWorkspaceNameExists,
    default_workspace_directory,
    resolve_optional_workspace_file,
)
from ewp_transcripts.workdirs import allocate_work_directory, cleanup_work_directory

API_VERSION = "1.0"
REPOSITORY_URL = "https://github.com/Polikles/ewp-transcripts"
ISSUES_URL = f"{REPOSITORY_URL}/issues"
LICENSE_URL = f"{REPOSITORY_URL}/blob/main/LICENSE"
_ASSET_TYPES = {"app.css": "text/css; charset=utf-8", "app.js": "text/javascript; charset=utf-8"}
# Fixed resource manifest: never interpret a browser-supplied path as a filesystem path.
_ASSET_TYPES.update(
    {
        "brand/" + name: mime
        for name, mime in {
            "tokens.css": "text/css; charset=utf-8",
            "logo.svg": "image/svg+xml",
            "favicon.svg": "image/svg+xml",
            "gear.svg": "image/svg+xml",
            "web-pattern-light.svg": "image/svg+xml",
            "web-pattern-dark.svg": "image/svg+xml",
            "montserrat.woff2": "font/woff2",
            "mono.woff2": "font/woff2",
            "NOTICE.txt": "text/plain; charset=utf-8",
            "LICENSE-ASSETS.txt": "text/plain; charset=utf-8",
            "Montserrat-OFL.txt": "text/plain; charset=utf-8",
            "NotoSansMono-OFL.txt": "text/plain; charset=utf-8",
            "Lucide-LICENSE.txt": "text/plain; charset=utf-8",
            **{
                icon + ".svg": "image/svg+xml"
                for icon in (
                    "file-music",
                    "list-ordered",
                    "settings-2",
                    "book-open",
                    "languages",
                    "download",
                    "split",
                )
            },
        }.items()
    }
)
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self' "
        "'sha256-+ofmwl8C0LfVC0NWIY+m/gaSyXmSOBladdCFOJyIBis='; img-src 'self'; "
        "font-src 'self'; media-src 'self'; connect-src 'self'; base-uri 'none'; "
        "form-action 'none'; frame-ancestors 'none'"
    ),
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Cache-Control": "no-store",
}


def _is_canonical_result_filename(filename: str) -> bool:
    """Accept ordinary and force-versioned canonical result filenames."""

    return bool(re.search(r"_results(?:_v\d{3,})?\.json\Z", filename, re.IGNORECASE))


def _windows_interop_attempts(command: list[str]) -> tuple[tuple[list[str], str | None], ...]:
    """Try normal WSL binfmt, then its `/init` interpreter explicitly."""

    executable = shutil.which(command[0])
    if not executable:
        return ()
    resolved = [executable, *command[1:]]
    attempts: list[tuple[list[str], str | None]] = [(resolved, None)]
    if Path("/init").is_file():
        attempts.append((resolved, "/init"))
    return tuple(attempts)


def _is_wsl_environment() -> bool:
    try:
        release = Path("/proc/sys/kernel/osrelease").read_text(encoding="utf-8")
    except OSError:
        release = ""
    return "microsoft" in release.casefold() or bool(os.environ.get("WSL_INTEROP"))


def _select_local_directory() -> str | None:
    """Ask the deployment's desktop for one server-visible output directory."""

    attempts: list[tuple[list[str], str | None]] = []
    if (_is_wsl_environment() or sys.platform == "win32") and shutil.which("powershell.exe"):
        script = (
            "try { [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false); "
            "Add-Type -TypeDefinition 'using System.Runtime.InteropServices; "
            'public class EwpDpi { [DllImport("user32.dll")] '
            "public static extern bool SetProcessDPIAware(); }'; "
            "[void][EwpDpi]::SetProcessDPIAware(); "
            "Add-Type -AssemblyName System.Windows.Forms; "
            "[System.Windows.Forms.Application]::EnableVisualStyles(); "
            "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
            "if ($dialog.PSObject.Properties.Name -contains 'AutoUpgradeEnabled') "
            "{ $dialog.AutoUpgradeEnabled = $true }; "
            "$dialog.Description = 'Choose EWP output folder'; "
            "if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) "
            "{ [Console]::Out.Write($dialog.SelectedPath) } else { exit 3 } "
            "} catch { [Console]::Error.Write($_.Exception.Message); exit 4 }"
        )
        encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
        arguments = ["powershell.exe", "-NoProfile", "-STA", "-EncodedCommand", encoded]
        attempts.extend(_windows_interop_attempts(arguments))
    linux_dialogs = (
        (
            "zenity",
            ["zenity", "--file-selection", "--directory", "--title=Choose EWP output folder"],
        ),
        (
            "kdialog",
            ["kdialog", "--getexistingdirectory", ".", "--title", "Choose EWP output folder"],
        ),
        (
            "yad",
            ["yad", "--file-selection", "--directory", "--title=Choose EWP output folder"],
        ),
    )
    for executable_name, command in linux_dialogs:
        executable = shutil.which(executable_name)
        if executable:
            attempts.append(([executable, *command[1:]], None))
    if not attempts:
        raise ValueError(
            "No desktop folder dialog is available. Enter the output directory path directly."
        )
    failures: list[str] = []
    for command, interpreter in attempts:
        try:
            completed = subprocess.run(
                command,
                executable=interpreter,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=600,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            launcher = f"/init → {Path(command[0]).name}" if interpreter else Path(command[0]).name
            failures.append(f"{launcher}: {type(error).__name__} ({error})")
            continue
        if completed.returncode in {1, 3} and Path(command[0]).name in {
            "zenity",
            "kdialog",
            "yad",
        }:
            return None
        if completed.returncode == 3 and Path(command[0]).name == "powershell.exe":
            return None
        if completed.returncode == 0:
            return completed.stdout.strip() or None
        failures.append(
            f"{'/init → ' if interpreter else ''}{Path(command[0]).name}: "
            f"exit {completed.returncode}"
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
    if path.startswith("/help/"):
        guide = render_guide(path.removeprefix("/help/"))
        if guide is not None:
            return WebResponse(HTTPStatus.OK, "text/html; charset=utf-8", guide)
    if path == "/api/v1/guides":
        return _asset_response("guides/index.json", "application/json; charset=utf-8")
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
        body += b"\n" + assets.joinpath("ui_locale.js").read_bytes()
        body += b"\n" + assets.joinpath("ui_locale_catalog.js").read_bytes()
        body += b"\n" + assets.joinpath("review_feedback.js").read_bytes()
        body += b"\n" + assets.joinpath("workbench.js").read_bytes()
        body += b"\n" + assets.joinpath("dictionary_library.js").read_bytes()
        body += b"\n" + assets.joinpath("workflow_guidance.js").read_bytes()
        body += b"\n" + assets.joinpath("source_playback.js").read_bytes()
        body += b"\n" + assets.joinpath("runtime_progress.js").read_bytes()
        body += b"\n" + assets.joinpath("workflow_batch.js").read_bytes()
        body += b"\n" + assets.joinpath("user_profiles.js").read_bytes()
        body += b"\n" + assets.joinpath("workspace_restore.js").read_bytes()
        body += b"\n" + assets.joinpath("credential_controls.js").read_bytes()
        body += b"\n" + assets.joinpath("project_controls.js").read_bytes()
        body += b"\n" + assets.joinpath("media_choices.js").read_bytes()
        body += b"\n" + assets.joinpath("native_picker_controls.js").read_bytes()
        body += b"\n" + assets.joinpath("cloud_asr_controls.js").read_bytes()
    if name == "app.css":
        body += b"\n" + assets.joinpath("review_editor_recovery.css").read_bytes()
        body += b"\n" + assets.joinpath("review_editor_display.css").read_bytes()
        body += b"\n" + assets.joinpath("translation_review_editor.css").read_bytes()
        body += b"\n" + assets.joinpath("workflow_tracker.css").read_bytes()
        body += b"\n" + assets.joinpath("workbench.css").read_bytes()
        body += b"\n" + assets.joinpath("workflow_guidance.css").read_bytes()
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
        from ewp_transcripts.platform_runtime import prepare_native_environment

        prepare_native_environment()
        application_config = load_config()
        local_provider_lock = threading.Lock()
        self.gui_config = config
        self.gui_workflows = GuiWorkflowController(prohibited_roots=config.prohibited_roots)
        self.gui_inputs = GuiInputs(self.gui_workflows.resolve_allowed_path)
        self.gui_speech = GuiSpeechController(self.gui_inputs)
        self.gui_selections = GuiSelectionCache()
        self.gui_workspaces = GuiWorkspaceController(
            state_directory=default_workspace_directory(),
            resolve_path=self.gui_workflows.resolve_allowed_path,
            temporary_selection_root=self.gui_selections.root,
        )
        self.gui_workspace_locations = GuiWorkspaceLocations(
            default_workspace_directory().parent / "workspace-locations.json",
            self.gui_workflows.resolve_allowed_path,
        )
        self.gui_projects = GuiProjects(
            default_workspace_directory().parent / "project-catalog.json",
            self.gui_workflows.resolve_allowed_path,
        )
        self.gui_reviews = GuiReviewController(
            config=application_config,
            resolve_path=self.gui_workflows.resolve_allowed_path,
        )
        self.gui_media = GuiMediaController(resolve_path=self.gui_workflows.resolve_allowed_path)
        self.gui_library = GuiLibrary(
            state_directory=default_workspace_directory(),
            resolve_path=self.gui_workflows.resolve_allowed_path,
            subtitles=application_config.subtitles,
        )
        self.gui_dictionaries = GuiDictionaryController(
            resolve_path=self.gui_workflows.resolve_allowed_path, library=self.gui_library
        )
        self.gui_profiles = GuiProfileController(
            state_directory=default_workspace_directory().parent,
            workspaces=self.gui_workspaces,
            library=self.gui_library,
            projects=self.gui_projects,
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
        self.gui_downloads = GuiExportDownloads(
            config=application_config,
            resolve_path=self.gui_workflows.resolve_allowed_path,
            registry=default_workspace_directory().parent / "export-downloads.json",
        )
        self.gui_restore = GuiRestoreProgress()
        self.gui_workdirs = GuiWorkdirController(application_config.runtime.work_root)
        self.gui_csrf_token = secrets.token_urlsafe(32)
        self.gui_dependencies_tested = False
        self.gui_openrouter_api_key = ""
        self.gui_credentials = OSCredentialStore()
        self.gui_openrouter_api_key_env = application_config.correction.openrouter_api_key_env
        super().__init__((config.host, config.port), LocalGuiRequestHandler)
        self.gui_transcriptions = GuiTranscriptionQueue(
            config=application_config,
            api_key_provider=lambda: (
                self.gui_openrouter_api_key or os.environ.get(self.gui_openrouter_api_key_env, "")
            ),
            history_path=default_workspace_directory().parent / "runtime-timings.json",
        )

    def server_close(self) -> None:
        self.gui_openrouter_api_key = ""
        self.gui_transcriptions.close()
        self.gui_media.close()
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

    def workspace_catalogs(
        self, storage_directory: str
    ) -> tuple[tuple[str, str, GuiWorkspaceController], ...]:
        """Return the default and selected custom catalogs without hiding either one."""

        selected = self.workspace_controller(storage_directory)
        catalogs = [("", "Default", self.gui_workspaces)]
        if selected.state_directory != self.gui_workspaces.state_directory:
            catalogs.append((storage_directory, "Custom", selected))
        seen = {controller.state_directory for _, _, controller in catalogs}
        for directory in self.gui_workspace_locations.available().catalogs:
            controller = self.workspace_controller(directory)
            if controller.state_directory not in seen:
                catalogs.append((directory, "Custom", controller))
                seen.add(controller.state_directory)
        return tuple(catalogs)


class LocalGuiRequestHandler(BaseHTTPRequestHandler):
    """Serve the bundled shell and a small versioned read-only API."""

    server: LocalGuiServer
    server_version = "EWPTranscriberGUI"
    sys_version = ""
    _security_headers: ClassVar[dict[str, str]] = SECURITY_HEADERS

    def do_GET(self) -> None:  # noqa: N802
        if urlsplit(self.path).path.startswith("/api/v1/export-downloads/"):
            self._download_export()
            return
        if urlsplit(self.path).path.startswith("/api/v1/review-audio/"):
            self._stream_review_audio()
            return
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
                    "platform": sys.platform,
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

    def do_HEAD(self) -> None:  # noqa: N802
        if urlsplit(self.path).path.startswith("/api/v1/export-downloads/"):
            self._download_export(head=True)
        elif urlsplit(self.path).path.startswith("/api/v1/review-audio/"):
            self._stream_review_audio(head=True)
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def _download_export(self, *, head: bool = False) -> None:
        origins = {
            f"http://127.0.0.1:{self.server.server_port}",
            f"http://localhost:{self.server.server_port}",
        }
        if (
            self.headers.get("Host", "")
            not in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            or self.headers.get("Sec-Fetch-Site") == "cross-site"
            or (
                self.headers.get("Origin") is not None and self.headers.get("Origin") not in origins
            )
        ):
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        token = urlsplit(self.path).path.removeprefix("/api/v1/export-downloads/")
        try:
            filename, data = self.server.gui_downloads.open(token)
        except (OSError, ValueError, ApplicationError):
            self._write_response(
                _json_response(
                    HTTPStatus.NOT_FOUND,
                    {
                        "error": {
                            "code": "GUI_EXPORT_DOWNLOAD_INVALID",
                            "message": (
                                "Download is unavailable or changed. Refresh existing exports."
                            ),
                        }
                    },
                )
            )
            return
        self.send_response(HTTPStatus.OK)
        self._headers(content_type="application/octet-stream", content_length=len(data))
        self.send_header(
            "Content-Disposition",
            "attachment; filename=export; filename*=UTF-8''" + quote(filename, safe=""),
        )
        self.end_headers()
        if not head:
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                return

    def _stream_review_audio(self, *, head: bool = False) -> None:
        if (
            self.headers.get("Host", "")
            not in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
            or self.headers.get("Sec-Fetch-Site") == "cross-site"
        ):
            self._write_response(
                _json_response(
                    HTTPStatus.FORBIDDEN,
                    {
                        "error": {
                            "code": "GUI_HOST_REJECTED",
                            "message": "The request Host is not allowed by the local GUI server.",
                        }
                    },
                )
            )
            return
        token = urlsplit(self.path).path.removeprefix("/api/v1/review-audio/")
        try:
            audio = self.server.gui_media.open(token)
        except (OSError, ValueError):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        with audio:
            try:
                size = os.fstat(audio.fileno()).st_size
                try:
                    start, end = media_byte_range(self.headers.get("Range"), size)
                except ValueError:
                    self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                    self._headers(content_type="audio/wav", content_length=0)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.end_headers()
                    return
                partial = self.headers.get("Range") is not None
                self.send_response(HTTPStatus.PARTIAL_CONTENT if partial else HTTPStatus.OK)
                self._headers(content_type="audio/wav", content_length=end - start + 1)
                self.send_header("Accept-Ranges", "bytes")
                if partial:
                    self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.end_headers()
                if head:
                    return
                audio.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk = audio.read(min(remaining, 64 * 1024))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                return

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
                    selected_payload = {
                        "path": str(selected_path),
                        "source_sha256": sha256_file(selected_path),
                    }
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
            limit = PROFILE_LIMIT if path.startswith("/api/v1/profile/") else 1_048_576
            if not 0 < length <= limit:
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
        if path == "/api/v1/exports/list":
            if not secrets.compare_digest(
                self.headers.get("X-EWP-CSRF", ""), self.server.gui_csrf_token
            ):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {
                            "error": {
                                "code": "GUI_CSRF_REJECTED",
                                "message": "The export request lacks the active session token.",
                            }
                        },
                    )
                )
                return
            try:
                export_list = self.server.gui_downloads.list(
                    result=str(document.get("result_path", "")),
                    revision=str(document.get("revision_path", "")),
                    translation=str(document.get("translation_path", "")),
                    directory=str(document.get("export_output_directory", "")),
                )
                self._write_response(_json_response(HTTPStatus.OK, export_list))
            except (OSError, ValueError, ApplicationError) as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {"error": {"code": "GUI_EXPORT_DOWNLOAD_INVALID", "message": str(error)}},
                    )
                )
            return
        if path.startswith("/api/v1/workdirs/"):
            if not secrets.compare_digest(
                self.headers.get("X-EWP-CSRF", ""), self.server.gui_csrf_token
            ):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {
                            "error": {
                                "code": "GUI_CSRF_REJECTED",
                                "message": (
                                    "The maintenance request lacks the active session token."
                                ),
                            }
                        },
                    )
                )
                return
            try:
                references: list[Path] = []

                def collect(value: Any) -> None:
                    if isinstance(value, str) and value.startswith(("/", "~")):
                        references.append(Path(value))
                    elif isinstance(value, dict):
                        for key, item in value.items():
                            collect(key)
                            collect(item)
                    elif isinstance(value, (tuple, list)):
                        for item in value:
                            collect(item)

                current_fields = document.get("fields", {})
                if not isinstance(current_fields, dict):
                    raise ValueError("Current workspace fields are invalid")
                collect(current_fields)
                for job in self.server.gui_transcriptions.jobs():
                    collect(job.model_dump(mode="json"))
                for _storage, _label, controller in self.server.workspace_catalogs(
                    str(document.get("storage_directory", ""))
                ):
                    for maintenance_workspace in controller.documents():
                        collect(maintenance_workspace.model_dump(mode="json"))
                protected = tuple(references)
                if path.endswith("/inventory"):
                    age = document.get("older_than_days", 0)
                    if type(age) is not int or not 0 <= age <= 36500:
                        raise ValueError("Minimum age must be a whole number between 0 and 36500")
                    maintenance_payload = self.server.gui_workdirs.inventory(
                        protected,
                        older_than_days=age,
                        reason=str(document.get("reason", "")),
                    )
                elif path.endswith("/preview"):
                    ids = document.get("ids")
                    if not isinstance(ids, list) or any(not isinstance(item, str) for item in ids):
                        raise ValueError("Select temporary work directories to preview")
                    maintenance_payload = self.server.gui_workdirs.preview(ids, protected)
                elif path.endswith("/cleanup") and document.get("confirmed") is True:
                    maintenance_payload = self.server.gui_workdirs.cleanup(
                        str(document.get("preview_token", "")), protected
                    )
                else:
                    raise ValueError("Preview and confirm temporary work directory cleanup")
                self._write_response(_json_response(HTTPStatus.OK, maintenance_payload))
            except (OSError, ValueError, ApplicationError) as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {"error": {"code": "GUI_WORKDIR_INVALID", "message": str(error)}},
                    )
                )
            return
        if path in {"/api/v1/media/probe", "/api/v1/media/discover"}:
            if not secrets.compare_digest(
                self.headers.get("X-EWP-CSRF", ""), self.server.gui_csrf_token
            ):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {"error": {"code": "GUI_CSRF_REJECTED", "message": "Invalid session."}},
                    )
                )
                return
            try:
                media_method = (
                    self.server.gui_inputs.probe
                    if path.endswith("/probe")
                    else self.server.gui_inputs.discover
                )
                media_payload = media_method(str(document.get("path", "")))
                self._write_response(_json_response(HTTPStatus.OK, media_payload))
            except (ValueError, OSError, ApplicationError) as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {"error": {"code": "GUI_MEDIA_SELECTION_INVALID", "message": str(error)}},
                    )
                )
            return
        if path.startswith("/api/v1/projects/"):
            self._handle_projects_request(path, document)
            return
        if path.startswith("/api/v1/profile/"):
            self._handle_profile_request(path, document)
            return
        if path == "/api/v1/select-path":
            if not secrets.compare_digest(
                self.headers.get("X-EWP-CSRF", ""), self.server.gui_csrf_token
            ):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {"error": {"code": "GUI_CSRF_REJECTED", "message": "Invalid session."}},
                    )
                )
                return
            try:
                kind = document.get("kind")
                if kind not in {"file", "directory"}:
                    raise ValueError("Choose file or directory selection")
                native_selected = (
                    _select_local_directory() if kind == "directory" else select_native_file()
                )
                native_selected_path = (
                    str(
                        self.server.gui_workflows.resolve_allowed_path(
                            native_selected, directory=kind == "directory"
                        )
                    )
                    if native_selected
                    else None
                )
                self._write_response(_json_response(HTTPStatus.OK, {"path": native_selected_path}))
            except (ValueError, OSError) as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {"error": {"code": "GUI_NATIVE_PICKER_UNAVAILABLE", "message": str(error)}},
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
        if path.startswith("/api/v1/managed-sources/"):
            supplied = self.headers.get("X-EWP-CSRF", "")
            if not secrets.compare_digest(supplied, self.server.gui_csrf_token):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {
                            "error": {
                                "code": "GUI_CSRF_REJECTED",
                                "message": (
                                    "The managed-source request lacks the active session token."
                                ),
                            }
                        },
                    )
                )
                return
            try:
                output_value = document.get("output_directory")
                storage_value = document.get("storage_directory", "")
                if not isinstance(output_value, str) or not output_value.strip():
                    raise ValueError("Choose the shared output directory to inventory")
                if not isinstance(storage_value, str):
                    raise ValueError("Workspace storage directory is invalid")
                output_directory = self.server.gui_workflows.resolve_allowed_path(
                    output_value, directory=True
                )
                workspace_documents = tuple(
                    workspace
                    for _storage, _label, controller in self.server.workspace_catalogs(
                        storage_value
                    )
                    for workspace in controller.documents()
                )
                managed_queue_jobs = self.server.gui_transcriptions.jobs()
                managed_workspaces = workspace_documents
                if path == "/api/v1/managed-sources/inventory":
                    managed_sources = inventory_managed_sources(
                        output_directory,
                        queue_jobs=managed_queue_jobs,
                        workspaces=managed_workspaces,
                    )
                    managed_payload = {
                        "sources": [item.model_dump(mode="json") for item in managed_sources],
                        "workspace_count": len(workspace_documents),
                    }
                elif path == "/api/v1/managed-sources/cleanup":
                    managed_relative_paths = document.get("relative_paths")
                    if (
                        document.get("confirmed") is not True
                        or not isinstance(managed_relative_paths, list)
                        or not 1 <= len(managed_relative_paths) <= 100
                        or any(
                            not isinstance(item, str) or not item for item in managed_relative_paths
                        )
                    ):
                        raise ValueError("Select managed copies and confirm permanent cleanup")
                    managed_removed = cleanup_managed_sources(
                        output_directory,
                        tuple(managed_relative_paths),
                        queue_jobs=managed_queue_jobs,
                        workspaces=managed_workspaces,
                    )
                    managed_payload = {"removed": list(managed_removed)}
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
            except GuiManagedSourceCleanupError as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.CONFLICT,
                        {
                            "error": {
                                "code": "GUI_MANAGED_SOURCE_CLEANUP_REFUSED",
                                "message": str(error),
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
                                "code": "GUI_MANAGED_SOURCE_REQUEST_INVALID",
                                "message": str(error),
                            }
                        },
                    )
                )
                return
            self._write_response(_json_response(HTTPStatus.OK, managed_payload))
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
                if path == "/api/v1/workspaces/locations":
                    locations_registry = self.server.gui_workspace_locations
                    if document.get("remember") is True:
                        output = document.get("output_directory", "")
                        storage = document.get("workspace_directory", "")
                        if not isinstance(output, str) or not isinstance(storage, str):
                            raise ValueError("Workspace storage directory is invalid")
                        locations_registry.remember(
                            output_directory=output, storage_directory=storage
                        )
                    payload: dict[str, object] = {
                        "locations": locations_registry.available().model_dump(mode="json")
                    }
                elif path == "/api/v1/workspaces/list":
                    payload = {
                        "workspaces": [
                            {
                                **item.model_dump(mode="json"),
                                "storage_directory": catalog_storage,
                                "workspace_file": str(controller.document_path(item.workspace_id)),
                                "catalog": catalog_label,
                            }
                            for catalog_storage, catalog_label, controller in (
                                self.server.workspace_catalogs(storage_directory)
                            )
                            for item in controller.list()
                        ]
                    }
                elif path == "/api/v1/workspaces/save":
                    fields = document.get("fields")
                    if not isinstance(fields, dict):
                        raise ValueError("Workspace fields must be an object")
                    name = str(document.get("name", ""))
                    workspace_id = str(document.get("workspace_id", ""))
                    catalogs = tuple(
                        controller
                        for _, _, controller in self.server.workspace_catalogs(storage_directory)
                    )
                    workspaces.ensure_name_available(
                        name, workspace_id=workspace_id, catalogs=catalogs
                    )
                    pending_media = self._preserve_workspace_media(
                        document.get("pending_media", []), fields
                    )
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
                        if job.status in {"completed", "failed", "cancelled"}
                        and job.source_sha256
                        and not workspaces.is_temporary_selection(job.input_path)
                        and not workspaces.is_temporary_selection(job.result_path or "")
                    )
                    saved = workspaces.save(
                        name=name,
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
                                "speech": job.speech.model_dump(mode="json"),
                                **({"recording_id": job.recording_id} if job.recording_id else {}),
                                **(
                                    {"selected_streams": job.selected_streams}
                                    if job.selected_streams
                                    else {}
                                ),
                                **(
                                    {"group_sources": job.group_sources}
                                    if job.group_sources
                                    else {}
                                ),
                            }
                            for job in durable_staged
                        ],
                        terminal_jobs=[job.model_dump(mode="json") for job in durable_terminal],
                        pending_media=pending_media,
                        workspace_id=workspace_id,
                        omit_unavailable=True,
                        catalogs=catalogs,
                    )
                    locations = getattr(self.server, "gui_workspace_locations", None)
                    if isinstance(locations, GuiWorkspaceLocations):
                        output = str(saved.fields.get("output-path", ""))
                        catalog = str(workspaces.state_directory)
                        locations.remember(
                            output_directory=output,
                            storage_directory="" if catalog == output else catalog,
                        )
                    unavailable_fields_omitted = sum(
                        isinstance(value, str)
                        and bool(value.strip())
                        and saved.fields.get(name) == ""
                        for name, value in fields.items()
                    )
                    unavailable_jobs_omitted = (
                        len(durable_staged)
                        + len(durable_terminal)
                        - len(saved.staged_jobs)
                        - len(saved.terminal_jobs)
                    )
                    payload = {
                        "workspace": saved.model_dump(mode="json"),
                        "workspace_file": str(workspaces.document_path(saved.workspace_id)),
                        "temporary_jobs_omitted": sum(
                            job.status in {"staged", "completed", "failed", "cancelled"}
                            for job in queue_jobs
                        )
                        - len(durable_staged)
                        - len(durable_terminal),
                        "unavailable_fields_omitted": unavailable_fields_omitted,
                        "unavailable_jobs_omitted": unavailable_jobs_omitted,
                    }
                elif path == "/api/v1/workspaces/restore-progress":
                    payload = self.server.gui_restore.snapshot(str(document.get("restore_id", "")))
                elif path == "/api/v1/workspaces/load":
                    self.server.gui_transcriptions.revoke_cloud_consent()
                    restore_id = str(document.get("restore_id") or secrets.token_urlsafe(24))
                    self.server.gui_restore.start(restore_id)
                    succeeded = False
                    try:
                        loaded = workspaces.load(
                            str(document.get("workspace_id", "")),
                            on_read=self.server.gui_restore.total,
                        )
                        restored_terminal = self._restore_workspace_terminal_jobs(
                            loaded.terminal_jobs
                        )
                        self.server.gui_restore.advance(len(loaded.terminal_jobs))
                        restored = self._restore_workspace_staged_jobs(
                            loaded.staged_jobs, progress=self.server.gui_restore.advance
                        )
                        payload = {
                            "workspace": loaded.model_dump(mode="json"),
                            "workspace_file": str(workspaces.document_path(loaded.workspace_id)),
                            "restored_staged_jobs": restored,
                            "restored_terminal_jobs": restored_terminal,
                        }
                        locations = getattr(self.server, "gui_workspace_locations", None)
                        if isinstance(locations, GuiWorkspaceLocations):
                            output = str(loaded.fields.get("output-path", ""))
                            catalog = str(workspaces.state_directory)
                            locations.remember(
                                output_directory=output,
                                storage_directory="" if catalog == output else catalog,
                            )
                        succeeded = True
                    finally:
                        self.server.gui_restore.finish(restore_id, succeeded=succeeded)
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
                                "code": (
                                    "GUI_WORKSPACE_NAME_EXISTS"
                                    if isinstance(error, GuiWorkspaceNameExists)
                                    else "GUI_WORKSPACE_REQUEST_INVALID"
                                ),
                                "message": str(error),
                            }
                        },
                    )
                )
                return
            self._write_response(_json_response(HTTPStatus.OK, payload))
            return
        if path in {"/api/v1/speech/check", "/api/v1/speech/estimate"}:
            if not secrets.compare_digest(
                self.headers.get("X-EWP-CSRF", ""), self.server.gui_csrf_token
            ):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {"error": {"code": "GUI_CSRF_REJECTED", "message": "Invalid session."}},
                    )
                )
                return
            try:
                key = self.server.gui_openrouter_api_key or os.environ.get(
                    self.server.gui_openrouter_api_key_env, ""
                )
                if path.endswith("/check") and document.get("api_key"):
                    key = validate_api_key(document["api_key"])
                speech_payload = (
                    self.server.gui_speech.check_key(key)
                    if path.endswith("/check")
                    else self.server.gui_speech.refresh(document.get("items", []))
                )
                self._write_response(_json_response(HTTPStatus.OK, speech_payload))
            except (ValueError, OSError, ApplicationError) as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {"error": {"code": "GUI_ASR_CHECK_FAILED", "message": str(error)}},
                    )
                )
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
            try:
                action = document.get("action", "session")
                persistence = "server-session-only"
                if action == "status":
                    self._write_response(
                        _json_response(
                            HTTPStatus.OK,
                            {
                                "os_store_available": self.server.gui_credentials.available(),
                                "configured": bool(self.server.gui_openrouter_api_key),
                            },
                        )
                    )
                    return
                if action == "session":
                    key = validate_api_key(document.get("api_key"))
                elif action in {"save", "use", "remove"}:
                    supplied_key = (
                        validate_api_key(document.get("api_key")) if action == "save" else ""
                    )
                    key = self.server.gui_credentials.perform(str(action), supplied_key)
                    persistence = "os-store" if action != "remove" else "removed"
                elif action == "clear-session":
                    key = ""
                else:
                    raise ValueError("Unknown credential action.")
                self.server.gui_openrouter_api_key = key
                self._write_response(
                    _json_response(
                        HTTPStatus.OK,
                        {
                            "configured": bool(
                                key
                                or os.environ.get(
                                    self.server.gui_openrouter_api_key_env, ""
                                ).strip()
                            ),
                            "persistence": persistence,
                            "environment_configured": bool(
                                os.environ.get(self.server.gui_openrouter_api_key_env, "").strip()
                            ),
                        },
                    )
                )
            except ValueError as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {"error": {"code": "GUI_CREDENTIAL_INVALID", "message": str(error)}},
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
                if path == "/api/v1/reviews/playback":
                    payload = self.server.gui_media.prepare(
                        result, str(document.get("source_id", ""))
                    )
                elif path == "/api/v1/reviews/playback-position":
                    anchor_index, block_index = (
                        document.get("anchor_index"),
                        document.get("block_index"),
                    )
                    if type(anchor_index) is not int or type(block_index) is not int:
                        raise ValueError("Choose an existing transcript block.")
                    payload = self.server.gui_reviews.playback_position(
                        str(document.get("review_path", "")),
                        result,
                        anchor_index,
                        block_index,
                        expected_sha256=str(document.get("review_sha256", "")),
                    )
                elif path == "/api/v1/reviews/prepare":
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
                    self.server.gui_transcriptions.clear_workflow_error(result, "review")
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
                        speaker_colors=document.get("speaker_colors"),
                    )
                    self.server.gui_downloads.register(
                        result=result,
                        revision=str(document.get("revision_path", "")),
                        paths=cast(list[str], payload["written"]),
                    )
                    self.server.gui_transcriptions.clear_workflow_error(result, "original_export")
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
                if path in {
                    "/api/v1/reviews/prepare",
                    "/api/v1/reviews/load",
                    "/api/v1/reviews/session/restore",
                    "/api/v1/reviews/save",
                    "/api/v1/reviews/preview",
                    "/api/v1/reviews/apply",
                }:
                    self.server.gui_transcriptions.skip_workflow_stage(
                        str(payload.get("result_path", result)), "correction"
                    )
            except ApplicationError as error:
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {"error": {"code": error.code, "message": str(error)}},
                    )
                )
                return
            except FileNotFoundError as error:
                missing = error.filename or str(error)
                self._write_response(
                    _json_response(
                        HTTPStatus.BAD_REQUEST,
                        {
                            "error": {
                                "code": "GUI_REVIEW_FILE_MISSING",
                                "message": (
                                    f"A required review source file no longer exists: {missing}. "
                                    "Add the original canonical *_results.json to a workflow "
                                    "queue again."
                                ),
                            }
                        },
                    )
                )
                return
            except (OSError, ValueError) as error:
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
                    job.status in {"queued", "running", "cancel_requested"}
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
                    self.server.gui_transcriptions.clear_workflow_error(
                        str(document.get("result_path", "")), "correction"
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
                        job.status in {"queued", "running", "cancel_requested"}
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
                    self.server.gui_transcriptions.clear_workflow_error(
                        str(document.get("result_path", "")), "assisted_translation"
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
                    payload = self.server.gui_translation_reviews.preview(
                        **common,
                        allow_empty_units=document.get("allow_empty_units") is True,
                    )
                elif path.endswith("/apply"):
                    if document.get("confirmed") is not True:
                        raise ValueError("Semantic manual verification confirmation is required")
                    payload = self.server.gui_translation_reviews.apply(
                        **common,
                        output=str(document.get("translation_output_directory", "")),
                        allow_empty_units=document.get("allow_empty_units") is True,
                    )
                    self.server.gui_transcriptions.clear_workflow_error(
                        common["result"], "translation"
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
                    self.server.gui_downloads.register(
                        result=common["result"],
                        revision=common["revision"],
                        translation=str(document.get("translation_path", "")),
                        paths=[
                            *cast(list[str], payload["written"]),
                            *cast(list[str], payload["skipped"]),
                        ],
                    )
                    self.server.gui_transcriptions.clear_workflow_error(
                        common["result"], "translated_export"
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
                        str(document.get("catalog_directory", "")),
                        include_hidden=document.get("include_hidden") is True,
                    )
                elif path.endswith("/view"):
                    payload = self.server.gui_library.view(str(document.get("path", "")))
                elif path.endswith("/export"):
                    payload = {
                        **self.server.gui_library.export_dictionary(str(document.get("path", "")))
                    }
                elif path.endswith("/import"):
                    if not isinstance(document.get("payload"), str):
                        raise ValueError("Dictionary file must contain JSON text")
                    payload = self.server.gui_library.import_dictionary(
                        payload=document["payload"], directory=str(document.get("directory", ""))
                    )
                elif path.endswith("/visibility"):
                    if not isinstance(document.get("visible"), bool):
                        raise ValueError("Dictionary visibility must be true or false")
                    payload = self.server.gui_library.visibility(
                        path=str(document.get("path", "")),
                        digest=str(document.get("sha256", "")),
                        visible=document["visible"],
                    )
                elif path.endswith("/edition"):
                    if not isinstance(document.get("document"), dict):
                        raise ValueError("Dictionary document must be a JSON object")
                    payload = self.server.gui_library.edition(
                        document=document["document"],
                        directory=str(document.get("directory", "")),
                        previous_path=str(document.get("previous_path", "")),
                        previous_sha256=str(document.get("previous_sha256", "")),
                    )
                elif path.endswith("/profiles"):
                    payload = self.server.gui_library.profiles()
                elif path.endswith("/profile-save"):
                    colors = document.get("colors")
                    if not isinstance(colors, list) or not all(
                        isinstance(color, str) for color in colors
                    ):
                        raise ValueError("Profile colors must be an array of strings")
                    payload = self.server.gui_library.save_profile(
                        name=str(document.get("name", "")), colors=colors
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
        if path in {"/api/v1/dependencies/test", "/api/v1/dependencies/doctor"}:
            supplied = self.headers.get("X-EWP-CSRF", "")
            if not secrets.compare_digest(supplied, self.server.gui_csrf_token):
                self._write_response(
                    _json_response(
                        HTTPStatus.FORBIDDEN,
                        {
                            "error": {
                                "code": "GUI_CSRF_REJECTED",
                                "message": "The dependency test lacks the active session token.",
                            }
                        },
                    )
                )
                return
            native_test = path.endswith("/test")
            if not native_test and not getattr(self.server, "gui_dependencies_tested", False):
                self._write_response(
                    _json_response(
                        HTTPStatus.CONFLICT,
                        {
                            "error": {
                                "code": "GUI_DEPENDENCY_TEST_REQUIRED",
                                "message": "Run Test local dependencies first.",
                            }
                        },
                    )
                )
                return
            diagnostics = doctor(config=load_config(), test_speech_runtime=native_test)
            if native_test:
                self.server.gui_dependencies_tested = True
            self._write_response(_json_response(HTTPStatus.OK, diagnostics.model_dump(mode="json")))
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
            if path in {"/api/v1/transcriptions/cancel", "/api/v1/transcriptions/retry"}:
                try:
                    method = (
                        self.server.gui_transcriptions.cancel
                        if path.endswith("/cancel")
                        else self.server.gui_transcriptions.retry
                    )
                    job = method(str(document.get("job_id", "")))
                    self._write_response(
                        _json_response(HTTPStatus.OK, {"job": job.model_dump(mode="json")})
                    )
                except ValueError as error:
                    self._write_response(
                        _json_response(
                            HTTPStatus.CONFLICT,
                            {"error": {"code": "GUI_QUEUE_ACTION_REJECTED", "message": str(error)}},
                        )
                    )
                return
            if path == "/api/v1/transcriptions/cloud-consent":
                try:
                    if document.get("cloud_confirmed") is not True:
                        self.server.gui_transcriptions.revoke_cloud_consent()
                        payload = {"cloud_consent_token": ""}
                    else:
                        identifiers = document.get("cloud_job_ids")
                        if not isinstance(identifiers, list) or not all(
                            isinstance(identifier, str) for identifier in identifiers
                        ):
                            raise ValueError("Cloud queue selection is invalid")
                        token = self.server.gui_transcriptions.authorize_cloud_start(
                            tuple(identifiers)
                        )
                        payload = {"cloud_consent_token": token}
                    self._write_response(_json_response(HTTPStatus.OK, payload))
                except ValueError as error:
                    self._write_response(
                        _json_response(
                            HTTPStatus.BAD_REQUEST,
                            {
                                "error": {
                                    "code": "GUI_CLOUD_CONSENT_REQUIRED",
                                    "message": str(error),
                                }
                            },
                        )
                    )
                return
            if path == "/api/v1/transcriptions/start":
                try:
                    allow_cloud = document.get("cloud_confirmed") is True
                    start_token_value = document.get("cloud_consent_token")
                    start_token = start_token_value if isinstance(start_token_value, str) else ""
                    cloud_key = self.server.gui_transcriptions.cloud_start_key(
                        allow_cloud=allow_cloud, token=start_token
                    )
                    if cloud_key is not None:
                        try:
                            self.server.gui_speech.check_key(cloud_key)
                        except (SpeechEngineError, ValueError):
                            raise GuiCloudPreflightFailed(
                                "OpenRouter key check failed before queue start. "
                                "Check the key and connection; no audio was sent."
                            ) from None
                    count = self.server.gui_transcriptions.start(
                        allow_cloud=allow_cloud,
                        cloud_consent_token=start_token,
                        validated_api_key=cloud_key,
                    )
                except ValueError as error:
                    if isinstance(error, (GuiCloudKeyRequired, GuiCloudPreflightFailed)):
                        self.server.gui_transcriptions.revoke_cloud_consent()
                    self._write_response(
                        _json_response(
                            HTTPStatus.BAD_REQUEST,
                            {
                                "error": {
                                    "code": getattr(error, "code", "GUI_CLOUD_CONSENT_REQUIRED"),
                                    "message": str(error),
                                }
                            },
                        )
                    )
                    return
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
            if path == "/api/v1/transcriptions/remove-completed":
                if document.get("confirmed") is not True:
                    self._write_response(
                        _json_response(
                            HTTPStatus.BAD_REQUEST,
                            {
                                "error": {
                                    "code": "GUI_QUEUE_REMOVE_INVALID",
                                    "message": "Confirm completed task removal.",
                                }
                            },
                        )
                    )
                    return
                completed_ids = self.server.gui_transcriptions.remove_completed()
                self._write_response(
                    _json_response(HTTPStatus.OK, {"removed": list(completed_ids)})
                )
                return
            if path == "/api/v1/transcriptions/remove-batch":
                job_ids = document.get("job_ids")
                if (
                    document.get("confirmed") is not True
                    or not isinstance(job_ids, list)
                    or not 1 <= len(job_ids) <= 50
                    or any(not isinstance(item, str) or not item for item in job_ids)
                    or len(set(job_ids)) != len(job_ids)
                ):
                    self._write_response(
                        _json_response(
                            HTTPStatus.BAD_REQUEST,
                            {
                                "error": {
                                    "code": "GUI_QUEUE_REMOVE_INVALID",
                                    "message": (
                                        "Select one or more unique inactive queue items and "
                                        "confirm removal."
                                    ),
                                }
                            },
                        )
                    )
                    return
                try:
                    removed_ids, not_found_ids = self.server.gui_transcriptions.remove_inactive(
                        tuple(job_ids)
                    )
                except ValueError as error:
                    self._write_response(
                        _json_response(
                            HTTPStatus.CONFLICT,
                            {"error": {"code": "GUI_QUEUE_ACTIVE", "message": str(error)}},
                        )
                    )
                    return
                self._write_response(
                    _json_response(
                        HTTPStatus.OK,
                        {"removed": list(removed_ids), "not_found": list(not_found_ids)},
                    )
                )
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
            if path == "/api/v1/transcriptions/workflow-success":
                result_path = document.get("result_path")
                stage = document.get("stage")
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
                ):
                    self._write_response(
                        _json_response(
                            HTTPStatus.BAD_REQUEST,
                            {
                                "error": {
                                    "code": "GUI_WORKFLOW_SUCCESS_INVALID",
                                    "message": "The workflow success report is malformed.",
                                }
                            },
                        )
                    )
                    return
                cleared = self.server.gui_transcriptions.clear_workflow_error(
                    result_path, cast(WorkflowStageName, stage)
                )
                self._write_response(_json_response(HTTPStatus.OK, {"cleared": cleared}))
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
                group_options = self.server.gui_workflows.resolve_group_options(document)
                group_paths = group_options.get("explicit_group_paths", ())
                selected_streams = {
                    str(path): index
                    for path, index in group_options.get("selected_streams", {}).items()
                }
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
                speech = SpeechConfig.model_validate(document.get("speech", {}))
                plan = self.server.gui_workflows.completed_plan(
                    input_path,
                    output_path,
                    language=language,
                    speaker_count=speaker_count,
                    group_paths=tuple(str(path) for path in group_paths),
                    group_id=group_options.get("explicit_group_id"),
                    recording_id=group_options.get("recording_id"),
                    selected_streams=selected_streams,
                    speech=speech,
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
                                        "Check 'I reviewed the plan' before adding "
                                        "jobs to the queue."
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
                group_sources: dict[str, str] = {}
                durable_streams: dict[str, int] = {}
                if group_paths:
                    if group_options["explicit_group_id"] != planned_job_id:
                        raise ValueError("The group identity differs from the reviewed plan")
                    assert isinstance(sources, list)
                    reviewed = {
                        item["fingerprint"]["path"]: item["fingerprint"]["sha256"]
                        for item in sources
                    }
                    if len(sources) != len(group_paths):
                        raise ValueError("The group differs from the reviewed plan")
                    for source_path in group_paths:
                        original_path = str(source_path)
                        digest = sha256_file(source_path)
                        if digest != reviewed.get(str(source_path)):
                            raise ValueError("A grouped source changed after dry-run")
                        if self.server.gui_transcriptions.contains_active_input(source_path):
                            raise ValueError("A grouped source is already staged or running")
                        if self.server.gui_selections.root in source_path.parents:
                            source_path, preserved = preserve_gui_selected_source(
                                source_path, output_directory=output_path, category="media"
                            )
                            if preserved != digest:
                                raise ValueError("A grouped source changed while preserving it")
                        if self.server.gui_transcriptions.contains_active_input(source_path):
                            raise ValueError("A grouped source is already staged or running")
                        group_sources[str(source_path)] = digest
                        if original_path in selected_streams:
                            durable_streams[str(source_path)] = selected_streams[original_path]
                    input_path = Path(next(iter(group_sources)))
                    source_sha256 = group_sources[str(input_path)]
                original_input = str(input_path)
                if not group_paths and self.server.gui_selections.root in input_path.parents:
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
                    group_sources=group_sources,
                    recording_id=group_options.get("recording_id"),
                    speech=speech,
                    selected_streams=(
                        durable_streams
                        if group_paths
                        else {str(input_path): selected_streams[original_input]}
                        if original_input in selected_streams
                        else {}
                    ),
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

    def _handle_projects_request(self, path: str, document: dict[str, Any]) -> None:
        if not secrets.compare_digest(
            self.headers.get("X-EWP-CSRF", ""), self.server.gui_csrf_token
        ):
            self._write_response(
                _json_response(
                    HTTPStatus.FORBIDDEN,
                    {"error": {"code": "GUI_CSRF_REJECTED", "message": "Invalid session."}},
                )
            )
            return
        service = self.server.gui_projects
        try:
            action = path.rsplit("/", 1)[-1]
            if action == "list":
                payload = service.listing()
            elif action == "location":
                service.location(
                    name=str(document.get("name", "")),
                    kind=str(document.get("kind", "")),
                    path=str(document.get("path", "")),
                    remove=document.get("remove") is True,
                )
                payload = service.listing()
            elif action == "remember":
                service.remember(
                    output_root=str(document.get("output_root", "")),
                    result_path=str(document.get("result_path", "")),
                    name=str(document.get("name", "")),
                )
                payload = service.listing()
            elif action == "forget":
                service.forget(str(document.get("id", "")))
                payload = service.listing()
            elif action == "scan":
                payload = service.scan(str(document.get("directory", "")))
            elif action == "import-results":
                items = document.get("items")
                if not isinstance(items, list) or not 1 <= len(items) <= 50:
                    raise ValueError("Select 1–50 canonical results")
                output = service.resolve(str(document.get("output_root", "")), directory=True)
                checked = []
                for item in items:
                    if not isinstance(item, dict):
                        raise ValueError("Canonical selection is invalid")
                    source = service.resolve(str(item.get("path", "")))
                    if source.stat().st_size > 64 * 1024 * 1024:
                        raise ValueError("Canonical result exceeds scan limit")
                    canonical = require_completed_canonical_result(source)
                    digest = sha256_file(source)
                    if digest != item.get("sha256"):
                        raise ValueError("Canonical result changed since scanning; scan again")
                    checked.append((source, canonical, digest))
                added = 0
                for source, canonical, digest in checked:
                    preserved, copied_digest = preserve_gui_selected_source(
                        source, output_directory=output, category="canonical"
                    )
                    if copied_digest != digest:
                        raise ValueError("Canonical result changed while copying; scan again")
                    _, imported = self.server.gui_transcriptions.register_completed_result(
                        preserved,
                        output_directory=output,
                        planned_job_id=canonical.job_id,
                        language=LanguageMode(canonical.episode.language),
                        source_sha256=digest,
                    )
                    added += int(imported)
                payload = {"added": added}
            else:
                raise ValueError("Unknown project action")
        except (OSError, ValueError) as error:
            self._write_response(
                _json_response(
                    HTTPStatus.BAD_REQUEST,
                    {"error": {"code": "GUI_PROJECT_INVALID", "message": str(error)}},
                )
            )
            return
        self._write_response(_json_response(HTTPStatus.OK, payload))

    def _handle_profile_request(self, path: str, document: dict[str, Any]) -> None:
        if not secrets.compare_digest(
            self.headers.get("X-EWP-CSRF", ""), self.server.gui_csrf_token
        ):
            self._write_response(
                _json_response(
                    HTTPStatus.FORBIDDEN,
                    {
                        "error": {
                            "code": "GUI_CSRF_REJECTED",
                            "message": "The profile request lacks the active session token.",
                        }
                    },
                )
            )
            return
        payload: dict[str, Any]
        try:
            if path == "/api/v1/profile/save":
                catalogs = self.server.workspace_catalogs(
                    str(document.get("storage_directory", ""))
                )
                workspaces = tuple(
                    item for _, _, controller in catalogs for item in controller.documents()
                )
                include_dictionaries = document.get("include_dictionaries", True)
                if type(include_dictionaries) is not bool:
                    raise ValueError("Dictionary export option must be true or false")
                directories = (
                    [str(document.get("dictionary_directory", "dictionaries"))]
                    if include_dictionaries
                    else []
                )
                # Dictionaries referenced by workspace fields are included even when
                # they live outside the currently selected catalog.
                dictionary_paths = [
                    item["path"]
                    for directory in directories
                    for item in self.server.gui_dictionaries.catalog(
                        directory, include_hidden=True
                    )["items"]
                ]
                fields = document.get("fields", {})
                preferences = document.get("preferences", {})
                if not isinstance(fields, dict) or not isinstance(preferences, dict):
                    raise ValueError("Profile preferences and fields must be objects")
                for saved_fields in (
                    [fields, *(item.fields for item in workspaces)] if include_dictionaries else []
                ):
                    for key in (
                        "correction-dictionary",
                        "translation-dictionary",
                        "dictionary-previous",
                    ):
                        value = saved_fields.get(key)
                        if isinstance(value, str) and value and Path(value).is_file():
                            dictionary_paths.append(value)
                profile = self.server.gui_profiles.capture(
                    name=str(document.get("name", "")),
                    preferences=preferences,
                    fields=fields,
                    workspaces=workspaces,
                    dictionary_paths=dictionary_paths,
                )
                payload = {"profile": profile.model_dump(mode="json")}
            elif path == "/api/v1/profile/load":
                payload = self.server.gui_profiles.load()
            elif path == "/api/v1/profile/import":
                if not isinstance(document.get("profile"), dict):
                    raise ValueError("Profile document must be an object")
                payload = self.server.gui_profiles.restore(document["profile"])
            else:
                raise ValueError("Unknown user profile action")
        except (OSError, ValueError) as error:
            self._write_response(
                _json_response(
                    HTTPStatus.BAD_REQUEST,
                    {"error": {"code": "GUI_PROFILE_INVALID", "message": str(error)}},
                )
            )
            return
        self._write_response(_json_response(HTTPStatus.OK, payload))
        return

    def _preserve_workspace_media(
        self, items: object, fields: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Preserve pending picker media on explicit Save, before validating form paths."""
        if not isinstance(items, list) or len(items) > 300:
            raise ValueError("Workspace pending media selection is invalid")
        if not items:
            return []
        if not str(fields.get("output-path", "")).strip():
            raise ValueError("Choose an output directory before saving pending media")
        output = self.server.gui_workflows.resolve_allowed_path(
            str(fields.get("output-path", "")), directory=True
        )
        clean = []
        for raw in items:
            if not isinstance(raw, dict):
                raise ValueError("Workspace pending media selection is invalid")
            original = str(raw.get("path", ""))
            source = self.server.gui_workflows.resolve_allowed_path(original)
            digest = sha256_file(source)
            if raw.get("source_sha256") and raw["source_sha256"] != digest:
                raise ValueError("A pending source changed since this workspace was saved")
            media = GuiWorkspaceMedia.model_validate({**raw, "source_sha256": digest})
            if self.server.gui_selections.root in source.parents:
                source, preserved = preserve_gui_selected_source(
                    source, output_directory=output, category="media"
                )
                if digest != preserved:
                    raise ValueError("A pending source changed while preserving it")
            clean.append(media.model_copy(update={"path": str(source)}).model_dump(mode="json"))
            if fields.get("input-path") == original:
                fields["input-path"] = str(source)
        return clean

    def _restore_workspace_staged_jobs(
        self,
        staged_jobs: tuple[dict[str, Any], ...],
        *,
        progress: Callable[[int], None] | None = None,
    ) -> int:
        """Rebuild only hash-validated staged jobs after a GUI restart."""

        if not staged_jobs:
            return 0
        active = [
            job
            for job in self.server.gui_transcriptions.jobs()
            if job.status in {"staged", "queued", "running", "cancel_requested"}
        ]
        expected = {
            (
                item["planned_job_id"],
                item["source_sha256"],
                tuple(sorted(item.get("group_sources", {}).items())),
                tuple(sorted(item.get("selected_streams", {}).items())),
                item.get("recording_id"),
                SpeechConfig.model_validate(item.get("speech", {})).model_dump_json(),
            )
            for item in staged_jobs
        }
        if active:
            actual = {
                (
                    job.planned_job_id,
                    job.source_sha256,
                    tuple(sorted(job.group_sources.items())),
                    tuple(sorted(job.selected_streams.items())),
                    job.recording_id,
                    job.speech.model_dump_json(),
                )
                for job in active
            }
            if actual == expected:
                if progress is not None:
                    progress(len(staged_jobs))
                return 0
            raise ValueError(
                "An active transcription queue cannot be replaced by saved workspace jobs"
            )
        for item in staged_jobs:
            input_path = self.server.gui_workflows.resolve_allowed_path(str(item["input_path"]))
            output_path = self.server.gui_workflows.resolve_allowed_path(
                str(item["output_directory"]), directory=True
            )
            group_sources = cast(dict[str, str], item.get("group_sources", {}))
            for path, digest in group_sources.items():
                resolved = self.server.gui_workflows.resolve_allowed_path(path)
                if sha256_file(resolved) != digest:
                    raise ValueError("A grouped source changed since this workspace was saved")
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
                    "speech": item.get("speech", {}),
                    **(
                        {"group_paths": list(group_sources), "group_id": item["planned_job_id"]}
                        if group_sources
                        else (
                            {"recording_id": item["recording_id"]}
                            if item.get("recording_id")
                            else {}
                        )
                    ),
                    **(
                        {"selected_streams": item["selected_streams"]}
                        if item.get("selected_streams")
                        else {}
                    ),
                },
            )
            jobs = operation.result.get("jobs") if operation.result else None
            if operation.status != "completed" or not isinstance(jobs, list) or len(jobs) != 1:
                raise ValueError("A staged job could not be safely replanned")
            planned = jobs[0]
            outputs = planned.get("outputs") if isinstance(planned, dict) else None
            if not isinstance(planned, dict) or planned.get("job_id") != item["planned_job_id"]:
                raise ValueError("A staged job plan changed since this workspace was saved")
            failed_path = Path(str(item["planned_result_path"])).with_suffix(".failed.json")
            state = None
            try:
                failed_path = self.server.gui_workflows.resolve_allowed_path(str(failed_path))
                with failed_path.open(encoding="utf-8") as failure:
                    raw = failure.read(64_001)
                if len(raw) > 64_000:
                    raise ValueError("Saved job state is too large")
                state = JobStateRecord.model_validate_json(raw)
            except FileNotFoundError:
                pass
            if state is not None and (
                state.job_id == item["planned_job_id"]
                and state.episode_signature_sha256 == planned.get("episode_signature_sha256")
                and state.status.value in {"failed", "cancelled"}
            ):
                recovered = GuiTranscriptionJob(
                    job_id=str(uuid4()),
                    status=state.status.value,
                    input_path=str(input_path),
                    output_directory=str(output_path),
                    planned_job_id=str(item["planned_job_id"]),
                    planned_result_path=str(item["planned_result_path"]),
                    source_sha256=str(item["source_sha256"]),
                    group_sources=group_sources,
                    selected_streams=item.get("selected_streams", {}),
                    recording_id=item.get("recording_id"),
                    speech=SpeechConfig.model_validate(item.get("speech", {})),
                    language=language,
                    speaker_count=speaker_count,
                    created_at=state.created_at,
                    updated_at=state.updated_at,
                    error={
                        "code": state.failure_code or "GUI_TRANSCRIPTION_FAILED",
                        "message": state.failure_message or "Retained transcription failure",
                    },
                )
                self.server.gui_transcriptions.replace_terminal_jobs(
                    (
                        *(
                            job
                            for job in self.server.gui_transcriptions.jobs()
                            if job.status in {"completed", "failed", "cancelled"}
                            and not (
                                job.planned_result_path == recovered.planned_result_path
                                and job.source_sha256 == recovered.source_sha256
                            )
                        ),
                        recovered,
                    )
                )
                if progress is not None:
                    progress(1)
                continue
            if not isinstance(outputs, dict) or not isinstance(outputs.get("results"), str):
                existing = planned.get("existing_result")
                if not isinstance(existing, dict) or not isinstance(existing.get("path"), str):
                    raise ValueError("A staged job could not be safely replanned")
                result_path = self.server.gui_workflows.resolve_allowed_path(existing["path"])
                require_completed_canonical_result(result_path)
                self.server.gui_transcriptions.register_completed_result(
                    result_path,
                    output_directory=output_path,
                    planned_job_id=str(item["planned_job_id"]),
                    language=language,
                    source_sha256=sha256_file(result_path),
                )
                if progress is not None:
                    progress(1)
                continue
            self.server.gui_transcriptions.stage(
                input_path,
                output_path,
                planned_job_id=str(item["planned_job_id"]),
                planned_result_path=str(outputs["results"]),
                source_sha256=str(item["source_sha256"]),
                group_sources=group_sources,
                selected_streams=item.get("selected_streams", {}),
                recording_id=item.get("recording_id"),
                speech=SpeechConfig.model_validate(item.get("speech", {})),
                language=language,
                speaker_count=speaker_count,
            )
            if progress is not None:
                progress(1)
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
            if job.status != "completed":
                resolve_optional_workspace_file(
                    job.input_path, self.server.gui_workflows.resolve_allowed_path
                )
            self.server.gui_workflows.resolve_allowed_path(job.output_directory, directory=True)
            resolve_optional_workspace_file(
                job.planned_result_path, self.server.gui_workflows.resolve_allowed_path
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
        try:
            self.send_response(response.status)
            self._headers(content_type=response.content_type, content_length=len(response.body))
            self.end_headers()
            self.wfile.write(response.body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
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
    if _is_wsl_environment():
        commands = [
            ["cmd.exe", "/C", "start", "", url],
            ["powershell.exe", "-NoProfile", "-Command", "Start-Process", url],
        ]
        if shutil.which("wslview"):
            commands.append(["wslview", url])
        for command in commands:
            attempts: tuple[tuple[list[str], str | None], ...]
            if command[0] == "wslview":
                executable = shutil.which("wslview")
                attempts = (([executable, url], None),) if executable else ()
            else:
                attempts = _windows_interop_attempts(command)
            if not attempts:
                failures.append(f"{command[0]} unavailable")
                continue
            for attempt, interpreter in attempts:
                try:
                    completed = subprocess.run(
                        attempt,
                        executable=interpreter,
                        check=False,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        text=True,
                        errors="replace",
                        timeout=20,
                    )
                except (OSError, subprocess.TimeoutExpired) as error:
                    launcher = (
                        f"/init → {Path(attempt[0]).name}" if interpreter else Path(attempt[0]).name
                    )
                    failures.append(f"{launcher} {type(error).__name__}: {error}")
                    continue
                if completed.returncode == 0:
                    return
                failures.append(
                    f"{'/init → ' if interpreter else ''}{Path(attempt[0]).name} "
                    f"exit {completed.returncode}"
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
