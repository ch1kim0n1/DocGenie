"""Tests for core analysis functionality."""

from pathlib import Path

from docgenie.core import CacheManager, CodebaseAnalyzer, _hash_file


def test_hash_file(tmp_path: Path) -> None:
    """Test file hashing."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, world!", encoding="utf-8")

    hash1 = _hash_file(test_file)
    hash2 = _hash_file(test_file)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex digest

    # Different content = different hash
    test_file.write_text("Different content", encoding="utf-8")
    hash3 = _hash_file(test_file)
    assert hash1 != hash3


def test_cache_manager_lifecycle(tmp_path: Path) -> None:
    """Test cache manager save/load cycle."""
    cache = CacheManager(tmp_path)
    test_path = Path("test.py")
    digest = "abc123"
    parse_result = {"functions": ["foo"], "classes": []}

    cache.set(test_path, digest, parse_result, "python")
    cache.persist()

    # Load in new instance
    cache2 = CacheManager(tmp_path)
    retrieved = cache2.get(test_path, digest)

    assert retrieved is not None
    assert retrieved["functions"] == ["foo"]
    assert retrieved["language"] == "python"


def test_cache_manager_invalidation(tmp_path: Path) -> None:
    """Test cache invalidation on hash mismatch."""
    cache = CacheManager(tmp_path)
    test_path = Path("test.py")

    cache.set(test_path, "hash1", {"functions": []}, "python")

    # Different hash = cache miss
    assert cache.get(test_path, "hash2") is None


def test_cache_manager_corrupted_file(tmp_path: Path) -> None:
    """Test graceful handling of corrupted cache."""
    cache_file = tmp_path / ".docgenie" / "cache.json"
    cache_file.parent.mkdir(exist_ok=True)
    cache_file.write_text("invalid json {{{", encoding="utf-8")

    # Should not raise, just start fresh
    cache = CacheManager(tmp_path)
    assert cache._data == {}


def test_analyzer_basic_python_project(tmp_path: Path) -> None:
    """Test analyzing a simple Python project."""
    # Create a minimal project
    (tmp_path / "main.py").write_text(
        "def hello():\n    return 'world'\n\nclass Greeter:\n    pass\n",
        encoding="utf-8",
    )
    (tmp_path / "requirements.txt").write_text("requests>=2.0\nclick", encoding="utf-8")

    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    result = analyzer.analyze()

    assert result["files_analyzed"] >= 1
    assert "python" in result["languages"]
    assert len(result["functions"]) >= 1
    assert len(result["classes"]) >= 1
    assert "requirements.txt" in result["dependencies"]


def test_analyzer_ignores_patterns(tmp_path: Path) -> None:
    """Test that ignore patterns work."""
    (tmp_path / "main.py").write_text("def foo(): pass", encoding="utf-8")
    (tmp_path / "test.py").write_text("def test_foo(): pass", encoding="utf-8")

    analyzer = CodebaseAnalyzer(
        str(tmp_path), ignore_patterns=["test.py"], enable_tree_sitter=False
    )
    result = analyzer.analyze()

    # Should only analyze main.py
    assert result["files_analyzed"] == 1


def test_analyzer_handles_encoding_errors(tmp_path: Path) -> None:
    """Test graceful handling of files with encoding issues."""
    binary_file = tmp_path / "binary.dat"
    binary_file.write_bytes(b"\x00\x01\x02\xff\xfe")

    # Should not crash
    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    result = analyzer.analyze()

    assert isinstance(result, dict)


def test_analyzer_detects_javascript_project(tmp_path: Path) -> None:
    """Test detection of JavaScript projects."""
    (tmp_path / "index.js").write_text("function main() {}", encoding="utf-8")
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"react": "^18.0.0"}}',
        encoding="utf-8",
    )

    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    result = analyzer.analyze()

    assert "javascript" in result["languages"]
    assert "package.json" in result["dependencies"]
    assert "react" in str(result["dependencies"])


def test_analyzer_caching(tmp_path: Path) -> None:
    """Test that caching improves performance on re-analysis."""
    test_file = tmp_path / "module.py"
    test_file.write_text("def cached_func(): pass", encoding="utf-8")

    # First analysis
    analyzer1 = CodebaseAnalyzer(
        str(tmp_path),
        ignore_patterns=[".docgenie"],  # Ignore cache directory
        enable_tree_sitter=False,
    )
    result1 = analyzer1.analyze()

    # Second analysis (should use cache)
    analyzer2 = CodebaseAnalyzer(
        str(tmp_path),
        ignore_patterns=[".docgenie"],  # Ignore cache directory
        enable_tree_sitter=False,
    )
    result2 = analyzer2.analyze()

    # Both should analyze the same file
    assert result1["files_analyzed"] >= 1
    assert result2["files_analyzed"] >= 1
    # Functions should be the same (cached)
    assert len(result1["functions"]) == len(result2["functions"])


def test_analyzer_project_structure(tmp_path: Path) -> None:
    """Test project structure detection."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("pass", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("pass", encoding="utf-8")

    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    result = analyzer.analyze()

    structure = result["project_structure"]
    assert "root" in structure
    assert any("src" in key for key in structure.keys())
    assert any("tests" in key for key in structure.keys())


def test_analyzer_git_info(tmp_path: Path) -> None:
    """Test git info extraction (when available)."""
    (tmp_path / "main.py").write_text("pass", encoding="utf-8")

    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    result = analyzer.analyze()

    # Should have git_info key even if empty
    assert "git_info" in result
    assert isinstance(result["git_info"], dict)


# ---------------------------------------------------------------------------
# New expanded core tests
# ---------------------------------------------------------------------------


def test_cache_manager_get_missing_key_returns_none(tmp_path: Path) -> None:
    cache = CacheManager(tmp_path)
    assert cache.get(Path("nonexistent.py"), "abc123") is None


def test_cache_manager_persist_creates_file(tmp_path: Path) -> None:
    cache = CacheManager(tmp_path)
    cache.set(Path("a.py"), "hash1", {"functions": []}, "python")
    cache.persist()
    assert (tmp_path / ".docgenie" / "cache.json").exists()


def test_analyze_file_task_unknown_extension(tmp_path: Path) -> None:
    """Files with unrecognised extensions should produce empty results without crashing."""
    from docgenie.core import _analyze_file_task

    unknown_file = tmp_path / "data.xyz123"
    unknown_file.write_text("content", encoding="utf-8")
    file_path_str, language, parsed, file_hash = _analyze_file_task(
        (str(unknown_file), [], False)
    )
    assert language == ""
    assert parsed is None


def test_analyze_file_task_binary_content(tmp_path: Path) -> None:
    """Binary files should not raise — result tuple still has 4 elements."""
    from docgenie.core import _analyze_file_task

    binary_file = tmp_path / "data.py"
    binary_file.write_bytes(b"\x00\x01\x02\xff\xfe\xfd")
    result = _analyze_file_task((str(binary_file), [], False))
    assert result is not None
    assert len(result) == 4


def test_analyzer_website_detection(tmp_path: Path) -> None:
    """Directory with index.html should be detected as a website."""
    (tmp_path / "index.html").write_text("<html><body>Hello</body></html>", encoding="utf-8")

    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    result = analyzer.analyze()
    assert result["is_website"] is True


def test_analyzer_dependency_pyproject_toml(tmp_path: Path) -> None:
    """pyproject.toml with [project] dependencies should be parsed."""
    (tmp_path / "main.py").write_text("pass", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\ndependencies = ["click>=8.0", "requests"]\n',
        encoding="utf-8",
    )
    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    result = analyzer.analyze()
    assert "pyproject.toml" in result["dependencies"]


def test_analyzer_dependency_package_json(tmp_path: Path) -> None:
    """package.json dependencies should appear in analysis results."""
    (tmp_path / "index.js").write_text("function x(){}", encoding="utf-8")
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"lodash": "^4.0"}, "devDependencies": {"jest": "^29"}}',
        encoding="utf-8",
    )
    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    result = analyzer.analyze()
    deps = result["dependencies"]
    assert "package.json" in deps
    assert "lodash" in deps["package.json"].get("dependencies", [])


def test_analyzer_dependency_cargo_toml(tmp_path: Path) -> None:
    """Cargo.toml dependencies should be parsed."""
    (tmp_path / "main.rs").write_text("fn main() {}", encoding="utf-8")
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname = "app"\nversion = "0.1.0"\n\n[dependencies]\nserde = "1.0"\n',
        encoding="utf-8",
    )
    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    result = analyzer.analyze()
    assert "Cargo.toml" in result["dependencies"]


def test_analyzer_dependency_go_mod(tmp_path: Path) -> None:
    """go.mod dependencies should be detected."""
    (tmp_path / "main.go").write_text("package main\nfunc main() {}", encoding="utf-8")
    (tmp_path / "go.mod").write_text(
        "module example.com/app\n\ngo 1.21\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.9.0\n)\n",
        encoding="utf-8",
    )
    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    result = analyzer.analyze()
    assert "go.mod" in result["dependencies"]


def test_analyzer_dependency_gemfile(tmp_path: Path) -> None:
    """Gemfile gem entries should be parsed."""
    (tmp_path / "app.rb").write_text("puts 'hello'", encoding="utf-8")
    (tmp_path / "Gemfile").write_text(
        "source 'https://rubygems.org'\ngem 'rails', '~> 7.0'\ngem 'pg'\n",
        encoding="utf-8",
    )
    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    result = analyzer.analyze()
    assert "Gemfile" in result["dependencies"]
    assert "rails" in result["dependencies"]["Gemfile"]


def test_analyzer_concurrent_processing_multiple_files(tmp_path: Path) -> None:
    """Multiple Python files should all be analyzed via ProcessPoolExecutor."""
    for i in range(5):
        (tmp_path / f"module_{i}.py").write_text(
            f"def func_{i}(): pass", encoding="utf-8"
        )
    analyzer = CodebaseAnalyzer(
        str(tmp_path),
        ignore_patterns=[".docgenie"],
        enable_tree_sitter=False,
    )
    result = analyzer.analyze()
    assert result["files_analyzed"] == 5


def test_parse_requirements_txt_ignores_comments(tmp_path: Path) -> None:
    """Comments and -r lines should be excluded from requirements parsing."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text(
        "# This is a comment\nrequests>=2.0\n-r other.txt\nclick\n",
        encoding="utf-8",
    )
    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    deps = analyzer._parse_requirements_txt(req_file)
    assert "requests" in deps
    assert "click" in deps
    assert not any(d.startswith("#") for d in deps)
    assert not any(d.startswith("-") for d in deps)


def test_parse_setup_py_extracts_install_requires(tmp_path: Path) -> None:
    setup_file = tmp_path / "setup.py"
    setup_file.write_text(
        'from setuptools import setup\nsetup(install_requires=["click", "requests"])',
        encoding="utf-8",
    )
    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    deps = analyzer._parse_setup_py(setup_file)
    assert "click" in deps
    assert "requests" in deps


def test_parse_pom_xml_extracts_artifact_ids(tmp_path: Path) -> None:
    pom_file = tmp_path / "pom.xml"
    pom_file.write_text(
        "<project><dependencies>"
        "<dependency><artifactId>spring-boot</artifactId></dependency>"
        "<dependency><artifactId>junit</artifactId></dependency>"
        "</dependencies></project>",
        encoding="utf-8",
    )
    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    deps = analyzer._parse_pom_xml(pom_file)
    assert "spring-boot" in deps
    assert "junit" in deps
