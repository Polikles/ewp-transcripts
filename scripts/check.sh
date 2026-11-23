#!/usr/bin/env bash
set -euo pipefail

uv run --locked --no-sync ruff check src installer tests/unit tests/integration tools/build_distribution.py tools/build_setup.py tools/prepare_distribution_tools.py tools/build_installer_icon.py
uv run --locked --no-sync ruff format --check src installer tests/unit tests/integration tools/build_distribution.py tools/build_setup.py tools/prepare_distribution_tools.py tools/build_installer_icon.py
uv run --locked --no-sync mypy src
uv run --locked --no-sync pytest -q
