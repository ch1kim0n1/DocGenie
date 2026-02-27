from __future__ import annotations

import builtins
import json
from pathlib import Path

import pytest

from docgenie import core
from docgenie.core import CodebaseAnalyzer, _analyze_file_task


def test_analyze_file_task_handles_no_language_and_permission(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    unknown = tmp_path / "x.unknown"
    unknown.write_text("x", encoding="utf-8")
    p, lang, parsed, digest = _analyze_file_task((str(unknown), [], False))
    assert p == str(unknown)
    assert lang == ""
    assert parsed is None
    assert digest == ""

    py = tmp_path / "a.py"
    py.write_text("def x():\n    return 1\n", encoding="utf-8")

    def raise_perm(*_args, **_kwargs):
        raise PermissionError("no")

    monkeypatch.setattr(builtins, "open", raise_perm)
    p2, lang2, parsed2, digest2 = _analyze_file_task((str(py), [], False))
    assert p2 == str(py)
    assert lang2 == "python"
    assert parsed2 is None
    assert digest2 == ""


def test_apply_parsed_data_unknown_language(tmp_path: Path) -> None:
    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)
    target = tmp_path / "file.noext"
    target.write_text("x", encoding="utf-8")
    analyzer._apply_parsed_data({"functions": [], "classes": [], "imports": ["os"]}, target, None)
    assert analyzer.languages["unknown"] == 1
    assert analyzer.imports["unknown"] == {"os"}


def test_iter_source_files_and_structure_ignore(tmp_path: Path) -> None:
    (tmp_path / "keep.py").write_text("pass", encoding="utf-8")
    (tmp_path / "ignore.log").write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "keep2.py").write_text("pass", encoding="utf-8")
    analyzer = CodebaseAnalyzer(str(tmp_path), ignore_patterns=["*.log"], enable_tree_sitter=False)
    files = list(analyzer._iter_source_files())
    assert all(not f.name.endswith(".log") for f in files)
    analyzer._analyze_project_structure()
    assert "root" in analyzer.project_structure


def test_iter_source_files_honors_gitignore_generated_hidden_and_size(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("ignored_dir/\nignored.py\n", encoding="utf-8")
    (tmp_path / "ignored.py").write_text("def x(): pass\n", encoding="utf-8")
    (tmp_path / "ignored_dir").mkdir()
    (tmp_path / "ignored_dir" / "a.py").write_text("def x(): pass\n", encoding="utf-8")
    (tmp_path / ".hidden.py").write_text("def x(): pass\n", encoding="utf-8")
    (tmp_path / "generated.lock").write_text("lock", encoding="utf-8")
    (tmp_path / "big.py").write_text("x" * 4096, encoding="utf-8")
    (tmp_path / "ok.py").write_text("def ok():\n    return 1\n", encoding="utf-8")

    analyzer = CodebaseAnalyzer(
        str(tmp_path),
        enable_tree_sitter=False,
        config={
            "analysis": {
                "use_gitignore": True,
                "exclude_generated": True,
                "include_hidden": False,
                "max_file_size_kb": 1,
                "generated_patterns": [],
            }
        },
    )
    files = {p.name for p in analyzer._iter_source_files()}
    assert "ok.py" in files
    assert "ignored.py" not in files
    assert "a.py" not in files
    assert ".hidden.py" not in files
    assert "generated.lock" not in files
    assert "big.py" not in files


def test_core_handles_invalid_size_config_and_stat_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    analyzer = CodebaseAnalyzer(
        str(tmp_path),
        enable_tree_sitter=False,
        config={"analysis": {"max_file_size_kb": "not-a-number"}},
    )
    assert analyzer.max_file_size_kb is None

    analyzer_with_limit = CodebaseAnalyzer(
        str(tmp_path),
        enable_tree_sitter=False,
        config={"analysis": {"max_file_size_kb": 1}},
    )

    test_file = tmp_path / "err.py"
    test_file.write_text("pass\n", encoding="utf-8")

    def broken_stat(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        _ = (args, kwargs)
        raise OSError("stat failed")

    monkeypatch.setattr(Path, "stat", broken_stat)
    assert analyzer_with_limit._should_skip_path(test_file, is_dir=False) is True


def test_dependency_parsers_and_detect_dependencies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)

    req = tmp_path / "requirements.txt"
    req.write_text("# comment\n-r extra.txt\nrequests>=2\n flask==2\n", encoding="utf-8")
    assert analyzer._parse_requirements_txt(req) == ["requests", "flask"]

    pkg = tmp_path / "package.json"
    pkg.write_text(json.dumps({"dependencies": {"react": "1"}, "devDependencies": {"vite": "1"}}), encoding="utf-8")
    assert analyzer._parse_package_json(pkg) == {"dependencies": ["react"], "devDependencies": ["vite"]}

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\ndependencies=['a']\n[project.optional-dependencies]\ndev=['b']\n"
        "[tool.poetry.dependencies]\npython='^3.10'\nrequests='*'\n"
        "[tool.poetry.dev-dependencies]\npytest='*'\n",
        encoding="utf-8",
    )
    pdeps = analyzer._parse_pyproject_toml(pyproject)
    assert "dependencies" in pdeps and "optional-dependencies" in pdeps
    assert "poetry-dependencies" in pdeps and "poetry-dev-dependencies" in pdeps

    setup = tmp_path / "setup.py"
    setup.write_text("install_requires=['a>=1','b']", encoding="utf-8")
    assert analyzer._parse_setup_py(setup) == ["a", ",", "b"]
    setup.write_text("print('no deps')", encoding="utf-8")
    assert analyzer._parse_setup_py(setup) == []

    cargo = tmp_path / "Cargo.toml"
    cargo.write_text("[dependencies]\nserde='1'\n[dev-dependencies]\nproptest='1'\n", encoding="utf-8")
    assert analyzer._parse_cargo_toml(cargo) == {"dependencies": ["serde"], "dev-dependencies": ["proptest"]}

    gomod = tmp_path / "go.mod"
    gomod.write_text("module x\nrequire github.com/a/b v1\nrequire (\n github.com/c/d v2\n)\n", encoding="utf-8")
    assert analyzer._parse_go_mod(gomod) == ["github.com/a/b", "github.com/c/d"]

    pom = tmp_path / "pom.xml"
    pom.write_text("<artifactId>a</artifactId><artifactId>b</artifactId>", encoding="utf-8")
    assert analyzer._parse_pom_xml(pom) == ["a", "b"]

    gem = tmp_path / "Gemfile"
    gem.write_text("gem 'rails'\nsource 'x'\n", encoding="utf-8")
    assert analyzer._parse_gemfile(gem) == ["rails"]

    # Malformed dependency file should be ignored in _detect_dependencies exception path.
    bad_pkg = tmp_path / "package.json"
    bad_pkg.write_text("{not json", encoding="utf-8")
    analyzer._detect_dependencies()
    assert "requirements.txt" in analyzer.dependencies
    assert "package.json" not in analyzer.dependencies

    def broken_parser(_path: Path):
        raise ValueError("broken")

    monkeypatch.setattr(analyzer, "_parse_gemfile", broken_parser)
    analyzer.dependencies.clear()
    analyzer._detect_dependencies()
    assert isinstance(analyzer.dependencies, dict)


def test_analyze_with_mocked_process_pool(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    analyzer = CodebaseAnalyzer(str(tmp_path), enable_tree_sitter=False)

    class DummyFuture:
        def __init__(self, result):
            self._result = result

        def result(self):
            return self._result

    class DummyExecutor:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def submit(self, fn, payload):
            return DummyFuture(fn(payload))

    monkeypatch.setattr(core, "ProcessPoolExecutor", DummyExecutor)
    monkeypatch.setattr(core, "as_completed", lambda futures: list(futures.keys()))

    result = analyzer.analyze()
    assert result["files_analyzed"] >= 1
    assert result["website_detection_reason"]
