"""Tests for docgenie.html_generator — HTML documentation generation."""

from __future__ import annotations

from pathlib import Path

from docgenie.html_generator import HTMLGenerator

# ---------------------------------------------------------------------------
# generate_from_readme
# ---------------------------------------------------------------------------


def test_generate_from_readme_returns_html_string() -> None:
    gen = HTMLGenerator()
    html = gen.generate_from_readme("# Hello\n\nParagraph text.", None, "Hello")
    assert "<html" in html
    assert "<h1" in html
    assert "Hello" in html


def test_generate_from_readme_includes_doctype() -> None:
    html = HTMLGenerator().generate_from_readme("# Test", None, "Test")
    assert "<!DOCTYPE html>" in html


def test_generate_from_readme_sanitizes_project_name_xss() -> None:
    """Project name containing <script> must be sanitized in the HTML output."""
    html = HTMLGenerator().generate_from_readme(
        "# Normal content", None, "<script>alert('xss')</script>"
    )
    assert "<script>alert" not in html


def test_generate_from_readme_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "docs.html"
    HTMLGenerator().generate_from_readme("# Project", str(out), "Project")
    assert out.exists()
    assert out.stat().st_size > 100


def test_generate_from_readme_without_output_path_returns_string() -> None:
    html = HTMLGenerator().generate_from_readme("# Inline", None, "Inline")
    assert isinstance(html, str)
    assert len(html) > 50


def test_generate_from_readme_default_project_name() -> None:
    """Calling without project_name should use default and not raise."""
    html = HTMLGenerator().generate_from_readme("# Doc")
    assert "<html" in html


# ---------------------------------------------------------------------------
# State reset bug fix validation
# ---------------------------------------------------------------------------


def test_generate_from_readme_no_toc_bleed_across_calls() -> None:
    """Second call on the same HTMLGenerator instance must not leak content from first call."""
    gen = HTMLGenerator()
    gen.generate_from_readme(
        "# Section Alpha\n\n## Sub Alpha", None, "P1"
    )
    html2 = gen.generate_from_readme(
        "# Section Beta\n\n## Sub Beta", None, "P2"
    )
    assert "Section Alpha" not in html2
    assert "Section Beta" in html2


# ---------------------------------------------------------------------------
# generate_from_analysis
# ---------------------------------------------------------------------------


def test_generate_from_analysis_minimal(minimal_analysis: dict) -> None:
    html = HTMLGenerator().generate_from_analysis(minimal_analysis, None)
    assert "<!DOCTYPE html>" in html
    assert "TestProject" in html


def test_generate_from_analysis_website(website_analysis: dict) -> None:
    html = HTMLGenerator().generate_from_analysis(website_analysis, None)
    assert "MySite" in html
    assert "<html" in html


def test_generate_from_analysis_writes_file(minimal_analysis: dict, tmp_path: Path) -> None:
    out = tmp_path / "docs.html"
    HTMLGenerator().generate_from_analysis(minimal_analysis, str(out))
    assert out.exists()
    assert out.stat().st_size > 100


def test_generate_from_analysis_rich(rich_analysis: dict) -> None:
    html = HTMLGenerator().generate_from_analysis(rich_analysis, None)
    assert "RichProject" in html


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def test_create_html_document_structure() -> None:
    gen = HTMLGenerator()
    html = gen._create_html_document("<p>body content</p>", "MyDoc")
    assert "<!DOCTYPE html>" in html
    assert 'lang="en"' in html
    assert "<head>" in html
    assert "<title>MyDoc</title>" in html
    assert "<body>" in html
    assert "content-footer" in html


def test_get_css_styles_returns_non_empty() -> None:
    css = HTMLGenerator()._get_css_styles()
    assert isinstance(css, str)
    assert len(css) > 100


def test_extract_project_name() -> None:
    gen = HTMLGenerator()
    # _extract_project_name reads root_path.name, not project_name
    data = {"root_path": "/some/FooBar"}
    assert gen._extract_project_name(data) == "FooBar"


def test_extract_project_name_missing_key() -> None:
    """Missing project_name key should not raise."""
    gen = HTMLGenerator()
    result = gen._extract_project_name({})
    assert isinstance(result, str)
