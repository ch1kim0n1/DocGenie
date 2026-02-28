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

from .diff_engine import compute_git_diff_summary
from .index_store import IndexStore
from .models import AnalysisResult
from .output_links import scan_output_links
from .parsers import ParserRegistry
from .review_engine import build_reviews
from .utils import extract_git_info, get_file_language, is_website_project, should_ignore_file


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
        self.active_run_id: int | None = None

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
        self.file_imports: dict[str, set[str]] = defaultdict(set)
        self.documentation_files: list[str] = []
        self.config_files: list[str] = []
        self.git_info: dict[str, Any] = {}
        self.is_website = False
        self.website_detection_reason = ""
        self.diff_summary: dict[str, Any] = {}
        self.file_reviews: list[dict[str, Any]] = []
        self.folder_reviews: list[dict[str, Any]] = []
        self.output_links: list[dict[str, Any]] = []
        self.readme_readiness: dict[str, Any] = {}

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
        self.active_run_id = self.index_store.start_run(mode="analyze")
        self.git_info = extract_git_info(self.root_path)
        files = list(self._iter_source_files())

        tasks: list[tuple[str, list[str], bool]] = []
        for file_path in files:
            digest = _hash_file(file_path)
            cached = self.cache.get(file_path, digest)
            if cached:
                self._apply_parsed_data(cached, file_path, cached_language=cached.get("language"))
                continue
            tasks.append((str(file_path), self.ignore_patterns, self.enable_tree_sitter))

        if tasks:
            with ProcessPoolExecutor() as executor:
                futures = {
                    executor.submit(_analyze_file_task, payload): payload[0] for payload in tasks
                }
                for future in as_completed(futures):
                    file_path_str, language, parsed, file_hash = future.result()
                    if not language or parsed is None:
                        continue
                    self._apply_parsed_data(parsed, Path(file_path_str), cached_language=language)
                    self.cache.set(Path(file_path_str), file_hash, parsed, language)

        self._analyze_project_structure()
        self._detect_dependencies()
        self._run_diff_and_review()
        self._run_output_link_scan()
        compiled = self._compile_results()
        compiled.is_website = is_website_project(compiled.to_public_dict())
        compiled.website_detection_reason = "Heuristic detection based on project assets"
        if self.active_run_id is not None:
            self.index_store.finish_run(
                self.active_run_id,
                {
                    "files_analyzed": self.files_analyzed,
                    "diff_available": bool(self.diff_summary.get("available")),
                    "output_links": len(self.output_links),
                },
            )
            if self.diff_summary:
                self.index_store.add_diff_run(
                    self.active_run_id,
                    self.diff_summary.get("from_ref"),
                    self.diff_summary.get("to_ref"),
                    self.diff_summary,
                )
            if self.file_reviews:
                self.index_store.replace_file_reviews(self.active_run_id, self.file_reviews)
            if self.output_links:
                self.index_store.replace_output_links(self.active_run_id, self.output_links)
            self.index_store.commit()
        self.cache.persist()
        return compiled.to_public_dict()

    def __del__(self) -> None:
        try:
            self.index_store.close()
        except Exception:
            pass

    def _run_diff_and_review(self) -> None:
        diff_config = self.config.get("diff", {}) if isinstance(self.config, dict) else {}
        review_config = self.config.get("review", {}) if isinstance(self.config, dict) else {}
        if not isinstance(diff_config, dict) or not diff_config.get("enabled", True):
            return

        self.diff_summary = compute_git_diff_summary(
            self.root_path,
            from_ref=diff_config.get("from_ref"),
            to_ref=str(diff_config.get("to_ref", "HEAD")),
            rename_detection=bool(diff_config.get("rename_detection", True)),
            enable_tree_sitter=self.enable_tree_sitter,
        )

        if not isinstance(review_config, dict) or not review_config.get("enabled", True):
            return
        self.file_reviews, self.folder_reviews = build_reviews(
            diff_summary=self.diff_summary,
            functions=self.functions,
            classes=self.classes,
            weights=review_config.get("risk_weights")
            if isinstance(review_config.get("risk_weights"), dict)
            else None,
            max_files_per_folder=int(review_config.get("max_files_per_folder", 50)),
        )

    def _run_output_link_scan(self) -> None:
        output_config = self.config.get("output_links", {}) if isinstance(self.config, dict) else {}
        if not isinstance(output_config, dict) or not output_config.get("enabled", True):
            return
        languages = output_config.get("languages", ["python", "javascript", "typescript", "shell"])
        self.output_links = scan_output_links(
            self.root_path,
            ignore_patterns=self.ignore_patterns,
            languages=languages if isinstance(languages, list) else None,
        )

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
            rel_file = self._relative_file_path(file_path)
            if rel_file:
                self.file_imports[rel_file].add(str(imp))

    def _relative_file_path(self, file_path: Path) -> str:
        try:
            return file_path.resolve().relative_to(self.root_path).as_posix()
        except ValueError:
            return file_path.as_posix()

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
            file_imports={path: sorted(imps) for path, imps in self.file_imports.items()},
            documentation_files=self.documentation_files,
            config_files=self.config_files,
            git_info=self.git_info,
            is_website=self.is_website,
            website_detection_reason=self.website_detection_reason,
            root_path=self.root_path,
            config=self.config,
            diff_summary=self.diff_summary,
            folder_reviews=self.folder_reviews,
            file_reviews=self.file_reviews,
            output_links=self.output_links,
            readme_readiness=self.readme_readiness,
        )
