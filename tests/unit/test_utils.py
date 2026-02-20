"""Tests for docgenie.utils — utility functions."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from docgenie.utils import (
    LANGUAGE_EXTENSIONS,
    create_directory_tree,
    extract_git_info,
    extract_repo_name_from_url,
    format_file_size,
    get_file_language,
    get_project_type,
    is_website_project,
    should_ignore_file,
)

# ---------------------------------------------------------------------------
# get_file_language
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("module.py", "python"),
        ("app.js", "javascript"),
        ("component.ts", "typescript"),
        ("main.rs", "rust"),
        ("server.go", "go"),
        ("Service.java", "java"),
        ("utils.cpp", "cpp"),
        ("index.html", "html"),
        ("style.css", "css"),
        ("README.md", "markdown"),
    ],
)
def test_get_file_language_known_extensions(filename: str, expected: str) -> None:
    assert get_file_language(Path(filename)) == expected


def test_get_file_language_unknown_extension() -> None:
    assert get_file_language(Path("file.xyz123")) is None


def test_get_file_language_no_extension() -> None:
    assert get_file_language(Path("Makefile")) is None


def test_get_file_language_uppercase_extension() -> None:
    # Suffix is lowercased before lookup, so .PY should resolve to python
    assert get_file_language(Path("FILE.PY")) == "python"


def test_language_extensions_dict_has_expected_keys() -> None:
    assert ".py" in LANGUAGE_EXTENSIONS
    assert ".js" in LANGUAGE_EXTENSIONS
    assert ".rs" in LANGUAGE_EXTENSIONS
    assert ".go" in LANGUAGE_EXTENSIONS


# ---------------------------------------------------------------------------
# should_ignore_file
# ---------------------------------------------------------------------------


def test_should_ignore_git_dir() -> None:
    assert should_ignore_file(".git") is True


def test_should_ignore_node_modules() -> None:
    import os

    assert should_ignore_file(os.path.join("node_modules", "react", "index.js")) is True


def test_should_ignore_pycache() -> None:
    assert should_ignore_file("src/__pycache__/mod.cpython-312.pyc") is True


def test_should_not_ignore_normal_file() -> None:
    assert should_ignore_file("src/main.py") is False


def test_should_ignore_additional_pattern() -> None:
    assert should_ignore_file("generated.out", ["*.out"]) is True


def test_should_ignore_pyc_glob() -> None:
    assert should_ignore_file("main.pyc") is True


def test_should_not_ignore_test_file() -> None:
    assert should_ignore_file("tests/test_app.py") is False


# ---------------------------------------------------------------------------
# extract_repo_name_from_url
# ---------------------------------------------------------------------------


def test_extract_repo_name_https_with_git_suffix() -> None:
    assert extract_repo_name_from_url("https://github.com/user/repo.git") == "user/repo"


def test_extract_repo_name_ssh() -> None:
    assert extract_repo_name_from_url("git@github.com:user/repo.git") == "user/repo"


def test_extract_repo_name_https_no_git_suffix() -> None:
    assert extract_repo_name_from_url("https://github.com/user/repo") == "user/repo"


def test_extract_repo_name_unrecognized_falls_through() -> None:
    # Should return the original url when no match found
    url = "not-a-valid-url"
    result = extract_repo_name_from_url(url)
    assert isinstance(result, str)


def test_extract_repo_name_always_returns_str() -> None:
    for url in ["", "plain", "https://example.com/a/b.git", "git@host:a/b.git"]:
        assert isinstance(extract_repo_name_from_url(url), str)


# ---------------------------------------------------------------------------
# format_file_size
# ---------------------------------------------------------------------------


def test_format_file_size_zero() -> None:
    assert format_file_size(0) == "0 B"


def test_format_file_size_bytes() -> None:
    assert format_file_size(500) == "500.0 B"


def test_format_file_size_kilobytes() -> None:
    assert format_file_size(1024) == "1.0 KB"


def test_format_file_size_megabytes() -> None:
    assert format_file_size(1024 * 1024) == "1.0 MB"


def test_format_file_size_gigabytes() -> None:
    assert format_file_size(1024**3) == "1.0 GB"


# ---------------------------------------------------------------------------
# is_website_project
# ---------------------------------------------------------------------------


def _website_analysis(**overrides: object) -> dict:
    base: dict = {
        "project_structure": {"root": {"files": [], "dirs": []}},
        "dependencies": {},
        "languages": {},
    }
    base.update(overrides)
    return base


def test_is_website_project_html_entry_point() -> None:
    data = _website_analysis(
        project_structure={"root": {"files": ["index.html"], "dirs": []}}
    )
    assert is_website_project(data) is True


def test_is_website_project_static_generator_config() -> None:
    data = _website_analysis(
        project_structure={"root": {"files": ["mkdocs.yml"], "dirs": []}}
    )
    assert is_website_project(data) is True


def test_is_website_project_web_framework_dep() -> None:
    data = _website_analysis(
        dependencies={"package.json": {"dependencies": ["react"]}}
    )
    assert is_website_project(data) is True


def test_is_website_project_plain_python_is_false() -> None:
    data = _website_analysis(
        project_structure={"root": {"files": ["main.py", "requirements.txt"], "dirs": []}},
        dependencies={"requirements.txt": ["click", "requests"]},
        languages={"python": 10},
    )
    assert is_website_project(data) is False


def test_is_website_project_high_web_ratio() -> None:
    data = _website_analysis(
        project_structure={"root": {"files": ["index.html"], "dirs": []}},
        languages={"html": 8, "css": 4, "javascript": 3, "python": 1},
    )
    assert is_website_project(data) is True


# ---------------------------------------------------------------------------
# get_project_type
# ---------------------------------------------------------------------------


def _project_analysis(**overrides: object) -> dict:
    base: dict = {
        "project_structure": {"root": {"files": [], "dirs": []}},
        "dependencies": {},
        "languages": {},
        "main_language": "unknown",
        "is_website": False,
    }
    base.update(overrides)
    return base


def test_get_project_type_fastapi() -> None:
    # FastAPI is detected as a web framework, so is_website_project returns True,
    # and get_project_type returns "Website" (not "FastAPI Application")
    data = _project_analysis(
        project_structure={"root": {"files": ["requirements.txt"], "dirs": []}},
        dependencies={"requirements.txt": ["fastapi"]},
    )
    assert get_project_type(data) == "Website"


def test_get_project_type_nodejs() -> None:
    data = _project_analysis(
        project_structure={"root": {"files": ["package.json"], "dirs": []}},
        dependencies={"package.json": {"dependencies": ["lodash"]}},
    )
    assert get_project_type(data) == "Node.js Application"


def test_get_project_type_rust() -> None:
    data = _project_analysis(
        project_structure={"root": {"files": ["Cargo.toml"], "dirs": []}}
    )
    assert get_project_type(data) == "Rust Application"


def test_get_project_type_go() -> None:
    data = _project_analysis(
        project_structure={"root": {"files": ["go.mod"], "dirs": []}}
    )
    assert get_project_type(data) == "Go Application"


def test_get_project_type_fallback_to_main_language() -> None:
    data = _project_analysis(main_language="kotlin")
    result = get_project_type(data)
    assert "kotlin" in result.lower() or "Kotlin" in result


@pytest.mark.parametrize(
    ("deps", "expected"),
    [
        ({"package.json": {"dependencies": ["react"]}}, "React Website"),
        ({"package.json": {"dependencies": ["vue"]}}, "Vue.js Website"),
        ({"package.json": {"dependencies": ["angular"]}}, "Angular Website"),
        ({"package.json": {"dependencies": ["gatsby"]}}, "Gatsby Static Website"),
        ({"package.json": {"dependencies": ["next"]}}, "Next.js Website"),
    ],
)
def test_get_project_type_website_package_variants(deps: dict, expected: str) -> None:
    data = _project_analysis(
        project_structure={"root": {"files": ["index.html", "package.json"], "dirs": []}},
        dependencies=deps,
        languages={"html": 4, "javascript": 6},
    )
    assert get_project_type(data) == expected


def test_get_project_type_static_website_hugo_jekyll() -> None:
    data = _project_analysis(
        project_structure={"root": {"files": ["index.html", "hugo.toml"], "dirs": []}},
        languages={"html": 5},
    )
    assert get_project_type(data) == "Static Website (Hugo/Jekyll)"


def test_get_project_type_django_and_flask_website() -> None:
    django_data = _project_analysis(
        project_structure={"root": {"files": ["index.html"], "dirs": []}},
        dependencies={"requirements.txt": ["django"]},
        languages={"html": 3, "python": 2},
    )
    flask_data = _project_analysis(
        project_structure={"root": {"files": ["index.html"], "dirs": []}},
        dependencies={"requirements.txt": ["flask"]},
        languages={"html": 3, "python": 2},
    )
    assert get_project_type(django_data) == "Django Website"
    assert get_project_type(flask_data) == "Flask Website"


def test_get_project_type_non_website_python_frameworks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("docgenie.utils.is_website_project", lambda data: False)
    django_data = _project_analysis(
        project_structure={"root": {"files": ["requirements.txt"], "dirs": []}},
        dependencies={"requirements.txt": ["django"]},
        languages={"python": 10},
    )
    flask_data = _project_analysis(
        project_structure={"root": {"files": ["setup.py"], "dirs": []}},
        dependencies={"setup.py": ["flask"]},
        languages={"python": 10},
    )
    assert get_project_type(django_data) == "Django Application"
    assert get_project_type(flask_data) == "Flask Application"


def test_get_project_type_non_website_node_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("docgenie.utils.is_website_project", lambda data: False)
    react_data = _project_analysis(
        project_structure={"root": {"files": ["package.json"], "dirs": []}},
        dependencies={"package.json": {"dependencies": ["react"]}},
        languages={"javascript": 8, "python": 2},
    )
    express_data = _project_analysis(
        project_structure={"root": {"files": ["package.json"], "dirs": []}},
        dependencies={"package.json": {"dependencies": ["express"]}},
        languages={"javascript": 8, "python": 2},
    )
    assert get_project_type(react_data) == "React Application"
    assert get_project_type(express_data) == "Node.js/Express Application"


def test_get_project_type_java_and_ruby() -> None:
    java_data = _project_analysis(
        project_structure={"root": {"files": ["build.gradle"], "dirs": []}}
    )
    ruby_data = _project_analysis(project_structure={"root": {"files": ["Gemfile"], "dirs": []}})
    assert get_project_type(java_data) == "Java Application"
    assert get_project_type(ruby_data) == "Ruby Application"


def test_get_project_type_unknown_defaults_to_software_project() -> None:
    data = _project_analysis(main_language="unknown")
    assert get_project_type(data) == "Software Project"


# ---------------------------------------------------------------------------
# create_directory_tree
# ---------------------------------------------------------------------------


def test_create_directory_tree_empty() -> None:
    result = create_directory_tree({})
    assert result == "No files found"


def test_create_directory_tree_root_files() -> None:
    structure = {"root": {"files": ["README.md", "main.py"], "dirs": []}}
    result = create_directory_tree(structure)
    assert "README.md" in result
    assert "main.py" in result


def test_create_directory_tree_returns_string() -> None:
    structure = {"root": {"files": ["a.py"], "dirs": ["src"]}}
    assert isinstance(create_directory_tree(structure), str)


def test_create_directory_tree_shows_root_overflow_message() -> None:
    root_files = [f"file_{index}.txt" for index in range(11)]
    structure = {"root": {"files": root_files, "dirs": []}}
    result = create_directory_tree(structure)
    assert "... and 1 more files" in result


def test_create_directory_tree_respects_max_depth() -> None:
    deep_path = f"a{os.sep}b"
    structure = {
        "root": {"files": ["README.md"], "dirs": ["a"]},
        deep_path: {"files": ["hidden.txt"], "dirs": []},
    }
    result = create_directory_tree(structure, max_depth=1)
    assert "hidden.txt" not in result


# ---------------------------------------------------------------------------
# extract_git_info
# ---------------------------------------------------------------------------


def test_extract_git_info_non_repo(tmp_path: Path) -> None:
    """A plain directory that is not a git repo should return empty dict."""
    result = extract_git_info(tmp_path)
    assert result == {}


def test_extract_git_info_happy_path_with_mocked_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeAuthor:
        name = "Alice"
        email = "alice@example.com"

    class FakeCommit:
        hexsha = "abc123"
        author = FakeAuthor()
        committed_datetime = "2026-01-01 00:00:00"
        message = "Initial commit\n"

    class FakeHead:
        is_detached = False
        commit = FakeCommit()

    class FakeBranch:
        name = "main"

    class FakeOrigin:
        url = "https://github.com/example/repo.git"

    class FakeRemotes:
        origin = FakeOrigin()

    class FakeGit:
        @staticmethod
        def shortlog(flag: str) -> str:
            assert flag == "-sn"
            return "  2\tAlice\n  1\tBob\n"

    class FakeRepo:
        def __init__(self, path: Path, search_parent_directories: bool) -> None:
            self.head = FakeHead()
            self.active_branch = FakeBranch()
            self.remotes = FakeRemotes()
            self.git = FakeGit()

    monkeypatch.setattr("docgenie.utils.Repo", FakeRepo)
    result = extract_git_info(Path("."))

    assert result["repo_name"] == "example/repo"
    assert result["current_branch"] == "main"
    assert result["latest_commit"]["hash"] == "abc123"
    assert result["contributor_count"] == 2
