from __future__ import annotations

from docgenie.review_engine import build_reviews


def test_build_reviews_from_diff() -> None:
    diff_summary = {
        "available": True,
        "files": [
            {
                "path": "src/a.py",
                "change_type": "M",
                "churn": 120,
                "symbol_delta": 2,
                "folder": "src",
            },
            {
                "path": "src/b.py",
                "change_type": "A",
                "churn": 5,
                "symbol_delta": 0,
                "folder": "src",
            },
        ],
    }
    file_reviews, folder_reviews = build_reviews(
        diff_summary=diff_summary,
        functions=[{"file": "src/a.py"}],
        classes=[{"file": "src/a.py"}],
    )
    assert len(file_reviews) == 2
    assert folder_reviews[0]["folder"] == "src"
    assert file_reviews[0]["risk_level"] in {"low", "medium", "high"}
