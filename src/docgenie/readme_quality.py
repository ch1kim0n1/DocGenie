"""Quality scoring helpers for README generation."""

from __future__ import annotations

from typing import Any


def build_quality_report(analysis_data: dict[str, Any], *, has_tests: bool) -> dict[str, Any]:
    """Compute simple quality/confidence signals for generated docs."""
    files_analyzed = int(analysis_data.get("files_analyzed", 0) or 0)
    languages = analysis_data.get("languages", {})
    functions = analysis_data.get("functions", [])
    classes = analysis_data.get("classes", [])
    dependencies = analysis_data.get("dependencies", {})

    score = 30
    warnings: list[str] = []

    if files_analyzed >= 20:
        score += 20
    elif files_analyzed >= 5:
        score += 10
    else:
        warnings.append("Low file count analyzed. Results may be incomplete.")

    if len(languages) >= 2:
        score += 15
    elif len(languages) == 1:
        score += 8
    else:
        warnings.append("No recognized source languages detected.")

    if len(functions) + len(classes) >= 10:
        score += 20
    elif len(functions) + len(classes) >= 1:
        score += 10
    else:
        warnings.append("No functions/classes were extracted from source files.")

    if dependencies:
        score += 10
    else:
        warnings.append("No dependency metadata files were detected.")

    if has_tests:
        score += 5
    else:
        warnings.append("No tests detected. Generated usage guidance may need manual review.")

    score = max(0, min(score, 100))
    if score >= 75:
        confidence = "High"
    elif score >= 50:
        confidence = "Medium"
    else:
        confidence = "Low"
    return {"score": score, "confidence": confidence, "warnings": warnings}
