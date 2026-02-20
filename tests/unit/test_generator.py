"""Tests for README generator."""

import copy
from pathlib import Path

import pytest

from docgenie.generator import ReadmeGenerator


@pytest.fixture
def sample_analysis() -> dict:
    """Sample analysis data for testing."""
    return {
        "project_name": "TestProject",
        "files_analyzed": 10,
        "languages": {"python": 8, "javascript": 2},
        "main_language": "python",
        "dependencies": {
            "requirements.txt": ["requests", "click"],
        },
        "project_structure": {
            "root": {"files": ["README.md", "setup.py"], "dirs": ["src", "tests"]},
        },
        "functions": [
            {"name": "main", "line": 10, "docstring": "Main entry point", "args": []},
        ],
        "classes": [
            {"name": "App", "line": 20, "docstring": "Application class", "methods": []},
        ],
        "imports": {"python": ["os", "sys"]},
        "documentation_files": [],
        "config_files": [],
        "git_info": {"remote_url": "https://github.com/user/repo"},
        "is_website": False,
        "website_detection_reason": "",
    }


def test_readme_generation_basic(sample_analysis: dict, tmp_path: Path) -> None:
    """Test basic README generation."""
    generator = ReadmeGenerator()
    output_path = tmp_path / "README.md"

    content = generator.generate(sample_analysis, str(output_path))

    assert output_path.exists()
    assert "TestProject" in content
    assert "python" in content.lower()
    assert "Installation" in content


def test_readme_includes_dependencies(sample_analysis: dict) -> None:
    """Test that dependencies are included."""
    generator = ReadmeGenerator()
    content = generator.generate(sample_analysis, None)

    assert "requests" in content
    assert "click" in content


def test_readme_includes_functions(sample_analysis: dict) -> None:
    """Test that functions are documented."""
    generator = ReadmeGenerator()
    content = generator.generate(sample_analysis, None)

    assert "main" in content or "API" in content


def test_readme_includes_classes(sample_analysis: dict) -> None:
    """Test that classes are documented."""
    generator = ReadmeGenerator()
    content = generator.generate(sample_analysis, None)

    assert "App" in content or "API" in content


def test_readme_with_git_info(sample_analysis: dict) -> None:
    """Test that git info is included."""
    generator = ReadmeGenerator()
    content = generator.generate(sample_analysis, None)

    assert "github.com" in content


def test_readme_without_dependencies(sample_analysis: dict) -> None:
    """Test README generation without dependencies."""
    sample_analysis["dependencies"] = {}
    generator = ReadmeGenerator()
    content = generator.generate(sample_analysis, None)

    # Should still generate valid README
    assert "TestProject" in content
    assert len(content) > 100


def test_readme_website_detection(sample_analysis: dict) -> None:
    """Test website-specific documentation."""
    sample_analysis["is_website"] = True
    sample_analysis["languages"] = {"html": 5, "css": 3, "javascript": 2}

    generator = ReadmeGenerator()
    content = generator.generate(sample_analysis, None)

    # Should have website-specific sections
    assert content  # Basic validation


def test_readme_multiple_languages(sample_analysis: dict) -> None:
    """Test README with multiple languages."""
    sample_analysis["languages"] = {
        "python": 10,
        "javascript": 5,
        "typescript": 3,
        "rust": 2,
    }

    generator = ReadmeGenerator()
    content = generator.generate(sample_analysis, None)

    assert "python" in content.lower()
    assert "javascript" in content.lower()


def test_readme_empty_project(tmp_path: Path) -> None:
    """Test README for empty project."""
    minimal_analysis = {
        "project_name": "EmptyProject",
        "files_analyzed": 0,
        "languages": {},
        "main_language": "unknown",
        "dependencies": {},
        "project_structure": {"root": {"files": [], "dirs": []}},
        "functions": [],
        "classes": [],
        "imports": {},
        "documentation_files": [],
        "config_files": [],
        "git_info": {},
        "is_website": False,
        "website_detection_reason": "",
    }

    generator = ReadmeGenerator()
    content = generator.generate(minimal_analysis, None)

    # Should still generate something
    assert "EmptyProject" in content
    assert len(content) > 50


def test_readme_respects_include_directory_tree(sample_analysis: dict) -> None:
    """If disabled, README should omit the directory tree section."""
    data = copy.deepcopy(sample_analysis)
    data["config"] = {"template_customizations": {"include_directory_tree": False}}

    generator = ReadmeGenerator()
    content = generator.generate(data, None)

    assert "## Project Structure" not in content


def test_readme_respects_include_api_docs(sample_analysis: dict) -> None:
    """If disabled, README should omit the API reference section."""
    data = copy.deepcopy(sample_analysis)
    data["config"] = {"template_customizations": {"include_api_docs": False}}

    generator = ReadmeGenerator()
    content = generator.generate(data, None)

    assert "## API Reference" not in content


# ---------------------------------------------------------------------------
# New expanded generator tests
# ---------------------------------------------------------------------------


def test_readme_async_function_triggers_async_feature(sample_analysis: dict) -> None:
    """An async function in the analysis should produce the async feature bullet."""
    data = copy.deepcopy(sample_analysis)
    data["functions"] = [
        {"name": "fetch", "line": 5, "docstring": None, "args": [], "is_async": True}
    ]
    content = ReadmeGenerator().generate(data, None)
    assert "Asynchronous" in content or "async" in content.lower()


def test_readme_api_docs_excludes_private_functions(sample_analysis: dict) -> None:
    """Functions whose name starts with _ should not appear in API Reference."""
    data = copy.deepcopy(sample_analysis)
    data["functions"] = [
        {"name": "_private_helper", "line": 5, "docstring": None, "args": [], "is_async": False},
        {"name": "public_func", "line": 10, "docstring": "Public.", "args": [], "is_async": False},
    ]
    content = ReadmeGenerator().generate(data, None)
    # public_func should be in API docs; _private_helper should not
    assert "public_func" in content
    assert "_private_helper" not in content


def test_readme_api_docs_respects_max_functions(sample_analysis: dict) -> None:
    """max_functions_documented should limit the number of documented functions."""
    data = copy.deepcopy(sample_analysis)
    data["functions"] = [
        {"name": f"func_{i}", "line": i, "docstring": None, "args": [], "is_async": False}
        for i in range(20)
    ]
    data["config"] = {"template_customizations": {"max_functions_documented": 3}}
    content = ReadmeGenerator().generate(data, None)
    # At most 3 functions should appear in the API reference
    func_names_in_content = [f"func_{i}" for i in range(20) if f"func_{i}" in content]
    assert len(func_names_in_content) <= 3


def test_readme_install_command_poetry(sample_analysis: dict) -> None:
    """pyproject.toml without requirements.txt should use poetry install."""
    data = copy.deepcopy(sample_analysis)
    data["project_structure"] = {"root": {"files": ["pyproject.toml"], "dirs": []}}
    data["dependencies"] = {}
    content = ReadmeGenerator().generate(data, None)
    assert "poetry install" in content


def test_readme_install_command_cargo(sample_analysis: dict) -> None:
    """Cargo.toml project should include cargo build command."""
    data = copy.deepcopy(sample_analysis)
    data["project_structure"] = {"root": {"files": ["Cargo.toml"], "dirs": []}}
    content = ReadmeGenerator().generate(data, None)
    assert "cargo build" in content


def test_readme_install_command_go_mod(sample_analysis: dict) -> None:
    """go.mod project should include go mod download command."""
    data = copy.deepcopy(sample_analysis)
    data["project_structure"] = {"root": {"files": ["go.mod"], "dirs": []}}
    content = ReadmeGenerator().generate(data, None)
    assert "go mod download" in content


def test_readme_install_command_pom_xml(sample_analysis: dict) -> None:
    """pom.xml project should include mvn clean install command."""
    data = copy.deepcopy(sample_analysis)
    data["project_structure"] = {"root": {"files": ["pom.xml"], "dirs": []}}
    content = ReadmeGenerator().generate(data, None)
    assert "mvn clean install" in content


def test_readme_generate_writes_file_with_project_name(
    sample_analysis: dict, tmp_path: Path
) -> None:
    """generate() should write a file containing the project name."""
    out = tmp_path / "README.md"
    ReadmeGenerator().generate(sample_analysis, str(out))
    assert out.exists()
    assert "TestProject" in out.read_text(encoding="utf-8")


def test_readme_has_tests_true_by_directory(sample_analysis: dict) -> None:
    """Project with a 'tests' directory should be detected as having tests."""
    data = copy.deepcopy(sample_analysis)
    data["project_structure"]["tests"] = {"files": ["test_main.py"], "dirs": []}
    content = ReadmeGenerator().generate(data, None)
    assert "## Testing" in content


def test_readme_requirements_node_js(sample_analysis: dict) -> None:
    """package.json dependency should add Node.js to requirements."""
    data = copy.deepcopy(sample_analysis)
    data["dependencies"] = {"package.json": {"dependencies": ["react"]}}
    content = ReadmeGenerator().generate(data, None)
    assert "Node.js" in content


def test_readme_requirements_rust(sample_analysis: dict) -> None:
    """Cargo.toml dependency should add Rust to requirements."""
    data = copy.deepcopy(sample_analysis)
    data["dependencies"] = {"Cargo.toml": {"dependencies": ["serde"]}}
    content = ReadmeGenerator().generate(data, None)
    assert "Rust" in content


def test_readme_features_fallback_when_empty(sample_analysis: dict) -> None:
    """No dependencies and no async functions → generic feature list generated."""
    data = copy.deepcopy(sample_analysis)
    data["dependencies"] = {}
    data["functions"] = []
    data["classes"] = []
    content = ReadmeGenerator().generate(data, None)
    # Generic features should include at least one of these
    assert any(
        kw in content for kw in ["performance", "easy", "modular", "configurable", "⚡", "🛠️"]
    )


def test_readme_website_detection_specific_output(sample_analysis: dict) -> None:
    """Website project should include web-detection notice in output."""
    data = copy.deepcopy(sample_analysis)
    data["is_website"] = True
    data["languages"] = {"html": 5, "css": 3, "javascript": 2}
    data["project_structure"] = {
        "root": {"files": ["index.html", "style.css"], "dirs": []}
    }
    content = ReadmeGenerator().generate(data, None)
    assert "Website" in content or "website" in content.lower()
