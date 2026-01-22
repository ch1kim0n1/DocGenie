"""Core codebase analysis functionality for DocGenie."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import toml

from .exceptions import CacheError, FileAccessError
from .models import AnalysisResult
from .parsers import ParserRegistry
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
        self._data: Dict[str, Dict[str, Any]] = {}
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

    def get(self, path: Path, digest: str) -> Optional[Dict[str, Any]]:
        record = self._data.get(str(path))
        if record and record.get("hash") == digest:
            return record.get("parse")
        return None

    def set(self, path: Path, digest: str, parse_result: Dict[str, Any], language: str) -> None:
        parse_result = dict(parse_result)
        parse_result["language"] = language
        self._data[str(path)] = {"hash": digest, "parse": parse_result}


def _analyze_file_task(payload: Tuple[str, List[str], bool]) -> Tuple[str, str, Optional[Dict[str, Any]], str]:
    """Worker for concurrent file analysis."""
    file_path_str, ignore_patterns, enable_tree_sitter = payload
    _ = ignore_patterns
    file_path = Path(file_path_str)
    language = get_file_language(file_path)
    if not language:
        return file_path_str, "", None, ""
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
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

    def __init__(self, root_path: str, ignore_patterns: Optional[List[str]] = None, enable_tree_sitter: bool = True):
        self.root_path = Path(root_path).resolve()
        self.ignore_patterns = ignore_patterns or []
        self.enable_tree_sitter = enable_tree_sitter
        self.cache = CacheManager(self.root_path)

        self.files_analyzed = 0
        self.languages: Counter[str] = Counter()
        self.dependencies: Dict[str, Any] = {}
        self.project_structure: Dict[str, Any] = {}
        self.functions: List[Dict[str, Any]] = []
        self.classes: List[Dict[str, Any]] = []
        self.imports: Dict[str, Set[str]] = defaultdict(set)
        self.documentation_files: List[str] = []
        self.config_files: List[str] = []
        self.git_info: Dict[str, Any] = {}
        self.is_website = False
        self.website_detection_reason = ""

    def analyze(self) -> Dict[str, Any]:
        """Perform comprehensive analysis of the codebase."""
        self.git_info = extract_git_info(self.root_path)
        files = list(self._iter_source_files())

        tasks: List[Tuple[str, List[str], bool]] = []
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
        compiled = self._compile_results()
        compiled.is_website = is_website_project(compiled.to_public_dict())
        compiled.website_detection_reason = "Heuristic detection based on project assets"
        self.cache.persist()
        return compiled.to_public_dict()

    def _apply_parsed_data(self, parsed: Dict[str, Any], file_path: Path, cached_language: Optional[str]) -> None:
        language = cached_language or parsed.get("language") or get_file_language(file_path) or "unknown"
        self.files_analyzed += 1
        self.languages[language] += 1
        self.functions.extend(parsed.get("functions", []))
        self.classes.extend(parsed.get("classes", []))
        for imp in parsed.get("imports", []):
            self.imports[language].add(imp)

    def _iter_source_files(self) -> Iterable[Path]:
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if not should_ignore_file(d, self.ignore_patterns)]
            for file in files:
                file_path = Path(root) / file
                if should_ignore_file(str(file_path), self.ignore_patterns):
                    continue
                yield file_path

    def _analyze_project_structure(self) -> None:
        structure: Dict[str, Any] = {}
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if not should_ignore_file(d, self.ignore_patterns)]
            rel_path = os.path.relpath(root, self.root_path)
            entry = {
                "files": [f for f in files if not should_ignore_file(f, self.ignore_patterns)],
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

    def _parse_requirements_txt(self, file_path: Path) -> List[str]:
        deps = []
        for line in file_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                dep = re.split(r"[<>=!]", line)[0].strip()
                if dep:
                    deps.append(dep)
        return deps

    def _parse_package_json(self, file_path: Path) -> Dict[str, List[str]]:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        deps: Dict[str, List[str]] = {}
        if "dependencies" in data:
            deps["dependencies"] = list(data["dependencies"].keys())
        if "devDependencies" in data:
            deps["devDependencies"] = list(data["devDependencies"].keys())
        return deps

    def _parse_pyproject_toml(self, file_path: Path) -> Dict[str, Any]:
        data = toml.load(file_path)
        deps: Dict[str, Any] = {}
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

    def _parse_setup_py(self, file_path: Path) -> List[str]:
        content = file_path.read_text(encoding="utf-8")
        install_requires_match = re.search(r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if install_requires_match:
            deps_str = install_requires_match.group(1)
            deps = re.findall(r'["\']([^"\'>=<]+)', deps_str)
            return deps
        return []

    def _parse_cargo_toml(self, file_path: Path) -> Dict[str, List[str]]:
        data = toml.load(file_path)
        deps: Dict[str, List[str]] = {}
        if "dependencies" in data:
            deps["dependencies"] = list(data["dependencies"].keys())
        if "dev-dependencies" in data:
            deps["dev-dependencies"] = list(data["dev-dependencies"].keys())
        return deps

    def _parse_go_mod(self, file_path: Path) -> List[str]:
        content = file_path.read_text(encoding="utf-8")
        deps: List[str] = []
        in_require = False
        for line in content.split("\n"):
            line = line.strip()
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

    def _parse_pom_xml(self, file_path: Path) -> List[str]:
        content = file_path.read_text(encoding="utf-8")
        return re.findall(r"<artifactId>(.*?)</artifactId>", content)

    def _parse_gemfile(self, file_path: Path) -> List[str]:
        deps: List[str] = []
        for line in file_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("gem "):
                match = re.search(r'gem\s+["\']([^"\']+)', line)
                if match:
                    deps.append(match.group(1))
        return deps

    def _compile_results(self) -> AnalysisResult:
        return AnalysisResult(
            project_name=self.root_path.name,
            files_analyzed=self.files_analyzed,
            languages=dict(self.languages.most_common()),
            dependencies=self.dependencies,
            project_structure=self.project_structure,
            functions=self.functions,
            classes=self.classes,
            imports={lang: sorted(list(imps)) for lang, imps in self.imports.items()},
            documentation_files=self.documentation_files,
            config_files=self.config_files,
            git_info=self.git_info,
            is_website=self.is_website,
            website_detection_reason=self.website_detection_reason,
            root_path=self.root_path,
        )
