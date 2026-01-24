"""Language parsers and plugin registry."""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any, cast

from tree_sitter_language_pack import get_parser as ts_get_parser

from .models import ClassDoc, FunctionDoc, MethodDoc, ParseResult


@dataclass
class ParserPlugin:
    """Base plugin interface for language parsing."""

    name: str
    languages: set[str]
    priority: int = 100  # lower number = higher priority

    def supports(self, language: str) -> bool:
        return language.lower() in self.languages

    def parse(
        self, content: str, path: Path, language: str
    ) -> ParseResult:  # pragma: no cover - interface
        raise NotImplementedError


class PythonAstParser(ParserPlugin):
    def __init__(self) -> None:
        super().__init__(name="python-ast", languages={"python"}, priority=0)

    def parse(self, content: str, path: Path, language: str) -> ParseResult:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return ParseResult()

        functions: list[FunctionDoc] = []
        classes: list[ClassDoc] = []
        imports: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(
                    FunctionDoc(
                        name=node.name,
                        file=path,
                        line=node.lineno,
                        docstring=ast.get_docstring(node),
                        args=[arg.arg for arg in node.args.args],
                        decorators=[_get_decorator_name(dec) for dec in node.decorator_list],
                        is_async=isinstance(node, ast.AsyncFunctionDef),
                    )
                )
            elif isinstance(node, ast.ClassDef):
                methods = [
                    MethodDoc(
                        name=item.name,
                        file=path,
                        line=item.lineno,
                        docstring=ast.get_docstring(item),
                        args=[arg.arg for arg in item.args.args],
                        is_async=isinstance(item, ast.AsyncFunctionDef),
                        decorators=[_get_decorator_name(dec) for dec in item.decorator_list],
                    )
                    for item in node.body
                    if isinstance(item, ast.FunctionDef)
                ]

                classes.append(
                    ClassDoc(
                        name=node.name,
                        file=path,
                        line=node.lineno,
                        docstring=ast.get_docstring(node),
                        bases=[_get_base_name(base) for base in node.bases],
                        decorators=[_get_decorator_name(dec) for dec in node.decorator_list],
                        methods=methods,
                    )
                )
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                else:
                    module = node.module or ""
                    for alias in node.names:
                        imports.add(f"{module}.{alias.name}" if module else alias.name)

        return ParseResult(functions=functions, classes=classes, imports=imports)


class RegexParser(ParserPlugin):
    """Lightweight fallback parser for non-Python languages."""

    def __init__(self) -> None:
        super().__init__(
            name="regex-fallback",
            languages={"javascript", "typescript", "java", "cpp", "c", "go", "rust"},
            priority=500,
        )

    def parse(self, content: str, path: Path, language: str) -> ParseResult:
        lines = content.splitlines()
        functions: list[FunctionDoc] = []
        classes: list[ClassDoc] = []
        imports: set[str] = set()

        patterns = _language_patterns(language)
        for idx, raw_line in enumerate(lines, 1):
            line = raw_line.strip()
            for pattern in patterns.functions:
                match = re.search(pattern, line)
                if match:
                    functions.append(
                        FunctionDoc(
                            name=match.group(1),
                            file=path,
                            line=idx,
                            docstring=None,
                            args=[],
                        )
                    )
                    break

            for pattern in patterns.classes:
                match = re.search(pattern, line)
                if match:
                    classes.append(
                        ClassDoc(
                            name=match.group(1),
                            file=path,
                            line=idx,
                            docstring=None,
                        )
                    )
                    break

            for pattern in patterns.imports:
                match = re.search(pattern, line)
                if match:
                    imports.add(match.group(1).strip())

        return ParseResult(functions=functions, classes=classes, imports=imports)


class TreeSitterParser(ParserPlugin):
    """Tree-sitter powered parser for rich cross-language support."""

    SUPPORTED = {"python", "javascript", "typescript", "java", "cpp", "c", "go", "rust"}

    def __init__(self) -> None:
        super().__init__(name="tree-sitter", languages=self.SUPPORTED, priority=50)
        self.available = ts_get_parser is not None

    def parse(self, content: str, path: Path, language: str) -> ParseResult:
        parser = ts_get_parser(language)
        tree = parser.parse(bytes(content, "utf-8"))
        root = tree.root_node

        functions: list[FunctionDoc] = []
        classes: list[ClassDoc] = []
        imports: set[str] = set()

        def text(node: Any) -> str:
            return content[node.start_byte : node.end_byte]

        for node in _iter_tree_sitter_nodes(root):
            node_type = node.type
            if node_type in _function_nodes(language):
                name = _extract_name(node, content)
                if name:
                    functions.append(
                        FunctionDoc(
                            name=name,
                            file=path,
                            line=node.start_point[0] + 1,
                            docstring=None,
                            args=[],
                        )
                    )
            if node_type in _class_nodes(language):
                name = _extract_name(node, content)
                if name:
                    classes.append(
                        ClassDoc(
                            name=name,
                            file=path,
                            line=node.start_point[0] + 1,
                            docstring=None,
                        )
                    )
            if node_type in _import_nodes(language):
                name = text(node)
                imports.add(name)

        return ParseResult(functions=functions, classes=classes, imports=imports)


@dataclass
class _LanguagePatterns:
    functions: Sequence[str] = field(default_factory=tuple)
    classes: Sequence[str] = field(default_factory=tuple)
    imports: Sequence[str] = field(default_factory=tuple)


def _language_patterns(language: str) -> _LanguagePatterns:
    lang = language.lower()
    return {
        "javascript": _LanguagePatterns(
            functions=(
                r"function\s+(\w+)\s*\(",
                r"(\w+)\s*:\s*function\s*\(",
                r"(\w+)\s*=\s*function\s*\(",
                r"(\w+)\s*=\s*\([^)]*\)\s*=>",
                r"(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>",
            ),
            classes=(r"class\s+(\w+)",),
            imports=(
                r'import\s+.*\s+from\s+["\']([^"\']+)["\']',
                r'import\s+["\']([^"\']+)["\']',
                r'require\s*\(\s*["\']([^"\']+)["\']\s*\)',
            ),
        ),
        "typescript": _LanguagePatterns(
            functions=(
                r"function\s+(\w+)\s*\(",
                r"(\w+)\s*=\s*\([^)]*\)\s*=>",
                r"(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>",
            ),
            classes=(r"class\s+(\w+)",),
            imports=(
                r'import\s+.*\s+from\s+["\']([^"\']+)["\']',
                r'import\s+["\']([^"\']+)["\']',
            ),
        ),
        "java": _LanguagePatterns(
            functions=(r"(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\(",),
            classes=(r"(?:public|private)?\s*class\s+(\w+)",),
            imports=(r"import\s+([^;]+);",),
        ),
        "cpp": _LanguagePatterns(
            functions=(r"^\s*(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*(?:{|;)",),
            classes=(r"class\s+(\w+)",),
            imports=(r"#include\s*[<\"]([^>\"]+)[>\"]",),
        ),
        "c": _LanguagePatterns(
            functions=(r"^\s*(?:\w+\s+)*(\w+)\s*\([^)]*\)\s*(?:{|;)",),
            classes=(),
            imports=(r"#include\s*[<\"]([^>\"]+)[>\"]",),
        ),
        "go": _LanguagePatterns(
            functions=(r"func\s+(?:\([^)]*\)\s+)?(\w+)\s*\(",),
            classes=(r"type\s+(\w+)\s+struct",),
            imports=(r'import\s+(?:\(\s*)?["]([^"]+)["]',),
        ),
        "rust": _LanguagePatterns(
            functions=(r"fn\s+(\w+)\s*\(",),
            classes=(r"(?:struct|enum)\s+(\w+)",),
            imports=(r"use\s+([^;]+);",),
        ),
    }.get(lang, _LanguagePatterns())


def _function_nodes(language: str) -> set[str]:
    return {
        "python": {"function_definition"},
        "javascript": {"function_declaration", "method_definition", "arrow_function"},
        "typescript": {"function_declaration", "method_definition", "arrow_function"},
        "java": {"method_declaration"},
        "cpp": {"function_definition"},
        "c": {"function_definition"},
        "go": {"function_declaration", "method_declaration"},
        "rust": {"function_item"},
    }.get(language, set())


def _class_nodes(language: str) -> set[str]:
    return {
        "python": {"class_definition"},
        "javascript": {"class_declaration"},
        "typescript": {"class_declaration"},
        "java": {"class_declaration"},
        "cpp": {"class_specifier"},
        "go": {"type_declaration"},
        "rust": {"struct_item", "enum_item", "impl_item"},
    }.get(language, set())


def _import_nodes(language: str) -> set[str]:
    return {
        "javascript": {"import_clause", "import_statement"},
        "typescript": {"import_clause", "import_statement"},
        "java": {"import_declaration"},
        "cpp": {"preproc_include"},
        "c": {"preproc_include"},
        "rust": {"use_declaration"},
        "go": {"import_declaration", "import_spec"},
        "python": {"import_statement", "import_from_statement"},
    }.get(language, set())


def _iter_tree_sitter_nodes(root: Any) -> Iterable[Any]:
    """Depth-first traversal over a tree-sitter node tree."""
    cursor = root.walk()
    visited_children = False

    while True:
        node = cursor.node
        yield node

        if not visited_children and cursor.goto_first_child():
            visited_children = False
            continue

        if cursor.goto_next_sibling():
            visited_children = False
            continue

        # Walk up until we can move to a sibling, otherwise we're done.
        while cursor.goto_parent():
            if cursor.goto_next_sibling():
                visited_children = False
                break
        else:
            break


def _extract_name(node: Any, content: str) -> str | None:
    """Best-effort extraction of identifier from a tree-sitter node."""
    if hasattr(node, "child_by_field_name"):
        name_node = node.child_by_field_name("name")
        if name_node:
            return content[name_node.start_byte : name_node.end_byte]
    return None


def _get_decorator_name(decorator: Any) -> str:
    if isinstance(decorator, ast.Name):
        return decorator.id
    if isinstance(decorator, ast.Attribute):
        owner = getattr(decorator.value, "id", None)
        if isinstance(owner, str):
            return f"{owner}.{decorator.attr}"
        return decorator.attr
    return str(decorator)


def _get_base_name(base: Any) -> str:
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Attribute):
        owner = getattr(base.value, "id", None)
        if isinstance(owner, str):
            return f"{owner}.{base.attr}"
        return base.attr
    return str(base)


class ParserRegistry:
    """Registry responsible for selecting the best parser for a language."""

    def __init__(
        self, enable_tree_sitter: bool = True, plugins: Iterable[ParserPlugin] | None = None
    ):
        builtin: list[ParserPlugin] = [PythonAstParser(), RegexParser()]
        if enable_tree_sitter:
            builtin.append(TreeSitterParser())
        self.plugins: list[ParserPlugin] = sorted(
            list(builtin) + list(plugins or []) + list(_load_external_plugins()),
            key=lambda p: p.priority,
        )

    def resolve(self, language: str) -> ParserPlugin | None:
        for plugin in self.plugins:
            if plugin.supports(language):
                return plugin
        return None

    def parse(self, content: str, path: Path, language: str) -> ParseResult:
        parser = self.resolve(language)
        if not parser:
            return ParseResult()
        return parser.parse(content, path, language)


def _load_external_plugins() -> Iterable[ParserPlugin]:
    try:
        eps_any = metadata.entry_points()
        if hasattr(eps_any, "select"):
            eps = cast(Any, eps_any).select(group="docgenie.parsers")
        else:
            eps = cast(Any, eps_any).get("docgenie.parsers", [])
    except Exception:  # pragma: no cover - best effort only
        return []
    plugins: list[ParserPlugin] = []
    for ep in eps:
        plugin_obj = _safe_load_entry_point(ep)
        if isinstance(plugin_obj, ParserPlugin):
            plugins.append(plugin_obj)
    return plugins


def _safe_load_entry_point(ep: Any) -> Any:
    """Best-effort external plugin loader."""
    try:
        return cast(Any, ep).load()
    except (ImportError, AttributeError, TypeError, ValueError):
        return None
