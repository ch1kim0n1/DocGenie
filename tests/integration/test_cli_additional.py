from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from docgenie import cli
from docgenie.cli import (
    _build_outputs,
    _confirm_overwrite,
    _extract_title,
    _print_summary,
    _resolve_output,
    _validate_format,
    app,
)


def test_validate_format_and_extract_title() -> None:
    assert _validate_format("BOTH") == "both"
    with pytest.raises(typer.Exit):
        _validate_format("invalid")

    assert _extract_title("# Title\ntext") == "Title"
    assert _extract_title("text\n## no") is None


def test_output_resolution_helpers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = tmp_path
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_file = tmp_path / "custom.md"

    assert _resolve_output(None, base, "README.md") == base / "README.md"
    assert _resolve_output(out_dir, base, "README.md") == out_dir / "README.md"
    assert _resolve_output(out_file, base, "README.md") == out_file

    outputs = _build_outputs("both", None, base)
    assert {x[0] for x in outputs} == {"markdown", "html"}

    # confirm overwrite exit path
    target = tmp_path / "README.md"
    target.write_text("x", encoding="utf-8")

    monkeypatch.setattr(cli.typer, "confirm", lambda _msg: False)
    with pytest.raises(typer.Exit):
        _confirm_overwrite([("markdown", target)], preview=False, force=False)

    _confirm_overwrite([("markdown", target)], preview=True, force=False)
    _confirm_overwrite([("markdown", target)], preview=False, force=True)


def test_print_summary_with_repository() -> None:
    _print_summary(
        {
            "project_name": "P",
            "files_analyzed": 1,
            "languages": {"python": 1},
            "functions": [],
            "classes": [],
            "git_info": {"remote_url": "https://example.com/repo.git"},
        },
        "markdown",
    )


def test_generate_and_init_and_html_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sample = tmp_path / "main.py"
    sample.write_text("def hello():\n    return 'world'\n", encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text("# Sample\n", encoding="utf-8")

    runner = CliRunner()

    # generate markdown saved output + summary table branch
    result = runner.invoke(app, ["generate", str(tmp_path), "--format", "markdown", "--force"])
    assert result.exit_code == 0
    assert (tmp_path / "README.md").exists()

    # generate html preview branch
    result_html_preview = runner.invoke(app, ["generate", str(tmp_path), "--format", "html", "--preview"])
    assert result_html_preview.exit_code == 0
    assert "HTML Preview" in result_html_preview.stdout

    # init command branches
    init_result = runner.invoke(app, ["init", "--force"])
    assert init_result.exit_code == 0
    exists_result = runner.invoke(app, ["init"])
    assert exists_result.exit_code != 0

    # analyze json and yaml branches
    analyze_json = runner.invoke(app, ["analyze", str(tmp_path), "--format", "json"])
    assert analyze_json.exit_code == 0
    assert "files_analyzed" in analyze_json.stdout

    analyze_yaml = runner.invoke(app, ["analyze", str(tmp_path), "--format", "yaml"])
    assert analyze_yaml.exit_code == 0
    assert "files_analyzed" in analyze_yaml.stdout

    # html command readme source
    html_out = tmp_path / "out.html"
    html_result = runner.invoke(app, ["html", str(readme), "--source", "readme", "--output", str(html_out), "--force"])
    assert html_result.exit_code == 0
    assert html_out.exists()

    html_dir_result = runner.invoke(
        app, ["html", str(readme), "--source", "readme", "--output", str(tmp_path), "--force"]
    )
    assert html_dir_result.exit_code == 0

    existing = tmp_path / "exists.html"
    existing.write_text("<h1>x</h1>", encoding="utf-8")
    monkeypatch.setattr(cli.typer, "confirm", lambda _msg: False)
    exists_result = runner.invoke(
        app, ["html", str(readme), "--source", "readme", "--output", str(existing)]
    )
    assert exists_result.exit_code != 0

    # html command invalid readme input
    bad_result = runner.invoke(app, ["html", str(tmp_path), "--source", "readme"])
    assert bad_result.exit_code != 0

    # html command codebase source + open browser
    opened: list[str] = []
    monkeypatch.setattr(cli.webbrowser, "open", lambda url: opened.append(url))
    code_result = runner.invoke(app, ["html", str(tmp_path), "--source", "codebase", "--open-browser", "--force", "--verbose"])
    assert code_result.exit_code == 0
    assert opened


def test_render_outputs_direct(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    analysis = {
        "project_name": "P",
        "files_analyzed": 1,
        "languages": {"python": 1},
        "dependencies": {},
        "project_structure": {"root": {"files": [], "dirs": []}},
        "functions": [],
        "classes": [],
        "imports": {},
        "documentation_files": [],
        "config_files": [],
        "git_info": {},
    }

    class FakeReadme:
        def generate(self, _analysis, _output):
            return "# readme"

    class FakeHtml:
        def generate_from_analysis(self, _analysis, _output):
            return "<h1>html</h1>\n" * 100

    monkeypatch.setattr(cli, "ReadmeGenerator", FakeReadme)
    monkeypatch.setattr(cli, "HTMLGenerator", FakeHtml)

    cli._render_outputs([("markdown", tmp_path / "README.md")], analysis, preview=True)
    cli._render_outputs([("html", tmp_path / "docs.html")], analysis, preview=True)
    cli._render_outputs([("markdown", tmp_path / "README.md"), ("html", tmp_path / "docs.html")], analysis, preview=False)


def test_run_analysis_verbose(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "m.py").write_text("def x():\n    return 1\n", encoding="utf-8")

    class FakeAnalyzer:
        def __init__(self, *_args, **_kwargs):
            pass

        def analyze(self):
            return {"project_name": "X", "files_analyzed": 1, "languages": {}, "functions": [], "classes": [], "git_info": {}}

    monkeypatch.setattr(cli, "CodebaseAnalyzer", FakeAnalyzer)
    monkeypatch.setattr(cli, "load_config", lambda _path: {"ignore_patterns": ["*.tmp"]})
    data = cli._run_analysis(tmp_path, ["*.log"], True, verbose=True)
    assert data["files_analyzed"] == 1


def test_cli_module_main_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["docgenie", "--help"])
    with pytest.raises(SystemExit):
        runpy.run_module("docgenie.cli", run_name="__main__")
