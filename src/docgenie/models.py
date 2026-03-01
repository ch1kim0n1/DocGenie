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


@dataclass(frozen=True)
class FileIndexRecord:
    path: str
    size: int
    mtime_ns: int
    digest: str
    language: str | None
    is_generated: bool
    is_hidden: bool
    ignored_reason: str | None


@dataclass(frozen=True)
class SymbolRecord:
    symbol_type: str
    qualified_name: str
    path: str
    line: int
    signature_hash: str | None = None


@dataclass(frozen=True)
class PackageRecord:
    path: str
    package_type: str
    manifest: str | None
    parent_path: str | None


@dataclass(frozen=True)
class RunMetrics:
    scanned_files: int = 0
    changed_files: int = 0
    skipped_files: int = 0
    duration_sec: float = 0.0
    cache_hit_ratio: float = 0.0
    skip_reasons: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class DocArtifactRecord:
    artifact_path: str
    target: str
    content_hash: str
    section_hashes: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SkipReason:
    path: str
    reason: str


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
    file_imports: dict[str, list[str]] = field(default_factory=dict)
    config: dict[str, object] = field(default_factory=dict)
    diff_summary: dict[str, object] = field(default_factory=dict)
    folder_reviews: list[dict[str, object]] = field(default_factory=list)
    file_reviews: list[dict[str, object]] = field(default_factory=list)
    output_links: list[dict[str, object]] = field(default_factory=list)
    readme_readiness: dict[str, object] = field(default_factory=dict)

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
            "file_imports": self.file_imports,
            "documentation_files": self.documentation_files,
            "config_files": self.config_files,
            "git_info": self.git_info,
            "is_website": self.is_website,
            "website_detection_reason": self.website_detection_reason,
            "root_path": str(self.root_path),
            "config": self.config,
            "diff_summary": self.diff_summary,
            "folder_reviews": self.folder_reviews,
            "file_reviews": self.file_reviews,
            "output_links": self.output_links,
            "readme_readiness": self.readme_readiness,
        }
