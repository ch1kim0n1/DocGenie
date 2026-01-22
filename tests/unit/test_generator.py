"""Tests for README generator."""

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
