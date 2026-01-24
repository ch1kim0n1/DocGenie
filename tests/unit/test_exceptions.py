"""Tests for custom exception hierarchy."""

from pathlib import Path

import pytest

from docgenie.exceptions import (
    CacheError,
    ConfigError,
    DependencyError,
    DocGenieError,
    FileAccessError,
    GeneratorError,
    ParserError,
)


def test_docgenie_error_with_path() -> None:
    """Test base exception with path."""
    path = Path("/tmp/test.py")
    err = DocGenieError("Something went wrong", path)
    assert "Something went wrong" in str(err)
    assert str(path) in str(err)
    assert err.path == path


def test_docgenie_error_without_path() -> None:
    """Test base exception without path."""
    err = DocGenieError("Something went wrong")
    assert str(err) == "Something went wrong"
    assert err.path is None


def test_parser_error() -> None:
    """Test parser-specific error."""
    path = Path("code.js")
    err = ParserError("Syntax error", path, "javascript")
    assert "javascript" in str(err)
    assert str(path) in str(err)
    assert err.language == "javascript"


def test_dependency_error_with_extra() -> None:
    """Test dependency error with installation hint."""
    err = DependencyError("tree-sitter", "full")
    assert "tree-sitter" in str(err)
    assert "pip install docgenie[full]" in str(err)


def test_dependency_error_without_extra() -> None:
    """Test dependency error without extra."""
    err = DependencyError("some-package")
    assert "some-package" in str(err)
    assert "pip install" in str(err)


def test_cache_error() -> None:
    """Test cache error."""
    err = CacheError("Cache corrupted")
    assert isinstance(err, DocGenieError)


def test_config_error() -> None:
    """Test config error."""
    err = ConfigError("Invalid YAML")
    assert isinstance(err, DocGenieError)


def test_file_access_error() -> None:
    """Test file access error."""
    err = FileAccessError("Permission denied", Path("/root/file"))
    assert isinstance(err, DocGenieError)


def test_generator_error() -> None:
    """Test generator error."""
    err = GeneratorError("Template rendering failed")
    assert isinstance(err, DocGenieError)
