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


def test_diff_direction_added_not_reversed(tmp_path: Path) -> None:
    """Issue #33: from->to direction must classify a new file as added, not deleted."""
    repo = Repo.init(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    repo.index.add(["a.py"])
    repo.index.commit("initial")

    # Add a brand-new file in the 'to' commit.
    (tmp_path / "b.py").write_text("y = 2\n", encoding="utf-8")
    repo.index.add(["b.py"])
    repo.index.commit("add b")

    summary = compute_git_diff_summary(tmp_path, from_ref="HEAD~1", to_ref="HEAD")
    assert summary["totals"]["added"] == 1
    assert summary["totals"]["deleted"] == 0
    b = next(f for f in summary["files"] if f["path"] == "b.py")
    assert b["change_type"] == "A"
    # numstat added lines should be positive (consistent direction).
    assert b["added_lines"] >= 1


def test_no_rename_detection_shows_add_and_delete(tmp_path: Path) -> None:
    """Issue #33: --no-rename-detection must surface renames as add + delete."""
    repo = Repo.init(tmp_path)
    content = "def func():\n    return 42\n" * 5
    (tmp_path / "old.py").write_text(content, encoding="utf-8")
    repo.index.add(["old.py"])
    repo.index.commit("initial")

    # Rename old.py -> new.py with identical content.
    (tmp_path / "new.py").write_text(content, encoding="utf-8")
    (tmp_path / "old.py").unlink()
    repo.index.remove(["old.py"])
    repo.index.add(["new.py"])
    repo.index.commit("rename")

    with_rename = compute_git_diff_summary(
        tmp_path, from_ref="HEAD~1", to_ref="HEAD", rename_detection=True
    )
    without_rename = compute_git_diff_summary(
        tmp_path, from_ref="HEAD~1", to_ref="HEAD", rename_detection=False
    )
    assert with_rename["totals"]["renamed"] == 1
    # When rename detection is disabled, the rename appears as add + delete.
    assert without_rename["totals"]["renamed"] == 0
    assert without_rename["totals"]["added"] == 1
    assert without_rename["totals"]["deleted"] == 1
