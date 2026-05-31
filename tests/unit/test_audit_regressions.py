"""Regression tests for audit issues #31-#50."""

from __future__ import annotations

from pathlib import Path

import pytest

from docgenie.generator import ReadmeGenerator
from docgenie.html_generator import HTMLGenerator
from docgenie.parsers import PythonAstParser
from docgenie.readme_gate import evaluate_readme_readiness
from docgenie.sanitize import sanitize_markdown_html


# --- #31 Stored XSS in generated HTML --------------------------------------
def test_sanitize_markdown_html_strips_script() -> None:
    dirty = '<p>ok</p><script>alert(document.cookie)</script>'
    clean = sanitize_markdown_html(dirty)
    assert "<script" not in clean.lower()
    assert "alert(" not in clean or "<script" not in clean.lower()
    assert "<p>ok</p>" in clean


def test_html_generator_neutralizes_script_from_docstring() -> None:
    gen = HTMLGenerator()
    readme = "# Title\n\n<script>alert('xss')</script>\n\nNormal body."
    html = gen.generate_from_readme(readme, None, "Proj")
    assert "<script>alert" not in html
    # The DocGenie-controlled JS block is still present (it is not user content).
    assert "renderImpactGraph" in html


def test_html_generator_neutralizes_javascript_url() -> None:
    gen = HTMLGenerator()
    readme = "# T\n\n[click](javascript:alert(1))\n"
    html = gen.generate_from_readme(readme, None, "Proj")
    assert "javascript:alert" not in html


def test_html_generator_from_analysis_strips_script_in_docstring() -> None:
    gen = HTMLGenerator()
    analysis = {
        "project_name": "Name",
        "project_structure": {"root": {"files": ["main.py"], "dirs": []}},
        "dependencies": {},
        "languages": {"python": 1},
        "functions": [
            {
                "name": "f",
                "file": "main.py",
                "line": 1,
                "docstring": "<script>alert('xss')</script>",
                "args": [],
            }
        ],
        "classes": [],
        "git_info": {},
        "documentation_files": [],
        "config_files": [],
        "files_analyzed": 1,
    }
    html = gen.generate_from_analysis(analysis, None)
    assert "<script>alert" not in html


# --- #32 Documentation Quality section renders -----------------------------
def test_quality_section_renders_score_and_confidence() -> None:
    gen = ReadmeGenerator()
    analysis = {
        "project_name": "Proj",
        "files_analyzed": 25,
        "languages": {"python": 20, "typescript": 5},
        "dependencies": {"requirements.txt": ["x"]},
        "project_structure": {"root": {"files": ["README.md"], "dirs": []}, "tests": {}},
        "functions": [{"name": f"f{i}"} for i in range(8)],
        "classes": [{"name": f"C{i}"} for i in range(3)],
        "git_info": {},
    }
    content = gen.generate(analysis)
    assert "## Documentation Quality" in content
    # No empty score/confidence.
    assert "**Quality Score**: /100" not in content
    assert "**Quality Score**: 100/100" in content
    assert "**Confidence**: High" in content


def test_quality_section_renders_warnings() -> None:
    gen = ReadmeGenerator()
    analysis = {
        "project_name": "Proj",
        "files_analyzed": 1,
        "languages": {},
        "dependencies": {},
        "project_structure": {"root": {"files": ["app.py"], "dirs": []}},
        "functions": [],
        "classes": [],
        "git_info": {},
    }
    content = gen.generate(analysis)
    assert "**Warnings**:" in content


# --- #39 Readiness gate uses real confidence -------------------------------
def test_readiness_does_not_penalize_high_confidence() -> None:
    readme = (
        "# Proj\n## Installation\n## Usage\n## Architecture\n## License\n"
    )
    result = evaluate_readme_readiness(
        readme,
        analysis_data={"confidence_level": "high"},
        min_confidence="medium",
    )
    assert all("confidence" not in r for r in result["reasons"])
    assert result["score"] == 100


def test_readiness_penalizes_low_confidence() -> None:
    readme = (
        "# Proj\n## Installation\n## Usage\n## Architecture\n## License\n"
    )
    result = evaluate_readme_readiness(
        readme,
        analysis_data={"confidence_level": "low"},
        min_confidence="medium",
    )
    assert any("confidence" in r for r in result["reasons"])


def test_generate_sets_confidence_level_on_analysis_data() -> None:
    gen = ReadmeGenerator()
    analysis = {
        "project_name": "Proj",
        "files_analyzed": 25,
        "languages": {"python": 20, "typescript": 5},
        "dependencies": {"requirements.txt": ["x"]},
        "project_structure": {"root": {"files": ["README.md"], "dirs": []}, "tests": {}},
        "functions": [{"name": f"f{i}"} for i in range(8)],
        "classes": [{"name": f"C{i}"} for i in range(3)],
        "git_info": {},
    }
    gen.generate(analysis)
    assert analysis["confidence_level"] == "high"


# --- #49 Async functions/methods are extracted -----------------------------
def test_async_function_extracted() -> None:
    parser = PythonAstParser()
    result = parser.parse("async def handler():\n    return 1\n", Path("a.py"), "python")
    assert any(f.name == "handler" and f.is_async for f in result.functions)


def test_async_method_extracted() -> None:
    parser = PythonAstParser()
    code = "class C:\n    async def m(self):\n        return 1\n"
    result = parser.parse(code, Path("a.py"), "python")
    methods = result.classes[0].methods
    assert any(m.name == "m" and m.is_async for m in methods)


# --- #50 Requirements derived from project metadata ------------------------
def test_requires_python_from_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nrequires-python = ">=3.11"\n', encoding="utf-8"
    )
    gen = ReadmeGenerator()
    reqs = gen._extract_requirements(
        {"root_path": str(tmp_path)}, {"pyproject.toml": {}}
    )
    assert "Python >=3.11" in reqs
    assert "Python 3.8 or higher" not in reqs


def test_node_engine_from_package_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"engines": {"node": ">=18"}}', encoding="utf-8"
    )
    gen = ReadmeGenerator()
    reqs = gen._extract_requirements(
        {"root_path": str(tmp_path)}, {"package.json": {}}
    )
    assert "Node.js >=18" in reqs


def test_no_fabricated_requirements_without_metadata(tmp_path: Path) -> None:
    gen = ReadmeGenerator()
    reqs = gen._extract_requirements({"root_path": str(tmp_path)}, {})
    assert reqs == ["See installation instructions below"]


# --- #36 Documented `docgenie` command exists ------------------------------
def test_docgenie_entry_point_declared() -> None:
    """The documented `docgenie` command must be a declared console script."""
    import tomllib

    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    scripts = data["project"]["scripts"]
    assert "docgenie" in scripts
    assert scripts["docgenie"] == "docgenie.cli:app"


def test_docgenie_command_runs_via_cli_app(tmp_path: Path) -> None:
    """The `docgenie generate` workflow documented in the README runs end to end."""
    from typer.testing import CliRunner

    from docgenie.cli import app

    (tmp_path / "main.py").write_text("def hello():\n    return 1\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        app, ["generate", str(tmp_path), "--format", "markdown", "--preview"]
    )
    assert result.exit_code == 0


# --- #38 run_metrics populated ---------------------------------------------
def test_run_metrics_populated_by_analyze(tmp_path: Path) -> None:
    from docgenie.core import CodebaseAnalyzer

    (tmp_path / "main.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    result = analyzer.analyze()
    metrics = result["run_metrics"]
    assert metrics["scanned_files"] >= 1
    assert "cache_hit_ratio" in metrics
    assert "duration_sec" in metrics
    assert "skip_reasons" in metrics
