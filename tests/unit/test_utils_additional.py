from __future__ import annotations

from pathlib import Path

import pytest

from docgenie import utils


def test_get_file_language_unknown() -> None:
    assert utils.get_file_language(Path("README.unknownext")) is None


def test_should_ignore_file_with_additional_pattern() -> None:
    assert utils.should_ignore_file("src/notes.cache", ["*.cache"])
    assert utils.should_ignore_file("src/generated/output.py", ["generated"])
    assert not utils.should_ignore_file("src/main.keep", ["*.cache"])


def test_gitignore_and_generated_helpers(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("ignored_dir/\n*.secret\n", encoding="utf-8")
    matcher = utils.load_gitignore_spec(tmp_path)
    assert matcher is not None
    assert utils.is_path_ignored_by_gitignore("ignored_dir/file.py", matcher, is_dir=False)
    assert utils.is_path_ignored_by_gitignore("ignored_dir", matcher, is_dir=True)
    assert utils.is_path_ignored_by_gitignore("key.secret", matcher, is_dir=False)
    assert not utils.is_path_ignored_by_gitignore("src/main.py", matcher, is_dir=False)
    assert utils.load_gitignore_spec(tmp_path / "missing") is None

    assert utils.is_hidden_path(".env")
    assert utils.is_hidden_path("src/.cache/file.py")
    assert not utils.is_hidden_path("src/main.py")

    assert utils.is_probably_generated_file("dist/app.js")
    assert utils.is_probably_generated_file("foo.lock")
    assert utils.is_probably_generated_file("main.pb.go")
    assert utils.is_probably_generated_file("src/custom.xyz", ["*.xyz"])
    assert not utils.is_probably_generated_file("src/main.py")


def test_load_gitignore_spec_read_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    file_path = tmp_path / ".gitignore"
    file_path.write_text("*.tmp\n", encoding="utf-8")

    def broken_read_text(self, encoding: str = "utf-8"):  # type: ignore[no-untyped-def]
        raise OSError("read failure")

    monkeypatch.setattr(Path, "read_text", broken_read_text)
    assert utils.load_gitignore_spec(tmp_path) is None


def test_detect_packages(tmp_path: Path) -> None:
    (tmp_path / "service-a").mkdir()
    (tmp_path / "service-a" / "pyproject.toml").write_text("[project]\nname='a'\n", encoding="utf-8")
    (tmp_path / "service-b").mkdir()
    (tmp_path / "service-b" / "package.json").write_text("{\"name\":\"b\"}", encoding="utf-8")
    pkgs = utils.detect_packages(tmp_path)
    paths = {p["path"] for p in pkgs}
    assert "service-a" in paths
    assert "service-b" in paths


def test_extract_repo_name_from_url_variants() -> None:
    assert utils.extract_repo_name_from_url("git@github.com:owner/repo.git") == "owner/repo"
    assert utils.extract_repo_name_from_url("https://github.com/owner/repo.git") == "owner/repo"
    raw = "not-a-url"
    assert utils.extract_repo_name_from_url(raw) == raw


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (0, "0 B"),
        (1024, "1.0 KB"),
        (1024 * 1024, "1.0 MB"),
    ],
)
def test_format_file_size(size: int, expected: str) -> None:
    assert utils.format_file_size(size) == expected


def _analysis(files: list[str], deps: dict, languages: dict[str, int], extra_paths: list[str] | None = None) -> dict:
    structure = {"root": {"files": files, "dirs": []}}
    for p in extra_paths or []:
        structure[p] = {"files": [], "dirs": []}
    return {
        "project_structure": structure,
        "dependencies": deps,
        "languages": languages,
        "main_language": "python",
    }


def test_is_website_project_via_all_key_paths() -> None:
    assert utils.is_website_project(_analysis(["index.html"], {}, {"python": 1}))
    assert utils.is_website_project(_analysis(["mkdocs.yml"], {}, {"python": 1}))
    assert utils.is_website_project(_analysis(["README.md"], {"package.json": ["react"]}, {"python": 1}))
    assert utils.is_website_project(_analysis(["style.css"], {}, {"css": 2, "python": 1}))
    assert utils.is_website_project(_analysis(["README.md"], {}, {"css": 1, "python": 1}, ["public/assets"]))


def test_get_project_type_website_variants() -> None:
    assert utils.get_project_type(_analysis(["index.html", "package.json"], {"package.json": ["react"]}, {"html": 1})) == "React Website"
    assert utils.get_project_type(_analysis(["index.html", "package.json"], {"package.json": ["vue"]}, {"html": 1})) == "Vue.js Website"
    assert utils.get_project_type(_analysis(["index.html", "package.json"], {"package.json": ["angular"]}, {"html": 1})) == "Angular Website"
    assert utils.get_project_type(_analysis(["index.html", "package.json"], {"package.json": ["gatsby"]}, {"html": 1})) == "Gatsby Static Website"
    assert utils.get_project_type(_analysis(["index.html", "package.json"], {"package.json": ["next"]}, {"html": 1})) == "Next.js Website"
    assert utils.get_project_type(_analysis(["index.html", "package.json"], {"package.json": ["jquery"]}, {"html": 1})) == "JavaScript Website"
    assert utils.get_project_type(_analysis(["hugo.toml"], {}, {"html": 1})) == "Static Website (Hugo/Jekyll)"
    assert utils.get_project_type(_analysis(["index.html"], {"requirements.txt": ["django"]}, {"html": 1})) == "Django Website"
    assert utils.get_project_type(_analysis(["index.html"], {"requirements.txt": ["flask"]}, {"html": 1})) == "Flask Website"
    assert utils.get_project_type(_analysis(["index.html"], {}, {"html": 1})) == "Website"


def test_get_project_type_non_website_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(utils, "is_website_project", lambda _analysis_data: False)

    assert (
        utils.get_project_type(_analysis(["package.json"], {"package.json": ["react"]}, {"python": 1}))
        == "React Application"
    )
    assert (
        utils.get_project_type(_analysis(["package.json"], {"package.json": ["vue"]}, {"python": 1}))
        == "Vue.js Application"
    )
    assert (
        utils.get_project_type(
            _analysis(["package.json"], {"package.json": ["angular"]}, {"python": 1})
        )
        == "Angular Application"
    )
    assert (
        utils.get_project_type(
            _analysis(["package.json"], {"package.json": ["express"]}, {"python": 1})
        )
        == "Node.js/Express Application"
    )
    assert (
        utils.get_project_type(
            _analysis(["package.json"], {"package.json": ["left-pad"]}, {"python": 1})
        )
        == "Node.js Application"
    )

    assert (
        utils.get_project_type(
            _analysis(["requirements.txt"], {"requirements.txt": ["django"]}, {"python": 1})
        )
        == "Django Application"
    )
    assert (
        utils.get_project_type(
            _analysis(["requirements.txt"], {"requirements.txt": ["flask"]}, {"python": 1})
        )
        == "Flask Application"
    )
    assert (
        utils.get_project_type(
            _analysis(["requirements.txt"], {"requirements.txt": ["fastapi"]}, {"python": 1})
        )
        == "FastAPI Application"
    )
    assert (
        utils.get_project_type(
            _analysis(["requirements.txt"], {"requirements.txt": ["requests"]}, {"python": 1})
        )
        == "Python Application"
    )

    assert utils.get_project_type(_analysis(["Cargo.toml"], {}, {"rust": 1})) == "Rust Application"
    assert utils.get_project_type(_analysis(["go.mod"], {}, {"go": 1})) == "Go Application"
    assert utils.get_project_type(_analysis(["pom.xml"], {}, {"java": 1})) == "Java Application"
    assert utils.get_project_type(_analysis(["Gemfile"], {}, {"ruby": 1})) == "Ruby Application"

    assert (
        utils.get_project_type(
            {
                "project_structure": {"root": {"files": [], "dirs": []}},
                "dependencies": {},
                "languages": {},
                "main_language": "python",
            }
        )
        == "Python Project"
    )
    assert (
        utils.get_project_type(
            {
                "project_structure": {"root": {"files": [], "dirs": []}},
                "dependencies": {},
                "languages": {},
                "main_language": "unknown",
            }
        )
        == "Software Project"
    )


def test_create_directory_tree_limits_and_empty() -> None:
    tree = utils.create_directory_tree(
        {
            "root": {"files": [f"f{i}.py" for i in range(12)], "dirs": ["src"]},
            "src": {"files": ["a.py", "b.py", "c.py", "d.py", "e.py", "f.py"], "dirs": []},
            "deep/dir/level": {"files": ["x.py"], "dirs": []},
        },
        max_depth=2,
    )
    assert "... and 2 more files" in tree
    assert "src/" in tree
    assert "deep/dir/level" not in tree
    assert utils.create_directory_tree({"root": {"files": [], "dirs": []}}) == "No files found"


def test_extract_git_info_happy_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class DummyAuthor:
        name = "A"
        email = "a@example.com"

    class DummyCommit:
        hexsha = "abc"
        author = DummyAuthor()
        committed_datetime = "2026-01-01"
        message = "msg\n"

    class DummyOrigin:
        url = "https://github.com/org/repo.git"

    class DummyHead:
        is_detached = False
        commit = DummyCommit()

    class DummyGit:
        def shortlog(self, *_args: object) -> str:
            return "1\tA\n2\tB"

    class DummyRepo:
        remotes = type("R", (), {"origin": DummyOrigin()})
        active_branch = type("B", (), {"name": "main"})
        head = DummyHead()
        git = DummyGit()

        def __init__(self, _path: Path, search_parent_directories: bool = True) -> None:
            _ = search_parent_directories

    monkeypatch.setattr(utils, "Repo", DummyRepo)
    info = utils.extract_git_info(tmp_path)
    assert info["repo_name"] == "org/repo"
    assert info["current_branch"] == "main"
    assert info["latest_commit"]["hash"] == "abc"
    assert info["contributor_count"] == 2


def test_extract_git_info_handles_all_failures(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class BadRepo:
        def __init__(self, _path: Path, search_parent_directories: bool = True) -> None:
            _ = search_parent_directories
            self.remotes = type("RR", (), {})()
            self.head = type("H", (), {"is_detached": False})()
            self.git = type("GG", (), {"shortlog": lambda *_a: (_ for _ in ()).throw(utils.GitCommandError("shortlog", 1))})()

        @property
        def active_branch(self) -> object:
            raise utils.GitCommandError("branch", 1)

    monkeypatch.setattr(utils, "Repo", BadRepo)
    assert isinstance(utils.extract_git_info(tmp_path), dict)

    class RaiseRepo:
        def __init__(self, _path: Path, search_parent_directories: bool = True) -> None:
            raise utils.InvalidGitRepositoryError("x")

    monkeypatch.setattr(utils, "Repo", RaiseRepo)
    assert utils.extract_git_info(tmp_path) == {}
