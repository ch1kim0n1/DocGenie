"""Tests for docgenie.parsers — language parsing registry and plugins."""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

import pytest

from docgenie.parsers import (
    ParserPlugin,
    ParserRegistry,
    PythonAstParser,
    RegexParser,
    TreeSitterParser,
    _class_nodes,
    _extract_name,
    _function_nodes,
    _get_base_name,
    _get_decorator_name,
    _import_nodes,
    _iter_tree_sitter_nodes,
    _language_patterns,
    _load_external_plugins,
    _safe_load_entry_point,
)

# ---------------------------------------------------------------------------
# Original tests (preserved)
# ---------------------------------------------------------------------------


def test_python_ast_parser_extracts_functions_and_classes(tmp_path: Path) -> None:
    sample = tmp_path / "sample.py"
    sample.write_text(
        "import os\n\n"
        "def foo(x: int) -> int:\n"
        "    return x + 1\n\n"
        "class Bar:\n"
        "    def baz(self):\n"
        "        return 42\n",
        encoding="utf-8",
    )

    registry = ParserRegistry(enable_tree_sitter=False)
    parsed = registry.parse(sample.read_text(encoding="utf-8"), sample, "python")

    assert any(func.name == "foo" for func in parsed.functions)
    assert any(cls.name == "Bar" for cls in parsed.classes)
    assert parsed.imports == {"os"}


def test_regex_parser_handles_js_functions(tmp_path: Path) -> None:
    sample = tmp_path / "sample.js"
    sample.write_text(
        "import React from 'react';\nfunction App() { return null; }\nconst helper = () => true;\n",
        encoding="utf-8",
    )
    registry = ParserRegistry(enable_tree_sitter=False)
    parsed = registry.parse(sample.read_text(encoding="utf-8"), sample, "javascript")

    names = {func.name for func in parsed.functions}
    assert {"App", "helper"} <= names
    assert "react" in {imp.lower() for imp in parsed.imports}


# ---------------------------------------------------------------------------
# PythonAstParser — expanded tests
# ---------------------------------------------------------------------------


def _parse_python(source: str, filename: str = "test.py") -> object:
    parser = PythonAstParser()
    return parser.parse(textwrap.dedent(source), Path(filename), "python")


def test_python_ast_parser_async_function_at_module_level() -> None:
    """Async functions at module scope must be captured (bug fix validation)."""
    result = _parse_python("async def fetch(url): return url")
    names = {f.name for f in result.functions}  # type: ignore[union-attr]
    assert "fetch" in names
    async_func = next(f for f in result.functions if f.name == "fetch")  # type: ignore[union-attr]
    assert async_func.is_async is True


def test_python_ast_parser_sync_function_is_not_async() -> None:
    result = _parse_python("def sync_func(): pass")
    func = next(f for f in result.functions if f.name == "sync_func")  # type: ignore[union-attr]
    assert func.is_async is False


def test_python_ast_parser_async_method_in_class() -> None:
    """Async methods inside class bodies must be captured (bug fix validation)."""
    source = """
        class MyClient:
            async def connect(self): ...
            def close(self): ...
    """
    result = _parse_python(source)
    cls = next(c for c in result.classes if c.name == "MyClient")  # type: ignore[union-attr]
    method_names = {m.name for m in cls.methods}
    assert "connect" in method_names
    async_method = next(m for m in cls.methods if m.name == "connect")
    assert async_method.is_async is True


def test_python_ast_parser_class_with_three_methods() -> None:
    source = """
        class Trio:
            def a(self): pass
            def b(self): pass
            def c(self): pass
    """
    result = _parse_python(source)
    cls = next(c for c in result.classes if c.name == "Trio")  # type: ignore[union-attr]
    assert len(cls.methods) == 3


def test_python_ast_parser_decorator_simple() -> None:
    source = """
        @staticmethod
        def foo(): pass
    """
    result = _parse_python(source)
    func = next(f for f in result.functions if f.name == "foo")  # type: ignore[union-attr]
    assert "staticmethod" in func.decorators


def test_python_ast_parser_decorator_attribute() -> None:
    # Use attribute decorator without call parens so _get_decorator_name returns "app.get"
    source = """
        @app.get
        def handler(): pass
    """
    result = _parse_python(source)
    func = next(f for f in result.functions if f.name == "handler")  # type: ignore[union-attr]
    assert any("app.get" == d for d in func.decorators)


def test_python_ast_parser_class_with_base() -> None:
    source = "class Child(Base): pass"
    result = _parse_python(source)
    cls = next(c for c in result.classes if c.name == "Child")  # type: ignore[union-attr]
    assert "Base" in cls.bases


def test_python_ast_parser_import_from() -> None:
    source = "from pathlib import Path"
    result = _parse_python(source)
    assert "pathlib.Path" in result.imports  # type: ignore[union-attr]


def test_python_ast_parser_multi_alias_import() -> None:
    source = "import os, sys"
    result = _parse_python(source)
    assert "os" in result.imports  # type: ignore[union-attr]
    assert "sys" in result.imports  # type: ignore[union-attr]


def test_python_ast_parser_syntax_error_returns_empty() -> None:
    result = _parse_python("def (  # syntax error")
    assert result.functions == []  # type: ignore[union-attr]
    assert result.classes == []  # type: ignore[union-attr]


def test_python_ast_parser_args_captured() -> None:
    source = "def greet(name: str, greeting: str = 'Hi') -> str: return greeting"
    result = _parse_python(source)
    func = next(f for f in result.functions if f.name == "greet")  # type: ignore[union-attr]
    assert "name" in func.args
    assert "greeting" in func.args


# ---------------------------------------------------------------------------
# RegexParser — expanded tests
# ---------------------------------------------------------------------------


def _regex_parse(source: str, language: str, filename: str = "f.txt") -> object:
    parser = RegexParser()
    return parser.parse(textwrap.dedent(source), Path(filename), language)


def test_regex_parser_typescript_functions() -> None:
    source = "function greet(name: string): void { }\nconst arrowFn = (x: number) => x;"
    result = _regex_parse(source, "typescript")
    names = {f.name for f in result.functions}  # type: ignore[union-attr]
    assert "greet" in names


def test_regex_parser_java_class() -> None:
    source = "public class MyService { public void run() {} }"
    result = _regex_parse(source, "java")
    class_names = {c.name for c in result.classes}  # type: ignore[union-attr]
    assert "MyService" in class_names


def test_regex_parser_go_function() -> None:
    source = "func NewServer(port int) *Server { return nil }"
    result = _regex_parse(source, "go")
    names = {f.name for f in result.functions}  # type: ignore[union-attr]
    assert "NewServer" in names


def test_regex_parser_rust_struct() -> None:
    source = "struct Point { x: f64, y: f64 }"
    result = _regex_parse(source, "rust")
    class_names = {c.name for c in result.classes}  # type: ignore[union-attr]
    assert "Point" in class_names


def test_regex_parser_rust_enum() -> None:
    source = "enum Direction { North, South, East, West }"
    result = _regex_parse(source, "rust")
    class_names = {c.name for c in result.classes}  # type: ignore[union-attr]
    assert "Direction" in class_names


def test_regex_parser_rust_function() -> None:
    source = "fn add(a: i32, b: i32) -> i32 { a + b }"
    result = _regex_parse(source, "rust")
    names = {f.name for f in result.functions}  # type: ignore[union-attr]
    assert "add" in names


def test_regex_parser_unknown_language_returns_empty() -> None:
    result = _regex_parse("anything", "cobol")
    assert result.functions == []  # type: ignore[union-attr]
    assert result.classes == []  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# ParserRegistry
# ---------------------------------------------------------------------------


def test_parser_registry_python_resolves_ast_not_regex() -> None:
    registry = ParserRegistry(enable_tree_sitter=False)
    plugin = registry.resolve("python")
    assert plugin is not None
    assert plugin.name == "python-ast"


def test_parser_registry_js_resolves_regex_when_no_treesitter() -> None:
    registry = ParserRegistry(enable_tree_sitter=False)
    plugin = registry.resolve("javascript")
    assert plugin is not None
    assert plugin.name == "regex-fallback"


def test_parser_registry_unsupported_language_returns_none() -> None:
    registry = ParserRegistry(enable_tree_sitter=False)
    assert registry.resolve("cobol") is None


def test_parser_registry_parse_unsupported_returns_empty_parse_result() -> None:
    from docgenie.models import ParseResult

    registry = ParserRegistry(enable_tree_sitter=False)
    result = registry.parse("any source", Path("f.cbl"), "cobol")
    assert result == ParseResult()


def test_parser_registry_python_ast_priority_is_zero() -> None:
    p = PythonAstParser()
    assert p.priority == 0


def test_parser_registry_register_adds_plugin_and_resolves_language() -> None:
    class RubyParser(ParserPlugin):
        def __init__(self) -> None:
            super().__init__(name="ruby-parser", languages={"ruby"}, priority=40)

        def parse(self, content: str, path: Path, language: str) -> object:
            from docgenie.models import ParseResult

            return ParseResult()

    registry = ParserRegistry(enable_tree_sitter=False)
    registry.register(RubyParser())

    plugin = registry.resolve("ruby")
    assert plugin is not None
    assert plugin.name == "ruby-parser"


def test_parser_registry_register_replaces_existing_plugin_by_name() -> None:
    class JsParserA(ParserPlugin):
        def __init__(self) -> None:
            super().__init__(name="js-custom", languages={"javascript"}, priority=30)

        def parse(self, content: str, path: Path, language: str) -> object:
            from docgenie.models import ParseResult

            return ParseResult()

    class JsParserB(ParserPlugin):
        def __init__(self) -> None:
            super().__init__(name="js-custom", languages={"javascript"}, priority=10)

        def parse(self, content: str, path: Path, language: str) -> object:
            from docgenie.models import ParseResult

            return ParseResult()

    registry = ParserRegistry(enable_tree_sitter=False)
    registry.register(JsParserA())
    registry.register(JsParserB())

    matching = [plugin for plugin in registry.plugins if plugin.name == "js-custom"]
    assert len(matching) == 1
    assert matching[0].priority == 10


def test_parser_registry_register_sorts_by_priority() -> None:
    class SlowParser(ParserPlugin):
        def __init__(self) -> None:
            super().__init__(name="slow", languages={"ruby"}, priority=200)

        def parse(self, content: str, path: Path, language: str) -> object:
            from docgenie.models import ParseResult

            return ParseResult()

    class FastParser(ParserPlugin):
        def __init__(self) -> None:
            super().__init__(name="fast", languages={"ruby"}, priority=20)

        def parse(self, content: str, path: Path, language: str) -> object:
            from docgenie.models import ParseResult

            return ParseResult()

    registry = ParserRegistry(enable_tree_sitter=False)
    registry.register(SlowParser())
    registry.register(FastParser())

    ruby_plugins = [plugin for plugin in registry.plugins if plugin.supports("ruby")]
    assert ruby_plugins[0].name == "fast"


def test_parser_registry_register_invalid_type_raises_type_error() -> None:
    registry = ParserRegistry(enable_tree_sitter=False)
    with pytest.raises(TypeError, match="ParserPlugin"):
        registry.register("not-a-plugin")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Internal helper functions
# ---------------------------------------------------------------------------


def test_get_decorator_name_ast_name() -> None:
    node = ast.Name(id="staticmethod")
    assert _get_decorator_name(node) == "staticmethod"


def test_get_decorator_name_ast_attribute() -> None:
    node = ast.Attribute(value=ast.Name(id="app"), attr="get")
    assert _get_decorator_name(node) == "app.get"


def test_get_base_name_ast_name() -> None:
    node = ast.Name(id="Base")
    assert _get_base_name(node) == "Base"


def test_get_base_name_ast_attribute() -> None:
    node = ast.Attribute(value=ast.Name(id="module"), attr="Base")
    assert _get_base_name(node) == "module.Base"


# ---------------------------------------------------------------------------
# Plugin supports() method
# ---------------------------------------------------------------------------


def test_python_ast_parser_supports_case_insensitive() -> None:
    plugin = PythonAstParser()
    assert plugin.supports("python") is True
    assert plugin.supports("PYTHON") is True
    assert plugin.supports("javascript") is False


def test_regex_parser_supports_expected_languages() -> None:
    plugin = RegexParser()
    for lang in ("javascript", "typescript", "java", "cpp", "go", "rust"):
        assert plugin.supports(lang) is True


# ---------------------------------------------------------------------------
# _language_patterns
# ---------------------------------------------------------------------------


def test_language_patterns_javascript_has_functions() -> None:
    patterns = _language_patterns("javascript")
    assert len(patterns.functions) > 0


def test_language_patterns_unknown_returns_empty() -> None:
    patterns = _language_patterns("cobol")
    assert len(patterns.functions) == 0
    assert len(patterns.classes) == 0


def test_function_class_import_nodes_have_expected_mappings() -> None:
    assert "function_definition" in _function_nodes("python")
    assert "class_declaration" in _class_nodes("javascript")
    assert "import_statement" in _import_nodes("typescript")
    assert _function_nodes("unknown") == set()
    assert _class_nodes("unknown") == set()
    assert _import_nodes("unknown") == set()


def test_extract_name_handles_missing_child_by_field_name() -> None:
    class NodeWithoutMethod:
        pass

    assert _extract_name(NodeWithoutMethod(), "source") is None


def test_extract_name_reads_name_field() -> None:
    class NameNode:
        start_byte = 5
        end_byte = 10

    class ParentNode:
        def child_by_field_name(self, name: str) -> NameNode | None:
            return NameNode() if name == "name" else None

    assert _extract_name(ParentNode(), "xxxxxhello") == "hello"


def test_iter_tree_sitter_nodes_depth_first_traversal() -> None:
    class FakeNode:
        def __init__(self, name: str) -> None:
            self.type = name
            self.start_point = (0, 0)

    class FakeCursor:
        def __init__(self) -> None:
            self.nodes = [FakeNode("root"), FakeNode("child"), FakeNode("sibling")]
            self.index = 0

        @property
        def node(self) -> FakeNode:
            return self.nodes[self.index]

        def goto_first_child(self) -> bool:
            if self.index == 0:
                self.index = 1
                return True
            return False

        def goto_next_sibling(self) -> bool:
            if self.index == 1:
                self.index = 2
                return True
            return False

        def goto_parent(self) -> bool:
            if self.index in {1, 2}:
                self.index = 0
                return True
            return False

    class FakeRoot:
        def walk(self) -> FakeCursor:
            return FakeCursor()

    names = [node.type for node in _iter_tree_sitter_nodes(FakeRoot())]
    assert names == ["root", "child", "sibling"]


def test_safe_load_entry_point_handles_load_errors() -> None:
    class BrokenEP:
        def load(self) -> object:
            raise ImportError("boom")

    assert _safe_load_entry_point(BrokenEP()) is None


def test_load_external_plugins_select_api(monkeypatch: pytest.MonkeyPatch) -> None:
    class GoodPlugin(ParserPlugin):
        def __init__(self) -> None:
            super().__init__(name="good", languages={"python"}, priority=1)

        def parse(self, content: str, path: Path, language: str) -> object:
            from docgenie.models import ParseResult

            return ParseResult()

    class GoodEP:
        def load(self) -> GoodPlugin:
            return GoodPlugin()

    class BadEP:
        def load(self) -> object:
            return object()

    class EntryPointsWithSelect:
        def select(self, group: str) -> list[object]:
            assert group == "docgenie.parsers"
            return [GoodEP(), BadEP()]

    monkeypatch.setattr("docgenie.parsers.metadata.entry_points", lambda: EntryPointsWithSelect())
    plugins = list(_load_external_plugins())
    assert len(plugins) == 1
    assert plugins[0].name == "good"


def test_load_external_plugins_legacy_get_api(monkeypatch: pytest.MonkeyPatch) -> None:
    class LegacyGoodPlugin(ParserPlugin):
        def __init__(self) -> None:
            super().__init__(name="legacy", languages={"python"}, priority=2)

        def parse(self, content: str, path: Path, language: str) -> object:
            from docgenie.models import ParseResult

            return ParseResult()

    class LegacyEP:
        def load(self) -> LegacyGoodPlugin:
            return LegacyGoodPlugin()

    class EntryPointsLegacy:
        def get(self, group: str, default: list[object]) -> list[object]:
            if group == "docgenie.parsers":
                return [LegacyEP()]
            return default

    monkeypatch.setattr("docgenie.parsers.metadata.entry_points", lambda: EntryPointsLegacy())
    plugins = list(_load_external_plugins())
    assert len(plugins) == 1
    assert plugins[0].name == "legacy"


def test_tree_sitter_parser_parse_returns_empty_when_parser_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("docgenie.parsers.ts_get_parser", lambda language: None)
    parser = TreeSitterParser()
    result = parser.parse("def f():\n    pass", Path("a.py"), "python")
    assert result.functions == []
    assert result.classes == []


def test_tree_sitter_parser_parse_returns_empty_on_parser_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ExplodingParser:
        def parse(self, content: bytes) -> object:
            raise RuntimeError("parse failed")

    monkeypatch.setattr("docgenie.parsers.ts_get_parser", lambda language: ExplodingParser())
    parser = TreeSitterParser()
    result = parser.parse("content", Path("a.py"), "python")
    assert result.functions == []
    assert result.classes == []
