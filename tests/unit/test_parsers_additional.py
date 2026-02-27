from __future__ import annotations

import ast
from pathlib import Path

import pytest

from docgenie import parsers
from docgenie.models import ParseResult
from docgenie.parsers import ParserPlugin, ParserRegistry


class DummyPlugin(ParserPlugin):
    def parse(self, content: str, path: Path, language: str) -> ParseResult:
        _ = (content, path, language)
        return ParseResult()


def test_parser_registry_resolve_none_and_parse_default() -> None:
    registry = ParserRegistry(enable_tree_sitter=False, plugins=[])
    assert registry.resolve("unknown") is None
    parsed = registry.parse("", Path("x.unknown"), "unknown")
    assert parsed.functions == [] and parsed.classes == [] and parsed.imports == set()


def test_python_parser_syntax_error() -> None:
    parser = parsers.PythonAstParser()
    parsed = parser.parse("def broken(:\n", Path("broken.py"), "python")
    assert parsed.functions == []


def test_python_parser_decorators_and_bases() -> None:
    content = (
        "import pkg\n"
        "from os import path\n"
        "@decor\n"
        "def fn(a):\n"
        "    return a\n\n"
        "@ns.cls\n"
        "class C(Base):\n"
        "    @staticmethod\n"
        "    def m(self):\n"
        "        return 1\n"
    )
    parser = parsers.PythonAstParser()
    result = parser.parse(content, Path("x.py"), "python")
    assert {f.name for f in result.functions} == {"fn", "m"}
    cls = result.classes[0]
    assert cls.bases == ["Base"]
    assert "pkg" in result.imports
    assert "os.path" in result.imports


def test_regex_parser_for_other_languages() -> None:
    parser = parsers.RegexParser()
    go = parser.parse('import "fmt"\nfunc main() {}\ntype App struct{}\n', Path("main.go"), "go")
    assert {f.name for f in go.functions} == {"main"}
    assert {c.name for c in go.classes} == {"App"}
    assert "fmt" in go.imports

    c_parsed = parser.parse('#include <stdio.h>\nint main(){return 0;}\n', Path("a.c"), "c")
    assert any(func.name == "main" for func in c_parsed.functions)


def test_language_pattern_helpers_cover_unknown() -> None:
    assert parsers._language_patterns("unknown").functions == ()
    assert parsers._function_nodes("unknown") == set()
    assert parsers._class_nodes("unknown") == set()
    assert parsers._import_nodes("unknown") == set()


def test_extract_name_and_helper_fallbacks() -> None:
    class Named:
        def __init__(self) -> None:
            self.start_byte = 0
            self.end_byte = 4

    class NodeWithName:
        def child_by_field_name(self, field: str):
            return Named() if field == "name" else None

    assert parsers._extract_name(NodeWithName(), "name") == "name"
    assert parsers._extract_name(object(), "name") is None

    attr = ast.Attribute(value=ast.Name(id="obj"), attr="call")
    assert parsers._get_decorator_name(attr) == "obj.call"
    assert parsers._get_base_name(attr) == "obj.call"

    plain_attr = ast.Attribute(value=ast.Constant(value=1), attr="field")
    assert parsers._get_decorator_name(plain_attr) == "field"
    assert parsers._get_base_name(plain_attr) == "field"
    assert "Constant" in parsers._get_decorator_name(ast.Constant(value=1))
    assert "Constant" in parsers._get_base_name(ast.Constant(value=1))


def test_iter_tree_sitter_nodes_depth_first() -> None:
    class Cursor:
        def __init__(self, nodes: list[object]) -> None:
            self.nodes = nodes
            self.idx = 0
            self.node = nodes[0]

        def goto_first_child(self) -> bool:
            if self.idx == 0:
                self.idx = 1
                self.node = self.nodes[self.idx]
                return True
            return False

        def goto_next_sibling(self) -> bool:
            if self.idx == 1:
                self.idx = 2
                self.node = self.nodes[self.idx]
                return True
            return False

        def goto_parent(self) -> bool:
            if self.idx in {1, 2}:
                self.idx = 0
                self.node = self.nodes[0]
                return True
            return False

    class Root:
        def __init__(self) -> None:
            self.root = [type("N", (), {"type": "root"})(), type("N", (), {"type": "a"})(), type("N", (), {"type": "b"})()]

        def walk(self) -> Cursor:
            return Cursor(self.root)

    out = [n.type for n in parsers._iter_tree_sitter_nodes(Root())]
    assert out == ["root", "a", "b"]


def test_iter_tree_sitter_nodes_parent_to_sibling_branch() -> None:
    nodes = [type("N", (), {"type": "root"})(), type("N", (), {"type": "child"})(), type("N", (), {"type": "sibling"})()]

    class Cursor:
        def __init__(self) -> None:
            self.node = nodes[0]
            self.pos = "root"

        def goto_first_child(self) -> bool:
            if self.pos == "root":
                self.pos = "child"
                self.node = nodes[1]
                return True
            return False

        def goto_next_sibling(self) -> bool:
            if self.pos == "root":
                self.pos = "sibling"
                self.node = nodes[2]
                return True
            return False

        def goto_parent(self) -> bool:
            if self.pos == "child":
                self.pos = "root"
                self.node = nodes[0]
                return True
            return False

    class Root:
        def walk(self):
            return Cursor()

    out = [n.type for n in parsers._iter_tree_sitter_nodes(Root())]
    assert out == ["root", "child", "sibling"]


def test_tree_sitter_parser_and_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    class TSNode:
        def __init__(self, ntype: str, text: str = "", start: int = 0) -> None:
            self.type = ntype
            self.start_byte = 0
            self.end_byte = len(text)
            self.start_point = (start, 0)
            self._text = text

        def child_by_field_name(self, name: str):
            if name == "name" and self.type in {"function_definition", "class_definition"}:
                return type("Name", (), {"start_byte": 0, "end_byte": len(self._text)})()
            return None

    class Root:
        def __init__(self) -> None:
            self.nodes = [
                TSNode("function_definition", "fn_name", 2),
                TSNode("class_definition", "ClassX", 5),
                TSNode("import_statement", "import os", 7),
            ]

        def walk(self):
            class Cursor:
                def __init__(self, nodes: list[TSNode]) -> None:
                    self.nodes = nodes
                    self.idx = 0
                    self.node = nodes[0]

                def goto_first_child(self) -> bool:
                    return False

                def goto_next_sibling(self) -> bool:
                    if self.idx + 1 < len(self.nodes):
                        self.idx += 1
                        self.node = self.nodes[self.idx]
                        return True
                    return False

                def goto_parent(self) -> bool:
                    return False

            return Cursor(self.nodes)

    class Parser:
        def parse(self, _bytes: bytes):
            return type("Tree", (), {"root_node": Root()})()

    monkeypatch.setattr(parsers, "ts_get_parser", lambda _lang: Parser())
    parser = parsers.TreeSitterParser()
    parsed = parser.parse("fn_name", Path("x.py"), "python")
    assert any(f.name == "fn_name" for f in parsed.functions)
    assert parsed.classes
    assert parsed.imports

    registry = ParserRegistry(enable_tree_sitter=True, plugins=[DummyPlugin(name="x", languages={"python"}, priority=999)])
    assert registry.resolve("python") is not None


def test_external_plugin_loader_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    plugin = DummyPlugin(name="ext", languages={"python"})

    class EP:
        def __init__(self, obj):
            self.obj = obj

        def load(self):
            return self.obj

    class HasSelect:
        def select(self, group: str):
            assert group == "docgenie.parsers"
            return [EP(plugin), EP(object())]

    monkeypatch.setattr(parsers.metadata, "entry_points", lambda: HasSelect())
    loaded = list(parsers._load_external_plugins())
    assert loaded and loaded[0].name == "ext"

    monkeypatch.setattr(parsers.metadata, "entry_points", lambda: {"docgenie.parsers": [EP(plugin)]})
    loaded2 = list(parsers._load_external_plugins())
    assert loaded2 and loaded2[0].name == "ext"

    monkeypatch.setattr(parsers.metadata, "entry_points", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert list(parsers._load_external_plugins()) == []

    class BadEP:
        def load(self):
            raise ImportError("x")

    assert parsers._safe_load_entry_point(BadEP()) is None
