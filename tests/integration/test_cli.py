from pathlib import Path

from typer.testing import CliRunner

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


# ---------------------------------------------------------------------------
# New expanded CLI integration tests
# ---------------------------------------------------------------------------


def test_generate_html_format(multi_file_project: Path, cli_runner: CliRunner) -> None:
    """--format html should produce docs.html."""
    result = cli_runner.invoke(
        app, ["generate", str(multi_file_project), "--format", "html", "--force"]
    )
    assert result.exit_code == 0
    assert (multi_file_project / "docs.html").exists()


def test_generate_both_formats(multi_file_project: Path, cli_runner: CliRunner) -> None:
    """--format both should produce both README.md and docs.html."""
    result = cli_runner.invoke(
        app, ["generate", str(multi_file_project), "--format", "both", "--force"]
    )
    assert result.exit_code == 0
    assert (multi_file_project / "README.md").exists()
    assert (multi_file_project / "docs.html").exists()


def test_generate_with_output_path(
    multi_file_project: Path, cli_runner: CliRunner, tmp_path: Path
) -> None:
    """--output should write to the specified path."""
    out = tmp_path / "custom_readme.md"
    result = cli_runner.invoke(
        app,
        ["generate", str(multi_file_project), "--output", str(out), "--force"],
    )
    assert result.exit_code == 0
    assert out.exists()


def test_generate_no_tree_sitter(multi_file_project: Path, cli_runner: CliRunner) -> None:
    """--no-tree-sitter --preview should complete without error."""
    result = cli_runner.invoke(
        app, ["generate", str(multi_file_project), "--no-tree-sitter", "--preview"]
    )
    assert result.exit_code == 0


def test_generate_verbose(multi_file_project: Path, cli_runner: CliRunner) -> None:
    """--verbose --preview should complete without error."""
    result = cli_runner.invoke(
        app, ["generate", str(multi_file_project), "--verbose", "--preview"]
    )
    assert result.exit_code == 0


def test_generate_with_ignore_patterns(multi_file_project: Path, cli_runner: CliRunner) -> None:
    """--ignore patterns flag should be accepted without error."""
    result = cli_runner.invoke(
        app, ["generate", str(multi_file_project), "--ignore", "secret.py", "--preview"]
    )
    assert result.exit_code == 0


def test_analyze_json_format(multi_file_project: Path, cli_runner: CliRunner) -> None:
    """--format json should produce valid JSON with expected keys."""
    import json

    result = cli_runner.invoke(
        app, ["analyze", str(multi_file_project), "--format", "json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "files_analyzed" in data


def test_analyze_yaml_format(multi_file_project: Path, cli_runner: CliRunner) -> None:
    """--format yaml should produce valid YAML with expected keys."""
    import yaml

    result = cli_runner.invoke(
        app, ["analyze", str(multi_file_project), "--format", "yaml"]
    )
    assert result.exit_code == 0
    data = yaml.safe_load(result.stdout)
    assert "files_analyzed" in data


def test_html_command_from_readme(
    cli_runner: CliRunner, multi_file_project: Path, tmp_path: Path
) -> None:
    """html command with --source readme should convert a README file to HTML."""
    readme = multi_file_project / "README.md"
    readme.write_text("# MyProject\n\nA project description.\n", encoding="utf-8")
    out = tmp_path / "docs.html"
    result = cli_runner.invoke(
        app,
        ["html", str(readme), "--source", "readme", "--output", str(out), "--force"],
    )
    assert result.exit_code == 0
    assert out.exists()


def test_html_command_from_codebase(
    cli_runner: CliRunner, multi_file_project: Path, tmp_path: Path
) -> None:
    """html command with --source codebase should generate HTML from a directory."""
    out = tmp_path / "codebase_docs.html"
    result = cli_runner.invoke(
        app,
        ["html", str(multi_file_project), "--source", "codebase", "--output", str(out), "--force"],
    )
    assert result.exit_code == 0
    assert out.exists()


def test_docgenie_html_entrypoint_help(cli_runner: CliRunner) -> None:
    """docgenie-html --help should exit with code 0."""
    import sys

    import pytest

    from docgenie.convert_to_html import main as html_main

    with pytest.raises(SystemExit) as exc:
        html_main.__wrapped__ = None  # reset any wrapping
        sys.argv = ["docgenie-html", "--help"]
        html_main()
    assert exc.value.code == 0
