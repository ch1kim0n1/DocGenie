"""Core codebase analysis functionality for DocGenie."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from collections import Counter, defaultdict
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import suppress
from pathlib import Path
from typing import Any

import toml
from pathspec import PathSpec

from .index_store import IndexStore
from .models import AnalysisResult
from .parsers import ParserRegistry
from .utils import (
    detect_packages,
    extract_git_info,
    get_file_language,
    is_hidden_path,
    is_path_ignored_by_gitignore,
    is_probably_generated_file,
    is_website_project,
    load_gitignore_spec,
    should_ignore_file,
)

HARD_BLOB_SIZE_BYTES = 5 * 1024 * 1024


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


class CacheManager:
    """Simple file-based cache to support incremental analysis."""

    def __init__(self, root: Path):
        self.root = root
        self.cache_dir = root / ".docgenie"
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "cache.json"
        self._data: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.cache_file.exists():
            try:
                self._data = json.loads(self.cache_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                # Cache corrupted, start fresh
                self._data = {}

    def persist(self) -> None:
        self.cache_file.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def get(self, path: Path, digest: str) -> dict[str, Any] | None:
        record = self._data.get(str(path))
        if record and record.get("hash") == digest:
            return record.get("parse")
        return None

    def set(self, path: Path, digest: str, parse_result: dict[str, Any], language: str) -> None:
        parse_result = dict(parse_result)
        parse_result["language"] = language
        self._data[str(path)] = {"hash": digest, "parse": parse_result}


def _analyze_file_task(
    payload: tuple[str, list[str], bool],
) -> tuple[str, str, dict[str, Any] | None, str]:
    """Worker for concurrent file analysis."""
    file_path_str, ignore_patterns, enable_tree_sitter = payload
    _ = ignore_patterns
    file_path = Path(file_path_str)
    language = get_file_language(file_path)
    if not language:
        return file_path_str, "", None, ""
    try:
        with open(file_path, encoding="utf-8") as handle:
            content = handle.read()
    except (UnicodeDecodeError, PermissionError):
        return file_path_str, language, None, ""

    file_hash = _hash_file(file_path)
    parser_registry = ParserRegistry(enable_tree_sitter=enable_tree_sitter)
    parse_result = parser_registry.parse(content, file_path, language)
    return file_path_str, language, parse_result.to_public_dict(), file_hash


class CodebaseAnalyzer:
    """
    Analyzes a codebase to extract comprehensive information for documentation generation.
    """

    def __init__(
        self,
        root_path: str,
        ignore_patterns: list[str] | None = None,
        enable_tree_sitter: bool = True,
        config: dict[str, Any] | None = None,
    ):
        self.root_path = Path(root_path).resolve()
        self.ignore_patterns = ignore_patterns or []
        self.enable_tree_sitter = enable_tree_sitter
        self.config = config or {}
        analysis_config = self.config.get("analysis", {}) if isinstance(self.config, dict) else {}
        self.use_gitignore = bool(analysis_config.get("use_gitignore", True))
        self.exclude_generated = bool(analysis_config.get("exclude_generated", True))
        self.include_hidden = bool(analysis_config.get("include_hidden", False))
        max_size_raw = analysis_config.get("max_file_size_kb", 512)
        try:
            self.max_file_size_kb: int | None = int(max_size_raw)
        except (TypeError, ValueError):
            self.max_file_size_kb = None
        generated_patterns = analysis_config.get("generated_patterns", [])
        self.generated_patterns = generated_patterns if isinstance(generated_patterns, list) else []
        self.engine = str(analysis_config.get("engine", "hybrid_index"))
        self.incremental = bool(analysis_config.get("incremental", True))
        self.parallelism = analysis_config.get("parallelism", "auto")
        self.hard_file_cap = int(analysis_config.get("hard_file_cap", 300000))
        self.full_rescan_interval_runs = int(analysis_config.get("full_rescan_interval_runs", 20))
        self.gitignore_spec: PathSpec | None = (
            load_gitignore_spec(self.root_path) if self.use_gitignore else None
        )
        self.cache = CacheManager(self.root_path)
        self.index_store = IndexStore(self.root_path)

        self.files_analyzed = 0
        self.files_discovered = 0
        self.skipped_reasons: Counter[str] = Counter()
        self.cache_hits = 0
        self.languages: Counter[str] = Counter()
        self.dependencies: dict[str, Any] = {}
        self.project_structure: dict[str, Any] = {}
        self.functions: list[dict[str, Any]] = []
        self.classes: list[dict[str, Any]] = []
        self.imports: dict[str, set[str]] = defaultdict(set)
        self.documentation_files: list[str] = []
        self.config_files: list[str] = []
        self.git_info: dict[str, Any] = {}
        self.is_website = False
        self.website_detection_reason = ""
        self.packages: list[dict[str, Any]] = []
        self.run_metrics: dict[str, Any] = {}
        self.active_run_id: int | None = None

    def close(self) -> None:
        with suppress(Exception):
            self.index_store.close()

    def __del__(self) -> None:
        self.close()

    def _relative_path(self, path: Path) -> str:
        return path.relative_to(self.root_path).as_posix()

    def _skip_reason(self, path: Path, *, is_dir: bool) -> str | None:  # noqa: PLR0911
        rel_path = self._relative_path(path)
        normalized = rel_path.replace("\\", "/")
        if normalized == ".git" or normalized.startswith(".git/"):
            return "hard_exclude_vcs"

        if not is_dir:
            language = get_file_language(path)
            try:
                if language is None and path.stat().st_size > HARD_BLOB_SIZE_BYTES:
                    return "hard_exclude_large_binary"
            except OSError:
                return "hard_exclude_unreadable"

        if should_ignore_file(rel_path, self.ignore_patterns):
            return "user_ignore"

        if is_path_ignored_by_gitignore(rel_path, self.gitignore_spec, is_dir=is_dir):
            return "gitignore"

        if (
            (not is_dir)
            and self.exclude_generated
            and is_probably_generated_file(rel_path, self.generated_patterns)
        ):
            return "generated"

        if not self.include_hidden and is_hidden_path(rel_path):
            return "hidden"

        if (not is_dir) and self.max_file_size_kb is not None:
            try:
                if path.stat().st_size > self.max_file_size_kb * 1024:
                    return "size_limit"
            except OSError:
                return "stat_error"
        return None

    def _should_skip_path(self, path: Path, *, is_dir: bool) -> bool:
        reason = self._skip_reason(path, is_dir=is_dir)
        if reason:
            self.skipped_reasons[reason] += 1
            return True
        return False

    def analyze(self) -> dict[str, Any]:  # noqa: PLR0915
        """Perform comprehensive analysis of the codebase."""
        started = time.perf_counter()
        try:
            self.git_info = extract_git_info(self.root_path)
            self.packages = detect_packages(self.root_path)
            self.index_store.replace_packages(self.packages)
            self.active_run_id = self.index_store.start_run(
                mode="auto",
                engine=self.engine,
                incremental=self.incremental,
            )
            files = list(self._iter_source_files())
            if len(files) > self.hard_file_cap:
                files = files[: self.hard_file_cap]
                self.skipped_reasons["hard_file_cap"] += 1

            tasks: list[tuple[str, list[str], bool]] = []
            task_meta: dict[str, tuple[str, int, int]] = {}
            changed_files = 0
            for file_path in files:
                rel = self._relative_path(file_path)
                try:
                    stat = file_path.stat()
                except OSError:
                    self.skipped_reasons["stat_error"] += 1
                    continue
                indexed = self.index_store.get_file_record(rel) if self.incremental else None
                if (
                    indexed
                    and int(indexed.get("mtime_ns", -1)) == int(stat.st_mtime_ns)
                    and int(indexed.get("size", -1)) == int(stat.st_size)
                ):
                    cached = self.cache.get(file_path, str(indexed.get("hash", "")))
                    if cached:
                        self.cache_hits += 1
                        self._apply_parsed_data(
                            cached, file_path, cached_language=cached.get("language")
                        )
                        continue
                tasks.append((str(file_path), self.ignore_patterns, self.enable_tree_sitter))
                task_meta[str(file_path)] = (rel, int(stat.st_size), int(stat.st_mtime_ns))
                changed_files += 1

            if tasks:
                with ProcessPoolExecutor() as executor:
                    futures = {
                        executor.submit(_analyze_file_task, payload): payload[0]
                        for payload in tasks
                    }
                    for future in as_completed(futures):
                        file_path_str, language, parsed, file_hash = future.result()
                        if not language or parsed is None:
                            continue
                        file_path = Path(file_path_str)
                        rel, size, mtime_ns = task_meta.get(
                            file_path_str, (self._relative_path(file_path), 0, 0)
                        )
                        self._apply_parsed_data(parsed, file_path, cached_language=language)
                        self.cache.set(file_path, file_hash, parsed, language)
                        is_generated = is_probably_generated_file(rel, self.generated_patterns)
                        is_hidden = is_hidden_path(rel)
                        self.index_store.upsert_file(
                            path=rel,
                            size=size,
                            mtime_ns=mtime_ns,
                            digest=file_hash,
                            language=language,
                            is_generated=is_generated,
                            is_hidden=is_hidden,
                            ignored_reason=None,
                        )
                        symbols: list[dict[str, Any]] = []
                        for func in parsed.get("functions", []):
                            symbols.append(
                                {
                                    "symbol_type": "function",
                                    "qualified_name": func.get("name", ""),
                                    "line": func.get("line", 0),
                                }
                            )
                        for cls in parsed.get("classes", []):
                            symbols.append(
                                {
                                    "symbol_type": "class",
                                    "qualified_name": cls.get("name", ""),
                                    "line": cls.get("line", 0),
                                }
                            )
                        self.index_store.replace_symbols_and_imports(
                            rel,
                            symbols,
                            [str(imp) for imp in parsed.get("imports", [])],
                            language,
                        )

            self._analyze_project_structure()
            self._detect_dependencies()
            compiled = self._compile_results()
            compiled.is_website = is_website_project(compiled.to_public_dict())
            compiled.website_detection_reason = "Heuristic detection based on project assets"
            elapsed = time.perf_counter() - started
            scanned_files = len(files)
            skip_total = sum(self.skipped_reasons.values())
            cache_ratio = self.cache_hits / scanned_files if scanned_files else 0.0
            self.run_metrics = {
                "scanned_files": scanned_files,
                "changed_files": changed_files,
                "skipped_files": skip_total,
                "duration_sec": round(elapsed, 4),
                "cache_hit_ratio": round(cache_ratio, 4),
                "skip_reasons": dict(sorted(self.skipped_reasons.items())),
            }
            compiled.run_metrics = self.run_metrics
            compiled.packages = [dict(pkg) for pkg in self.packages]
            if self.active_run_id is not None:
                self.index_store.finish_run(self.active_run_id, self.run_metrics)
            self.index_store.commit()
            self.cache.persist()
            return compiled.to_public_dict()
        finally:
            self.close()

    def _apply_parsed_data(
        self, parsed: dict[str, Any], file_path: Path, cached_language: str | None
    ) -> None:
        language = (
            cached_language or parsed.get("language") or get_file_language(file_path) or "unknown"
        )
        self.files_analyzed += 1
        self.languages[language] += 1
        self.functions.extend(parsed.get("functions", []))
        self.classes.extend(parsed.get("classes", []))
        for imp in parsed.get("imports", []):
            self.imports[language].add(imp)

    def _iter_source_files(self) -> Iterable[Path]:
        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)
            dirs[:] = [d for d in dirs if not self._should_skip_path(root_path / d, is_dir=True)]
            for file in files:
                self.files_discovered += 1
                file_path = root_path / file
                if self._should_skip_path(file_path, is_dir=False):
                    continue
                yield file_path

    def _analyze_project_structure(self) -> None:
        structure: dict[str, Any] = {}
        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)
            dirs[:] = [d for d in dirs if not self._should_skip_path(root_path / d, is_dir=True)]
            rel_path = os.path.relpath(root, self.root_path)
            entry = {
                "files": [
                    f for f in files if not self._should_skip_path(root_path / f, is_dir=False)
                ],
                "dirs": dirs,
            }
            structure["root" if rel_path == "." else rel_path] = entry
        self.project_structure = structure

    def _detect_dependencies(self) -> None:
        dependency_files = {
            "requirements.txt": self._parse_requirements_txt,
            "pyproject.toml": self._parse_pyproject_toml,
            "setup.py": self._parse_setup_py,
            "package.json": self._parse_package_json,
            "Cargo.toml": self._parse_cargo_toml,
            "go.mod": self._parse_go_mod,
            "pom.xml": self._parse_pom_xml,
            "Gemfile": self._parse_gemfile,
        }

        for filename, parser in dependency_files.items():
            file_path = self.root_path / filename
            if file_path.exists():
                try:
                    deps = parser(file_path)
                    if deps:
                        self.dependencies[filename] = deps
                except (OSError, ValueError, KeyError, toml.TomlDecodeError):
                    # Silently skip malformed dependency files
                    continue

    def _parse_requirements_txt(self, file_path: Path) -> list[str]:
        deps: list[str] = []
        for raw_line in file_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                dep = re.split(r"[<>=!]", line)[0].strip()
                if dep:
                    deps.append(dep)
        return deps

    def _parse_package_json(self, file_path: Path) -> dict[str, list[str]]:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        deps: dict[str, list[str]] = {}
        if "dependencies" in data:
            deps["dependencies"] = list(data["dependencies"].keys())
        if "devDependencies" in data:
            deps["devDependencies"] = list(data["devDependencies"].keys())
        return deps

    def _parse_pyproject_toml(self, file_path: Path) -> dict[str, Any]:
        data = toml.load(file_path)
        deps: dict[str, Any] = {}
        project = data.get("project", {})
        if project.get("dependencies"):
            deps["dependencies"] = project["dependencies"]
        if project.get("optional-dependencies"):
            deps["optional-dependencies"] = list(project["optional-dependencies"].keys())
        if "tool" in data and "poetry" in data["tool"]:
            poetry = data["tool"]["poetry"]
            if "dependencies" in poetry:
                deps["poetry-dependencies"] = list(poetry["dependencies"].keys())
            if "dev-dependencies" in poetry:
                deps["poetry-dev-dependencies"] = list(poetry["dev-dependencies"].keys())
        return deps

    def _parse_setup_py(self, file_path: Path) -> list[str]:
        content = file_path.read_text(encoding="utf-8")
        install_requires_match = re.search(r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if install_requires_match:
            deps_str = install_requires_match.group(1)
            return re.findall(r'["\']([^"\'>=<]+)', deps_str)
        return []

    def _parse_cargo_toml(self, file_path: Path) -> dict[str, list[str]]:
        data = toml.load(file_path)
        deps: dict[str, list[str]] = {}
        if "dependencies" in data:
            deps["dependencies"] = list(data["dependencies"].keys())
        if "dev-dependencies" in data:
            deps["dev-dependencies"] = list(data["dev-dependencies"].keys())
        return deps

    def _parse_go_mod(self, file_path: Path) -> list[str]:
        content = file_path.read_text(encoding="utf-8")
        deps: list[str] = []
        in_require = False
        for raw_line in content.split("\n"):
            line = raw_line.strip()
            if line.startswith("require ("):
                in_require = True
                continue
            if line == ")" and in_require:
                in_require = False
                continue
            if in_require and line:
                deps.append(line.split()[0])
            elif line.startswith("require ") and not in_require:
                deps.append(line.split()[1])
        return deps

    def _parse_pom_xml(self, file_path: Path) -> list[str]:
        content = file_path.read_text(encoding="utf-8")
        return re.findall(r"<artifactId>(.*?)</artifactId>", content)

    def _parse_gemfile(self, file_path: Path) -> list[str]:
        deps: list[str] = []
        for raw_line in file_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line.startswith("gem "):
                match = re.search(r'gem\s+["\']([^"\']+)', line)
                if match:
                    deps.append(match.group(1))
        return deps

    def _compile_results(self) -> AnalysisResult:
        sorted_languages = dict(sorted(self.languages.items(), key=lambda kv: (-kv[1], kv[0])))
        sorted_functions = sorted(
            self.functions,
            key=lambda f: (str(f.get("file", "")), int(f.get("line", 0)), str(f.get("name", ""))),
        )
        sorted_classes = sorted(
            self.classes,
            key=lambda c: (str(c.get("file", "")), int(c.get("line", 0)), str(c.get("name", ""))),
        )
        return AnalysisResult(
            project_name=self.root_path.name,
            files_analyzed=self.files_analyzed,
            languages=sorted_languages,
            dependencies=self.dependencies,
            project_structure=self.project_structure,
            functions=sorted_functions,
            classes=sorted_classes,
            imports={lang: sorted(imps) for lang, imps in self.imports.items()},
            documentation_files=self.documentation_files,
            config_files=self.config_files,
            git_info=self.git_info,
            is_website=self.is_website,
            website_detection_reason=self.website_detection_reason,
            root_path=self.root_path,
            config=self.config,
            packages=[dict(pkg) for pkg in self.packages],
            run_metrics=self.run_metrics,
        )
