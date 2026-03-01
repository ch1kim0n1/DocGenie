"""README replacement readiness scoring."""

from __future__ import annotations

from typing import Any

CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}
PASS_THRESHOLD = 80
WARN_THRESHOLD = 60
DEFAULT_REQUIRED_SECTIONS = [
    "#",
    "## Installation",
    "## Usage",
    "## Architecture",
    "## License",
]


def evaluate_readme_readiness(
    readme_content: str,
    *,
    analysis_data: dict[str, Any],
    required_sections: list[str] | None = None,
    min_confidence: str = "medium",
) -> dict[str, Any]:
    required = required_sections or DEFAULT_REQUIRED_SECTIONS
    reasons: list[str] = []
    score = 100

    for section in required:
        if section not in readme_content:
            score -= 10
            reasons.append(f"Missing section: {section}")

    confidence = str(analysis_data.get("confidence_level", "low")).lower()
    if CONFIDENCE_ORDER.get(confidence, 0) < CONFIDENCE_ORDER.get(min_confidence, 1):
        score -= 20
        reasons.append(f"Analysis confidence {confidence} is below minimum {min_confidence}")

    unresolved_outputs = [x for x in analysis_data.get("output_links", []) if not x.get("resolved")]
    if unresolved_outputs:
        score -= min(20, len(unresolved_outputs) * 2)
        reasons.append(f"{len(unresolved_outputs)} unresolved output link(s)")

    high_risk = [x for x in analysis_data.get("file_reviews", []) if x.get("risk_level") == "high"]
    if high_risk:
        score -= min(20, len(high_risk) * 3)
        reasons.append(f"{len(high_risk)} high-risk changed file(s)")

    score = max(0, min(score, 100))
    if score >= PASS_THRESHOLD:
        status = "pass"
    elif score >= WARN_THRESHOLD:
        status = "warn"
    else:
        status = "fail"

    return {
        "score": score,
        "status": status,
        "reasons": reasons,
        "required_sections": required,
        "min_confidence": min_confidence,
    }
