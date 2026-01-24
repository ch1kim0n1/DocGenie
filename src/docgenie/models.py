"""Typed data models used across DocGenie."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class FunctionDoc:
    name: str
    file: Path
    line: int
    docstring: str | None
    args: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    is_async: bool = False

    def to_public_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "file": str(self.file),
            "line": self.line,
            "docstring": self.docstring,
            "args": list(self.args),
            "decorators": list(self.decorators),
            "is_async": self.is_async,
        }


@dataclass(frozen=True)
class MethodDoc(FunctionDoc):
    pass


@dataclass(frozen=True)
class ClassDoc:
    name: str
    file: Path
    line: int
    docstring: str | None
    bases: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    methods: list[MethodDoc] = field(default_factory=list)

    def to_public_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "file": str(self.file),
            "line": self.line,
            "docstring": self.docstring,
            "bases": list(self.bases),
            "decorators": list(self.decorators),
            "methods": [method.to_public_dict() for method in self.methods],
        }


@dataclass(frozen=True)
class ParseResult:
    functions: list[FunctionDoc] = field(default_factory=list)
    classes: list[ClassDoc] = field(default_factory=list)
    imports: set[str] = field(default_factory=set)

    def to_public_dict(self) -> dict[str, object]:
        return {
            "functions": [func.to_public_dict() for func in self.functions],
            "classes": [cls.to_public_dict() for cls in self.classes],
            "imports": sorted(self.imports),
        }


@dataclass(frozen=True)
class FileAnalysis:
    path: Path
    language: str
    parse: ParseResult


@dataclass
class AnalysisResult:
    project_name: str
    files_analyzed: int
    languages: dict[str, int]
    dependencies: dict[str, object]
    project_structure: dict[str, object]
    functions: list[dict[str, object]]
    classes: list[dict[str, object]]
    imports: dict[str, list[str]]
    documentation_files: list[str]
    config_files: list[str]
    git_info: dict[str, object]
    is_website: bool
    website_detection_reason: str
    root_path: Path
    config: dict[str, object] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, object]:
        return {
            "project_name": self.project_name,
            "files_analyzed": self.files_analyzed,
            "languages": dict(self.languages),
            "main_language": (
                max(self.languages.items(), key=lambda kv: kv[1])[0] if self.languages else "N/A"
            ),
            "dependencies": self.dependencies,
            "project_structure": self.project_structure,
            "functions": self.functions,
            "classes": self.classes,
            "imports": self.imports,
            "documentation_files": self.documentation_files,
            "config_files": self.config_files,
            "git_info": self.git_info,
            "is_website": self.is_website,
            "website_detection_reason": self.website_detection_reason,
            "root_path": str(self.root_path),
            "config": self.config,
        }
