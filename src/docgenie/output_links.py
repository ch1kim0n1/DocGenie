"""Heuristic output-flow link detection."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .utils import get_file_language, should_ignore_file

PY_WRITE_RE = re.compile(r"open\((['\"])([^'\"]+)\1\s*,\s*(['\"])[wax][bt+]?\3")
PY_PATH_WRITE_RE = re.compile(r"Path\((['\"])([^'\"]+)\1\)\.(write_text|write_bytes)\(")
PY_OPEN_GENERIC_RE = re.compile(r"open\((.+?),\s*(['\"])[wax][bt+]?\2")
JS_WRITE_RE = re.compile(r"(?:fs\.)?writeFile(?:Sync)?\((['\"])([^'\"]+)\1")
JS_STREAM_RE = re.compile(r"createWriteStream\((['\"])([^'\"]+)\1")
SHELL_REDIRECT_RE = re.compile(r">>\s*([^\s]+)|>\s*([^\s]+)")
SHELL_TEE_RE = re.compile(r"\btee\s+([^\s|;]+)")


def _normalize_target(root: Path, source_file: Path, raw_target: str) -> tuple[str | None, bool]:
    cleaned = raw_target.strip().strip("'\"")
    if "$" in cleaned or "{" in cleaned:
        return None, False
    target = Path(cleaned)
    abs_target = target if target.is_absolute() else (source_file.parent / target)
    try:
        rel = abs_target.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return None, False
    return rel.as_posix(), (root / rel).exists()


def scan_output_links(  # noqa: PLR0912, PLR0915
    root_path: Path,
    *,
    ignore_patterns: list[str] | None = None,
    languages: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Scan repository for likely source->output file writes."""
    selected_languages = set(languages or ["python", "javascript", "typescript", "shell"])
    links: list[dict[str, Any]] = []
    ignore = ignore_patterns or []

    for path in root_path.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root_path).as_posix()
        if should_ignore_file(rel, ignore):
            continue
        language = get_file_language(path)
        if language not in selected_languages:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue

        for idx, line in enumerate(lines, 1):
            raw_target: str | None = None
            op = ""
            confidence = "medium"

            if language == "python":
                pairs = ((PY_WRITE_RE, "open-write"), (PY_PATH_WRITE_RE, "path-write"))
                for regex, op_name in pairs:
                    m = regex.search(line)
                    if m:
                        raw_target = m.group(2)
                        op = op_name
                        confidence = "high"
                        break
                if not raw_target:
                    dynamic = PY_OPEN_GENERIC_RE.search(line)
                    if dynamic:
                        raw_target = "${dynamic}"
                        op = "open-write"
                        confidence = "low"
            elif language in {"javascript", "typescript"}:
                m = JS_WRITE_RE.search(line) or JS_STREAM_RE.search(line)
                if m:
                    raw_target = m.group(2)
                    op = "fs-write"
                    confidence = "high"
            elif language == "shell":
                m = SHELL_TEE_RE.search(line)
                if m:
                    raw_target = m.group(1)
                    op = "tee"
                    confidence = "medium"
                else:
                    m2 = SHELL_REDIRECT_RE.search(line)
                    if m2:
                        raw_target = m2.group(1) or m2.group(2)
                        op = "redirect"
                        confidence = "medium"

            if not raw_target:
                continue
            target_file, resolved = _normalize_target(root_path, path, raw_target)
            links.append(
                {
                    "source_file": rel,
                    "source_line": idx,
                    "target_file": target_file,
                    "operation": op,
                    "confidence": confidence,
                    "resolved": resolved,
                    "evidence_snippet": line.strip()[:160],
                }
            )

    return links
