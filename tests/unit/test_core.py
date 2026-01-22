"""Tests for core analysis functionality."""

from pathlib import Path

import pytest

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
    
    analyzer = CodebaseAnalyzer(str(tmp_path), ignore_patterns=["test.py"], enable_tree_sitter=False)
    result = analyzer.analyze()
    
    # Should only analyze main.py
    assert result["files_analyzed"] == 1


def test_analyzer_handles_encoding_errors(tmp_path: Path) -> None:
    """Test graceful handling of files with encoding issues."""
    binary_file = tmp_path / "binary.dat"
    binary_file.write_bytes(b"\x00\x01\x02\xFF\xFE")
    
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
    analyzer1 = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    result1 = analyzer1.analyze()
    
    # Second analysis (should use cache)
    analyzer2 = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    result2 = analyzer2.analyze()
    
    assert result1["files_analyzed"] == result2["files_analyzed"]
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
