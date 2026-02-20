"""Tests for docgenie.models — typed data models."""

from __future__ import annotations

from pathlib import Path

import pytest

from docgenie.models import AnalysisResult, ClassDoc, FunctionDoc, MethodDoc, ParseResult

# ---------------------------------------------------------------------------
# FunctionDoc
# ---------------------------------------------------------------------------


def test_function_doc_to_public_dict_all_fields() -> None:
    func = FunctionDoc(
        name="my_func",
        file=Path("src/module.py"),
        line=10,
        docstring="Does stuff.",
        args=["x", "y"],
        decorators=["staticmethod"],
        is_async=False,
    )
    d = func.to_public_dict()

    assert d["name"] == "my_func"
    assert d["file"] == str(Path("src/module.py"))
    assert d["line"] == 10
    assert d["docstring"] == "Does stuff."
    assert d["args"] == ["x", "y"]
    assert d["decorators"] == ["staticmethod"]
    assert d["is_async"] is False


def test_function_doc_file_is_stringified() -> None:
    """to_public_dict should return str, not Path."""
    func = FunctionDoc(name="f", file=Path("a/b.py"), line=1, docstring=None)
    result = func.to_public_dict()
    assert isinstance(result["file"], str)


def test_function_doc_args_is_copy() -> None:
    """Mutating the returned args list must not affect the dataclass."""
    func = FunctionDoc(name="f", file=Path("f.py"), line=1, docstring=None, args=["a"])
    d = func.to_public_dict()
    d["args"].append("z")  # type: ignore[union-attr]
    assert func.args == ["a"]


def test_function_doc_defaults() -> None:
    func = FunctionDoc(name="f", file=Path("f.py"), line=1, docstring=None)
    d = func.to_public_dict()
    assert d["args"] == []
    assert d["decorators"] == []
    assert d["is_async"] is False


def test_function_doc_is_frozen() -> None:
    func = FunctionDoc(name="f", file=Path("f.py"), line=1, docstring=None)
    with pytest.raises((AttributeError, TypeError)):
        func.name = "other"  # type: ignore[misc]


def test_function_doc_async_flag() -> None:
    func = FunctionDoc(name="fetch", file=Path("c.py"), line=5, docstring=None, is_async=True)
    assert func.to_public_dict()["is_async"] is True


# ---------------------------------------------------------------------------
# MethodDoc
# ---------------------------------------------------------------------------


def test_method_doc_inherits_function_doc() -> None:
    method = MethodDoc(name="run", file=Path("m.py"), line=3, docstring="Runs.")
    assert isinstance(method, FunctionDoc)
    d = method.to_public_dict()
    assert d["name"] == "run"


# ---------------------------------------------------------------------------
# ClassDoc
# ---------------------------------------------------------------------------


def test_class_doc_to_public_dict_with_methods() -> None:
    m1 = MethodDoc(name="__init__", file=Path("c.py"), line=5, docstring=None)
    m2 = MethodDoc(name="run", file=Path("c.py"), line=10, docstring="Runs.")
    cls = ClassDoc(
        name="Worker",
        file=Path("c.py"),
        line=1,
        docstring="A worker class.",
        bases=["Base"],
        decorators=[],
        methods=[m1, m2],
    )
    d = cls.to_public_dict()

    assert d["name"] == "Worker"
    assert d["docstring"] == "A worker class."
    assert d["bases"] == ["Base"]
    assert len(d["methods"]) == 2  # type: ignore[arg-type]
    assert isinstance(d["methods"][0], dict)  # type: ignore[index]
    assert d["methods"][0]["name"] == "__init__"  # type: ignore[index]


def test_class_doc_to_public_dict_no_methods() -> None:
    cls = ClassDoc(name="Empty", file=Path("e.py"), line=1, docstring=None)
    d = cls.to_public_dict()
    assert d["methods"] == []


def test_class_doc_is_frozen() -> None:
    cls = ClassDoc(name="C", file=Path("c.py"), line=1, docstring=None)
    with pytest.raises((AttributeError, TypeError)):
        cls.name = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ParseResult
# ---------------------------------------------------------------------------


def test_parse_result_to_public_dict_nested_conversion() -> None:
    func = FunctionDoc(name="foo", file=Path("f.py"), line=1, docstring=None)
    cls = ClassDoc(name="Bar", file=Path("b.py"), line=2, docstring=None)
    result = ParseResult(functions=[func], classes=[cls], imports={"sys", "os"})
    d = result.to_public_dict()

    assert isinstance(d["functions"][0], dict)  # type: ignore[index]
    assert isinstance(d["classes"][0], dict)  # type: ignore[index]
    # imports sorted
    assert d["imports"] == sorted(["sys", "os"])


def test_parse_result_imports_always_sorted() -> None:
    imports = {"z_module", "a_module", "m_module"}
    d = ParseResult(imports=imports).to_public_dict()
    assert d["imports"] == sorted(imports)


def test_parse_result_empty() -> None:
    d = ParseResult().to_public_dict()
    assert d["functions"] == []
    assert d["classes"] == []
    assert d["imports"] == []


# ---------------------------------------------------------------------------
# AnalysisResult
# ---------------------------------------------------------------------------


def _make_analysis(**overrides: object) -> AnalysisResult:
    defaults: dict[str, object] = {
        "project_name": "Proj",
        "files_analyzed": 0,
        "languages": {},
        "dependencies": {},
        "project_structure": {},
        "functions": [],
        "classes": [],
        "imports": {},
        "documentation_files": [],
        "config_files": [],
        "git_info": {},
        "is_website": False,
        "website_detection_reason": "",
        "root_path": Path("/tmp/proj"),
    }
    defaults.update(overrides)
    return AnalysisResult(**defaults)  # type: ignore[arg-type]


def test_analysis_result_main_language_from_languages() -> None:
    ar = _make_analysis(languages={"python": 5, "rust": 2})
    d = ar.to_public_dict()
    assert d["main_language"] == "python"


def test_analysis_result_main_language_empty() -> None:
    ar = _make_analysis(languages={})
    d = ar.to_public_dict()
    assert d["main_language"] == "N/A"


def test_analysis_result_root_path_stringified() -> None:
    ar = _make_analysis(root_path=Path("/some/path"))
    d = ar.to_public_dict()
    assert isinstance(d["root_path"], str)
    assert d["root_path"] == str(Path("/some/path"))
