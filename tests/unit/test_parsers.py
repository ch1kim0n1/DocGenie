from pathlib import Path

from docgenie.parsers import ParserRegistry


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
        "import React from 'react';\n"
        "function App() { return null; }\n"
        "const helper = () => true;\n",
        encoding="utf-8",
    )
    registry = ParserRegistry(enable_tree_sitter=False)
    parsed = registry.parse(sample.read_text(encoding="utf-8"), sample, "javascript")

    names = {func.name for func in parsed.functions}
    assert {"App", "helper"} <= names
    assert "react" in {imp.lower() for imp in parsed.imports}
