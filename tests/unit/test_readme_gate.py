from __future__ import annotations

from docgenie.readme_gate import evaluate_readme_readiness


def test_readme_gate_pass() -> None:
    readme = "# P\n\n## Installation\n\n## Usage\n\n## Architecture\n\n## License\n"
    result = evaluate_readme_readiness(
        readme,
        analysis_data={"confidence_level": "high", "file_reviews": [], "output_links": []},
    )
    assert result["status"] == "pass"


def test_readme_gate_fail() -> None:
    result = evaluate_readme_readiness(
        "# P\n",
        analysis_data={
            "confidence_level": "low",
            "file_reviews": [{"risk_level": "high"}, {"risk_level": "high"}],
            "output_links": [{"resolved": False}],
        },
        min_confidence="high",
    )
    assert result["status"] in {"warn", "fail"}
    assert result["score"] < 80
