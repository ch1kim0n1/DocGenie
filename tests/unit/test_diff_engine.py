from __future__ import annotations

from pathlib import Path

from git import Repo

from docgenie.diff_engine import compute_git_diff_summary


def test_diff_engine_non_git(tmp_path: Path) -> None:
    summary = compute_git_diff_summary(tmp_path, from_ref=None, to_ref="HEAD")
    assert summary["available"] is False


def test_diff_engine_basic_git(tmp_path: Path) -> None:
    repo = Repo.init(tmp_path)
    f = tmp_path / "main.py"
    f.write_text("def a():\n    return 1\n", encoding="utf-8")
    repo.index.add(["main.py"])
    repo.index.commit("initial")

    f.write_text("def a():\n    return 2\n\ndef b():\n    return 3\n", encoding="utf-8")
    repo.index.add(["main.py"])
    repo.index.commit("second")

    summary = compute_git_diff_summary(tmp_path, from_ref="HEAD~1", to_ref="HEAD")
    assert summary["available"] is True
    assert summary["totals"]["modified"] >= 1
    assert summary["files"][0]["path"] == "main.py"
