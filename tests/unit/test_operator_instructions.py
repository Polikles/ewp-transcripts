"""Keep the general-user operator entry point complete and discoverable."""

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = ROOT / "Instructions" / "README.md"


def test_primary_readme_links_complete_operator_runbook() -> None:
    primary = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Instructions/README.md" in primary
    assert "./scripts/install-fresh-ubuntu.sh --install" in primary
    assert "./scripts/setup-models.sh" in primary
    assert "docs/gui/README.md" in primary
    assert "docs/gui/pl/README.md" in primary
    assert "scripts/setup-windows.ps1 -Install" in primary
    assert RUNBOOK.is_file()


def test_operator_runbook_covers_every_shipped_command_and_safety_boundary() -> None:
    document = RUNBOOK.read_text(encoding="utf-8")

    for command in (
        "transcriber doctor",
        "transcriber inspect",
        "transcriber dry-run",
        "transcriber transcribe",
        "transcriber export",
        "transcriber revise prepare",
        "transcriber revise preview",
        "transcriber revise apply",
        "transcriber revise edit",
        "transcriber revise audit",
        "transcriber translate prepare",
        "transcriber translate preview",
        "transcriber translate apply",
        "transcriber translate audit",
        "transcriber translate export",
        "transcriber clean",
    ):
        assert command in document

    for contract in (
        "transcriber COMMAND --help",
        "transcriber revise COMMAND --help",
        "$HOME/.config/ewp-transcripts/config.toml",
        "`transcriber.toml` is optional",
        "one synchronized mono file per speaker",
        "Avoid 3+ channel sources",
        "speaker attribution is not guaranteed",
        "`--force` does not bypass input checks",
        "Never edit canonical JSON",
        "prepare -> edit in Windows VS Code -> preview -> apply ->\nexport",
        "Change All Occurrences",
        "selects the highest revision whose exact base-result hash matches",
        "retry only failed items",
        "Cleanup never removes source audio",
        "Cloud correction is implemented but remains strict-offline by default",
    ):
        assert contract in document


def test_operator_runbook_links_all_required_detailed_guides() -> None:
    document = RUNBOOK.read_text(encoding="utf-8")
    required = (
        "SYSTEM_REQUIREMENTS.md",
        "INSTALL_WSL.md",
        "INSTALL_TOOLS.md",
        "CUDA_SETUP.md",
        "INSTALL_APPLICATION.md",
        "MODEL_SETUP.md",
        "HUGGING_FACE_TOKEN.md",
        "OFFLINE_MODE.md",
        "REVISE_TRANSCRIPTS.md",
        "TRANSLATE_TRANSCRIPTS.md",
        "TROUBLESHOOTING.md",
        "FEEDBACK_FOR_V2.md",
    )

    for filename in required:
        assert filename in document
        assert (ROOT / "WSL config" / filename).is_file()


def test_current_bilingual_manual_and_operator_links_resolve() -> None:
    documents = [
        ROOT / "README.md",
        RUNBOOK,
        ROOT / "Instructions/GUI_QUICKSTART.md",
        ROOT / "Instructions/WINDOWS_NATIVE.md",
        ROOT / "WSL config/UBUNTU_UPGRADE.md",
        *list((ROOT / "docs/gui").rglob("*.md")),
    ]
    for document in documents:
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text()):
            url = urlsplit(target)
            if url.scheme or target.startswith("#"):
                continue
            assert (document.parent / unquote(url.path)).exists(), (document, target)
