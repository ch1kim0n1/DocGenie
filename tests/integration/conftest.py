"""Integration test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner


@pytest.fixture()
def cli_runner() -> CliRunner:
    """Typer CLI test runner."""
    return CliRunner()


@pytest.fixture()
def multi_file_project(tmp_path: Path) -> Path:
    """Create a realistic multi-file Python project for CLI integration tests."""
    (tmp_path / "main.py").write_text(
        '"""Entry point."""\n\ndef main() -> None:\n    """Run the app."""\n    pass\n',
        encoding="utf-8",
    )
    (tmp_path / "utils.py").write_text(
        "def helper(x: int) -> int:\n    \"\"\"Return x plus 1.\"\"\"\n    return x + 1\n",
        encoding="utf-8",
    )
    (tmp_path / "requirements.txt").write_text(
        "click>=8.0\nrequests>=2.25\n",
        encoding="utf-8",
    )
    return tmp_path
