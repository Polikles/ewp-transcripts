"""Release metadata and project licensing must remain synchronized."""

import tomllib
from importlib.metadata import version
from pathlib import Path

from ewp_transcripts import __version__

ROOT = Path(__file__).resolve().parents[2]


def test_release_version_and_license_metadata() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert metadata["project"]["dynamic"] == ["version"]
    version_source = ROOT / metadata["tool"]["hatch"]["version"]["path"]
    assert f'__version__ = "{__version__}"' in version_source.read_text()
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    project = next(item for item in lock["package"] if item["name"] == "ewp-transcripts")
    assert project["source"] == {"editable": "."}
    assert version("ewp-transcripts") == __version__
    assert metadata["project"]["authors"] == [
        {"name": "Damian Szczech", "email": "szczech.dam+ewptranscript@gmail.com"}
    ]
    assert metadata["project"]["license"] == "AGPL-3.0-only"
    assert metadata["project"]["license-files"] == ["LICENSE", "LICENSING.md"]
    assert metadata["project"]["urls"] == {
        "Repository": "https://github.com/Polikles/ewp-transcripts",
        "Issues": "https://github.com/Polikles/ewp-transcripts/issues",
    }


def test_agpl_license_and_public_notice_are_present() -> None:
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    licensing_text = (ROOT / "LICENSING.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert license_text.startswith("GNU AFFERO GENERAL PUBLIC LICENSE\nVersion 3")
    assert "END OF TERMS AND CONDITIONS" in license_text
    assert "AGPL-3.0-only" in licensing_text
    assert "Damian Szczech" in licensing_text
    assert "AGPL-3.0-only" in readme
    assert "without warranty" in readme
