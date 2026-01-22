from pathlib import Path

from typer.testing import CliRunner

from docgenie import __version__
from docgenie.cli import app


def test_generate_preview(tmp_path: Path) -> None:
    sample = tmp_path / "main.py"
    sample.write_text("def hello():\n    return 'world'\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "generate",
            str(tmp_path),
            "--format",
            "markdown",
            "--preview",
        ],
    )

    assert result.exit_code == 0
    assert "README Preview" in result.stdout


def test_analyze_text(tmp_path: Path) -> None:
    sample = tmp_path / "module.py"
    sample.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["analyze", str(tmp_path), "--format", "text"])
    assert result.exit_code == 0
    assert "Files analyzed" in result.stdout
