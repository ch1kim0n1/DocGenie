"""Quality scoring helpers for README generation."""

from __future__ import annotations

from typing import Any

# Quality scoring thresholds and constants
MIN_FILES_HIGH = 20
MIN_FILES_MEDIUM = 5
MIN_LANGUAGES = 2
MIN_SYMBOLS = 10
CONFIDENCE_HIGH_THRESHOLD = 75
CONFIDENCE_MEDIUM_THRESHOLD = 50

# Score point allocations
SCORE_BASE = 30
SCORE_FILES_HIGH = 20
SCORE_FILES_MEDIUM = 10
SCORE_LANGUAGES_MULTI = 15
SCORE_LANGUAGES_SINGLE = 8
SCORE_SYMBOLS = 20
SCORE_SYMBOLS_ANY = 10
SCORE_DEPENDENCIES = 10
SCORE_TESTS = 5


def build_quality_report(analysis_data: dict[str, Any], *, has_tests: bool) -> dict[str, Any]:
    """Compute simple quality/confidence signals for generated docs."""
    files_analyzed = int(analysis_data.get("files_analyzed", 0) or 0)
    languages = analysis_data.get("languages", {})
    functions = analysis_data.get("functions", [])
    classes = analysis_data.get("classes", [])
    dependencies = analysis_data.get("dependencies", {})

    score = SCORE_BASE
    warnings: list[str] = []

    # Score based on file count
    score += _score_files(files_analyzed, warnings)

    # Score based on language diversity
    score += _score_languages(languages, warnings)

    # Score based on code symbols
    score += _score_symbols(functions, classes, warnings)

    # Score based on dependencies
    if dependencies:
        score += SCORE_DEPENDENCIES
    else:
        warnings.append("No dependency metadata files were detected.")

    # Score based on tests
    if has_tests:
        score += SCORE_TESTS
    else:
        warnings.append("No tests detected. Generated usage guidance may need manual review.")

    score = max(0, min(score, 100))
    if score >= CONFIDENCE_HIGH_THRESHOLD:
        confidence = "High"
    elif score >= CONFIDENCE_MEDIUM_THRESHOLD:
        confidence = "Medium"
    else:
        confidence = "Low"
    return {"score": score, "confidence": confidence, "warnings": warnings}


def _score_files(files_analyzed: int, warnings: list[str]) -> int:
    """Return score based on file count."""
    if files_analyzed >= MIN_FILES_HIGH:
        return SCORE_FILES_HIGH
    if files_analyzed >= MIN_FILES_MEDIUM:
        return SCORE_FILES_MEDIUM
    warnings.append("Low file count analyzed. Results may be incomplete.")
    return 0


def _score_languages(languages: dict[str, int], warnings: list[str]) -> int:
    """Return score based on language diversity."""
    if len(languages) >= MIN_LANGUAGES:
        return SCORE_LANGUAGES_MULTI
    if len(languages) == 1:
        return SCORE_LANGUAGES_SINGLE
    warnings.append("No recognized source languages detected.")
    return 0


def _score_symbols(functions: list[Any], classes: list[Any], warnings: list[str]) -> int:
    """Return score based on code symbol count."""
    symbol_count = len(functions) + len(classes)
    if symbol_count >= MIN_SYMBOLS:
        return SCORE_SYMBOLS
    if symbol_count >= 1:
        return SCORE_SYMBOLS_ANY
    warnings.append("No functions/classes were extracted from source files.")
    return 0
