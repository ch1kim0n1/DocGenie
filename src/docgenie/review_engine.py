"""File and folder review scoring engine."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

_DEFAULT_WEIGHTS = {"churn": 0.35, "complexity": 0.35, "surface": 0.30}
RISK_HIGH = 0.7
RISK_MEDIUM = 0.4


def _risk_level(score: float) -> str:
    if score >= RISK_HIGH:
        return "high"
    if score >= RISK_MEDIUM:
        return "medium"
    return "low"


def build_reviews(
    *,
    diff_summary: dict[str, Any],
    functions: list[dict[str, Any]],
    classes: list[dict[str, Any]],
    weights: dict[str, float] | None = None,
    max_files_per_folder: int = 50,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build per-file and per-folder review cards."""
    if not diff_summary.get("available"):
        return [], []

    applied_weights = dict(_DEFAULT_WEIGHTS)
    if weights:
        applied_weights.update(weights)

    symbol_counts: dict[str, int] = defaultdict(int)
    for func in functions:
        file_path = str(func.get("file", "")).replace("\\", "/")
        if file_path:
            symbol_counts[file_path] += 1
    for cls in classes:
        file_path = str(cls.get("file", "")).replace("\\", "/")
        if file_path:
            symbol_counts[file_path] += 1

    file_reviews: list[dict[str, Any]] = []
    folder_rollups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "folder": ".",
            "files_changed": 0,
            "risk_distribution": {"low": 0, "medium": 0, "high": 0},
            "top_risky_files": [],
        }
    )

    grouped_files: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in diff_summary.get("files", []):
        grouped_files[item.get("folder", ".")].append(item)

    for folder, items in grouped_files.items():
        by_churn = sorted(items, key=lambda i: i.get("churn", 0), reverse=True)
        for item in by_churn[:max_files_per_folder]:
            path = str(item.get("path", ""))
            churn = int(item.get("churn", 0))
            change_type = str(item.get("change_type", "M"))
            symbol_delta = abs(int(item.get("symbol_delta", 0)))
            churn_component = min(churn / 200.0, 1.0)
            complexity_component = min(symbol_delta / 8.0, 1.0)
            surface_component = 0.9 if change_type in {"A", "D", "R"} else 0.5

            score = (
                applied_weights["churn"] * churn_component
                + applied_weights["complexity"] * complexity_component
                + applied_weights["surface"] * surface_component
            )
            level = _risk_level(score)

            rationale = [f"Change type: {change_type}", f"Churn: {churn} lines"]
            if symbol_delta:
                rationale.append(f"Symbol delta: {symbol_delta}")
            if symbol_counts.get(path):
                rationale.append(f"Known symbols in file: {symbol_counts[path]}")

            review = {
                "path": path,
                "folder": folder,
                "change_type": change_type,
                "risk_score": round(score, 3),
                "risk_level": level,
                "churn": churn,
                "symbol_delta": int(item.get("symbol_delta", 0)),
                "rationale": rationale,
            }
            file_reviews.append(review)

            rollup = folder_rollups[folder]
            rollup["folder"] = folder
            rollup["files_changed"] += 1
            rollup["risk_distribution"][level] += 1
            rollup["top_risky_files"].append(
                {
                    "path": path,
                    "risk_level": level,
                    "risk_score": review["risk_score"],
                }
            )

    folder_reviews = []
    for folder, rollup in folder_rollups.items():
        top = sorted(rollup["top_risky_files"], key=lambda x: x["risk_score"], reverse=True)[:5]
        folder_reviews.append(
            {
                "folder": folder,
                "files_changed": rollup["files_changed"],
                "risk_distribution": rollup["risk_distribution"],
                "top_risky_files": top,
            }
        )

    file_reviews.sort(key=lambda x: x["risk_score"], reverse=True)
    folder_reviews.sort(key=lambda x: x["files_changed"], reverse=True)
    return file_reviews, folder_reviews
