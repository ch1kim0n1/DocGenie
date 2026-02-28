from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

from docgenie import __author__, __email__, __version__
from docgenie.convert_to_html import main as html_entry
from docgenie.html_generator import HTMLGenerator
from docgenie.logging import LogContext, configure_logging, get_logger, log_error, log_file_operation
from docgenie.models import AnalysisResult, ClassDoc, FileAnalysis, FunctionDoc, MethodDoc, ParseResult


def test_public_metadata_exports() -> None:
    assert __version__
    assert __author__
    assert __email__


def test_models_public_dict_roundtrip() -> None:
    method = MethodDoc(name="m", file=Path("a.py"), line=3, docstring=None, args=["self"])
    func = FunctionDoc(name="f", file=Path("a.py"), line=1, docstring="doc", args=["x"])
    cls = ClassDoc(name="C", file=Path("a.py"), line=2, docstring=None, methods=[method])
    parsed = ParseResult(functions=[func], classes=[cls], imports={"os"})
    f_analysis = FileAnalysis(path=Path("a.py"), language="python", parse=parsed)
    assert f_analysis.language == "python"
    pub = parsed.to_public_dict()
    assert pub["functions"][0]["name"] == "f"
    assert pub["classes"][0]["methods"][0]["name"] == "m"

    res = AnalysisResult(
        project_name="p",
        files_analyzed=1,
        languages={"python": 1},
        dependencies={},
        project_structure={},
        functions=pub["functions"],
        classes=pub["classes"],
        imports={"python": ["os"]},
        documentation_files=[],
        config_files=[],
        git_info={},
        is_website=False,
        website_detection_reason="",
        root_path=Path("."),
    )
    assert res.to_public_dict()["main_language"] == "python"
    res2 = AnalysisResult(
        project_name="p",
        files_analyzed=0,
        languages={},
        dependencies={},
        project_structure={},
        functions=[],
        classes=[],
        imports={},
        documentation_files=[],
        config_files=[],
        git_info={},
        is_website=False,
        website_detection_reason="",
        root_path=Path("."),
    )
    assert res2.to_public_dict()["main_language"] == "N/A"


def test_html_generator_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    gen = HTMLGenerator()
    out = tmp_path / "docs.html"
    html = gen.generate_from_readme("# Title\n\nBody", str(out), "<My Project>")
    assert out.exists()
    assert "&lt;My Project&gt;" in html
    assert "Smooth scrolling" in gen._get_javascript()
    assert "--primary-color" in gen._get_css_styles()

    analysis = {
        "project_name": "Name",
        "project_structure": {"root": {"files": ["index.html"], "dirs": []}},
        "dependencies": {},
        "languages": {"html": 1},
        "functions": [],
        "classes": [],
        "git_info": {},
        "documentation_files": [],
        "config_files": [],
        "files_analyzed": 1,
    }
    html2 = gen.generate_from_analysis(analysis, str(tmp_path / "docs2.html"))
    assert "Name" in html2
    assert "Impact Graph" in html2
    assert gen._extract_project_name({"git_info": {"repo_name": "org/repo"}}) == "org/repo"
    assert gen._extract_project_name({"root_path": "/tmp/proj"}) == "proj"
    assert gen._extract_project_name({}) == "Project Documentation"

    # Non-website branch
    analysis_non = dict(analysis)
    analysis_non["project_structure"] = {"root": {"files": ["main.py"], "dirs": []}}
    assert "Name" in gen.generate_from_analysis(analysis_non, None)


def test_logging_helpers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    configure_logging(verbose=False, json_output=True)
    configure_logging(verbose=True, json_output=False)

    ctx_calls: list[tuple[str, str]] = []

    def _bind_contextvars(**kwargs: str) -> None:
        for k, v in kwargs.items():
            ctx_calls.append((k, v))

    def _unbind_contextvars(key: str) -> None:
        ctx_calls.append(("unbind", key))

    monkeypatch.setattr("structlog.contextvars.bind_contextvars", _bind_contextvars)
    monkeypatch.setattr("structlog.contextvars.unbind_contextvars", _unbind_contextvars)

    with LogContext(action="write", target="file"):
        pass

    assert ("action", "write") in ctx_calls
    assert ("unbind", "action") in ctx_calls

    logger = get_logger(__name__)
    assert logger is not None

    log_file_operation("write", tmp_path / "x.txt", size=12)
    log_error(RuntimeError("boom"), {"phase": "test"})


def test_entrypoints(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, object] = {}

    def fake_app(*, args=None, prog_name=None):
        called["args"] = args
        called["prog_name"] = prog_name

    monkeypatch.setattr("docgenie.convert_to_html.app", fake_app)
    monkeypatch.setattr(sys, "argv", ["docgenie-html", "README.md"]) 
    html_entry()
    assert called["prog_name"] == "docgenie-html"
    assert called["args"] == ["html", "README.md"]

    # Cover __main__ guards for both modules.
    monkeypatch.setattr(sys, "argv", ["docgenie", "--help"])
    with pytest.raises(SystemExit):
        runpy.run_module("docgenie.__main__", run_name="__main__")

    monkeypatch.setattr(sys, "argv", ["docgenie-html", "--help"])
    with pytest.raises(SystemExit):
        runpy.run_module("docgenie.convert_to_html", run_name="__main__")
