"""Git-based diff analysis for DocGenie."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from git import GitCommandError, InvalidGitRepositoryError, NoSuchPathError, Repo

from .parsers import ParserRegistry
from .utils import get_file_language

MIN_TAGS_FOR_PREV = 2
NUMSTAT_PARTS = 3


_DIFF_UNAVAILABLE: dict[str, Any] = {
    "available": False,
    "from_ref": None,
    "to_ref": None,
    "message": "Diff unavailable",
    "files": [],
    "totals": {"added": 0, "modified": 0, "deleted": 0, "renamed": 0, "changes": 0},
    "folder_stats": {},
}


def _safe_read_blob(repo: Repo, ref: str, rel_path: str) -> str:
    try:
        text = repo.git.show(f"{ref}:{rel_path}")
    except GitCommandError:
        return ""
    return text


def _symbol_count(content: str, rel_path: str, parser_registry: ParserRegistry) -> int:
    language = get_file_language(Path(rel_path))
    if not language or not content:
        return 0
    parsed = parser_registry.parse(content, Path(rel_path), language)
    return len(parsed.functions) + len(parsed.classes)


def _default_from_ref(repo: Repo) -> str:
    tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
    if len(tags) >= MIN_TAGS_FOR_PREV:
        return str(tags[-2])
    return "HEAD~1"


def compute_git_diff_summary(  # noqa: PLR0915
    root_path: Path,
    *,
    from_ref: str | None,
    to_ref: str = "HEAD",
    rename_detection: bool = True,
    enable_tree_sitter: bool = True,
) -> dict[str, Any]:
    """Compute git diff summary and per-file details."""
    try:
        repo = Repo(root_path, search_parent_directories=True)
    except (InvalidGitRepositoryError, NoSuchPathError):
        unavailable = dict(_DIFF_UNAVAILABLE)
        unavailable["message"] = "Not a git repository"
        return unavailable

    from_ref_resolved = from_ref or _default_from_ref(repo)
    try:
        left = repo.commit(from_ref_resolved)
        right = repo.commit(to_ref)
    except (GitCommandError, ValueError):
        unavailable = dict(_DIFF_UNAVAILABLE)
        unavailable["message"] = "Invalid git refs"
        unavailable["from_ref"] = from_ref_resolved
        unavailable["to_ref"] = to_ref
        return unavailable

    diff_index = left.diff(right, create_patch=False, R=rename_detection)

    numstat_map: dict[str, tuple[int, int]] = {}
    try:
        for line in repo.git.diff("--numstat", from_ref_resolved, to_ref).splitlines():
            parts = line.split("\t")
            if len(parts) < NUMSTAT_PARTS:
                continue
            added_raw, deleted_raw, path_raw = parts[0], parts[1], parts[2]
            path = path_raw.split("=>")[-1].strip().replace("{", "").replace("}", "")
            added = int(added_raw) if added_raw.isdigit() else 0
            deleted = int(deleted_raw) if deleted_raw.isdigit() else 0
            numstat_map[path] = (added, deleted)
    except GitCommandError:
        pass

    parser_registry = ParserRegistry(enable_tree_sitter=enable_tree_sitter)
    files: list[dict[str, Any]] = []
    folders: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "files_changed": 0,
            "added_lines": 0,
            "deleted_lines": 0,
            "high_risk_files": 0,
        }
    )
    totals = {"added": 0, "modified": 0, "deleted": 0, "renamed": 0, "changes": 0}

    for item in diff_index:
        change_type = item.change_type or "M"
        rel_path = (item.b_path or item.a_path or "").replace("\\", "/")
        if not rel_path:
            continue

        added_lines, deleted_lines = numstat_map.get(rel_path, (0, 0))
        before = _safe_read_blob(repo, from_ref_resolved, item.a_path or rel_path)
        after = _safe_read_blob(repo, to_ref, item.b_path or rel_path)
        symbol_delta = _symbol_count(after, rel_path, parser_registry) - _symbol_count(
            before, item.a_path or rel_path, parser_registry
        )

        if change_type == "A":
            totals["added"] += 1
        elif change_type == "D":
            totals["deleted"] += 1
        elif change_type == "R":
            totals["renamed"] += 1
        else:
            totals["modified"] += 1

        churn = added_lines + deleted_lines
        totals["changes"] += churn

        folder = str(Path(rel_path).parent).replace("\\", "/")
        folder = "." if folder in {"", "."} else folder
        folders[folder]["files_changed"] += 1
        folders[folder]["added_lines"] += added_lines
        folders[folder]["deleted_lines"] += deleted_lines

        files.append(
            {
                "path": rel_path,
                "old_path": item.a_path,
                "change_type": change_type,
                "added_lines": added_lines,
                "deleted_lines": deleted_lines,
                "churn": churn,
                "symbol_delta": symbol_delta,
                "folder": folder,
            }
        )

    return {
        "available": True,
        "from_ref": from_ref_resolved,
        "to_ref": to_ref,
        "message": "ok",
        "files": sorted(files, key=lambda x: x["path"]),
        "totals": totals,
        "folder_stats": dict(folders),
    }
