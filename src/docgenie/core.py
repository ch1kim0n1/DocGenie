"""Core codebase analysis functionality for DocGenie."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from collections import Counter, defaultdict
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import suppress
from dataclasses import asdict
from pathlib import Path
from typing import Any

import toml
from pathspec import PathSpec

from .diff_engine import compute_git_diff_summary
from .index_store import IndexStore
from .models import AnalysisResult, RunMetrics
from .output_links import scan_output_links
from .parsers import ParserRegistry
from .review_engine import build_reviews
from .utils import (
    extract_git_info,
    get_file_language,
    is_path_ignored_by_gitignore,
    is_probably_generated_file,
    is_website_project,
    load_gitignore_spec,
    should_ignore_file,
)

logger = logging.getLogger(__name__)

# Payloads of length > 3 carry a precomputed file digest as the 4th element.
_PAYLOAD_WITH_HASH_LEN = 3
# `require <module> <version>` in go.mod needs at least 2 tokens after `require`.
_GO_REQUIRE_MIN_PARTS = 2


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
    payload: tuple[Any, ...],
) -> tuple[str, str, dict[str, Any] | None, str]:
    """Worker for concurrent file analysis.

    The payload is ``(file_path, ignore_patterns, enable_tree_sitter[, digest])``.
    It may carry a precomputed SHA-256 digest (computed once in the main process
    for the cache lookup) so the worker does not read+hash the file a second time.
    If no digest is supplied (e.g. tests passing a 3-tuple), the worker hashes from
    the bytes it reads.
    """
    file_path_str = str(payload[0])
    enable_tree_sitter = bool(payload[2])
    precomputed_hash = str(payload[3]) if len(payload) > _PAYLOAD_WITH_HASH_LEN else None
    file_path = Path(file_path_str)
    language = get_file_language(file_path)
    if not language:
        return file_path_str, "", None, ""
    try:
        with open(file_path, "rb") as handle:
            raw = handle.read()
        content = raw.decode("utf-8")
    except (UnicodeDecodeError, PermissionError, OSError):
        return file_path_str, language, None, ""

    # Reuse the main-process digest when provided; otherwise hash the bytes we
    # just read (avoids a second full read of the file).
    file_hash = precomputed_hash or hashlib.sha256(raw).hexdigest()
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

    def _skip_reason(self, path: Path, *, is_dir: bool) -> str | None:
        """Return a skip reason string if path should be skipped, else None."""
        try:
            rel = path.resolve().relative_to(self.root_path).as_posix()
        except ValueError:
            rel = path.as_posix()

        reason: str | None = None
        if is_path_ignored_by_gitignore(rel, self.gitignore_spec, is_dir=is_dir):
            reason = "gitignore"
        elif should_ignore_file(rel, self.ignore_patterns or None):
            reason = "ignore_pattern"
        elif not self.include_hidden and any(
            part.startswith(".") for part in Path(rel).parts if part not in ("", ".")
        ):
            reason = "hidden"
        elif (
            not is_dir
            and self.exclude_generated
            and is_probably_generated_file(rel, self.generated_patterns or None)
        ):
            reason = "generated"
        elif (not is_dir) and self.max_file_size_kb is not None:
            try:
                over_limit = path.stat().st_size > self.max_file_size_kb * 1024
                reason = "size_limit" if over_limit else None
            except OSError:
                reason = "stat_error"
        return reason

    def _should_skip_path(self, path: Path, *, is_dir: bool) -> bool:
        reason = self._skip_reason(path, is_dir=is_dir)
        if reason:
            self.skipped_reasons[reason] += 1
            return True
        return False

    def analyze(self) -> dict[str, Any]:  # noqa: PLR0915
        """Perform comprehensive analysis of the codebase."""
        start_time = time.perf_counter()
        try:
            return self._analyze_impl(start_time)
        finally:
            # Deterministically release the SQLite handle on success and on error;
            # do not rely on __del__ (GC timing, Windows file locks).
            with suppress(Exception):
                self.index_store.close()

    def _analyze_impl(self, start_time: float) -> dict[str, Any]:  # noqa: PLR0915
        self.active_run_id = self.index_store.start_run(mode="analyze")
        self.git_info = extract_git_info(self.root_path)
        files = list(self._iter_source_files())

        tasks: list[tuple[str, list[str], bool, str]] = []
        for file_path in files:
            digest = _hash_file(file_path)
            cached = self.cache.get(file_path, digest)
            if cached:
                self.cache_hits += 1
                self._apply_parsed_data(cached, file_path, cached_language=cached.get("language"))
                continue
            # Pass the digest we just computed so the worker doesn't re-read+re-hash.
            tasks.append((str(file_path), self.ignore_patterns, self.enable_tree_sitter, digest))

        if tasks:
            with ProcessPoolExecutor(max_workers=min(4, (os.cpu_count() or 1))) as executor:
                futures = {
                    executor.submit(_analyze_file_task, payload): payload[0] for payload in tasks
                }
                for future in as_completed(futures):
                    try:
                        file_path_str, language, parsed, file_hash = future.result(timeout=60)
                    except TimeoutError:
                        timed_out_path = futures[future]
                        logger.warning("File analysis timed out, skipping: %s", timed_out_path)
                        continue
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
        result = compiled.to_public_dict()
        result["run_metrics"] = self._build_run_metrics(start_time)
        return result

    def _build_run_metrics(self, start_time: float) -> dict[str, Any]:
        """Build run metrics from tracked counters (see models.RunMetrics)."""
        skip_reasons = dict(self.skipped_reasons)
        skipped_files = sum(self.skipped_reasons.values())
        # changed_files = files actually parsed this run (cache misses).
        changed_files = max(0, self.files_analyzed - self.cache_hits)
        considered = self.cache_hits + changed_files
        cache_hit_ratio = round(self.cache_hits / considered, 4) if considered else 0.0
        metrics = RunMetrics(
            scanned_files=self.files_discovered,
            changed_files=changed_files,
            skipped_files=skipped_files,
            duration_sec=round(time.perf_counter() - start_time, 4),
            cache_hit_ratio=cache_hit_ratio,
            skip_reasons=skip_reasons,
        )
        return asdict(metrics)

    def __del__(self) -> None:
        with suppress(Exception):
            self.index_store.close()

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
                except (OSError, ValueError, KeyError, toml.TomlDecodeError) as exc:
                    logger.warning(
                        "Failed to parse dependency file %s (%s); skipping it.",
                        file_path,
                        exc,
                    )
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
                parts = line.split()
                if len(parts) >= 1:
                    deps.append(parts[0])
            elif line.startswith("require ") and not in_require:
                parts = line.split()
                if len(parts) >= _GO_REQUIRE_MIN_PARTS:
                    deps.append(parts[1])
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
