from __future__ import annotations

from docgenie.readme_quality import build_quality_report


def test_readme_quality_high_confidence_snapshot() -> None:
    report = build_quality_report(
        {
            "files_analyzed": 25,
            "languages": {"python": 20, "typescript": 5},
            "functions": [{}] * 8,
            "classes": [{}] * 4,
            "dependencies": {"pyproject.toml": {"dependencies": ["typer"]}},
        },
        has_tests=True,
    )
    assert report == {"score": 100, "confidence": "High", "warnings": []}


def test_readme_quality_low_confidence_snapshot() -> None:
    report = build_quality_report(
        {
            "files_analyzed": 1,
            "languages": {},
            "functions": [],
            "classes": [],
            "dependencies": {},
        },
        has_tests=False,
    )
    assert report["score"] == 30
    assert report["confidence"] == "Low"
    assert len(report["warnings"]) >= 4
