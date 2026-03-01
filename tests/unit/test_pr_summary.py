from __future__ import annotations

from docgenie.pr_summary import render_pr_summary


def test_render_pr_summary_markdown() -> None:
    analysis = {
        "diff_summary": {
            "from_ref": "v1",
            "to_ref": "HEAD",
            "totals": {"added": 1, "modified": 2, "deleted": 0, "renamed": 0, "changes": 23},
            "files": [
                {"path": "a.py", "change_type": "M", "added_lines": 5, "deleted_lines": 2, "churn": 7}
            ],
        },
        "file_reviews": [{"path": "a.py", "risk_level": "high", "risk_score": 0.9}],
        "output_links": [{"source_file": "a.py", "source_line": 10, "target_file": "out.txt", "confidence": "high"}],
        "readme_readiness": {"status": "warn", "score": 72},
    }
    text = render_pr_summary(analysis)
    assert "DocGenie PR Summary" in text
    assert "Highest-Churn Files" in text
    assert "High-Risk Files" in text
    assert "Output Flow Notes" in text
