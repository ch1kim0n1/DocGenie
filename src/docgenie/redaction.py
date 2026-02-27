"""Redaction helpers for generated documentation content."""

from __future__ import annotations

import re
from re import Pattern

BASE_PATTERNS = [
    (
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?"
        r"-----END [A-Z ]*PRIVATE KEY-----",
        "[REDACTED_PRIVATE_KEY]",
    ),
    (r"(?i)(api[_-]?key\s*[:=]\s*)[\"']?[A-Za-z0-9_\-]{12,}[\"']?", r"\1[REDACTED]"),
    (r"(?i)(token\s*[:=]\s*)[\"']?[A-Za-z0-9_\-\.]{12,}[\"']?", r"\1[REDACTED]"),
    (r"(?i)(secret\s*[:=]\s*)[\"']?[A-Za-z0-9_\-\.]{8,}[\"']?", r"\1[REDACTED]"),
    (r"(?i)(password\s*[:=]\s*)[\"']?[^\s\"']{6,}[\"']?", r"\1[REDACTED]"),
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]"),
]


def _compile(custom_patterns: list[str] | None = None) -> list[tuple[Pattern[str], str]]:
    compiled: list[tuple[Pattern[str], str]] = []
    for pattern, replacement in BASE_PATTERNS:
        compiled.append((re.compile(pattern), replacement))
    for pattern in custom_patterns or []:
        try:
            compiled.append((re.compile(pattern), "[REDACTED_CUSTOM]"))
        except re.error:
            continue
    return compiled


def redact_text(text: str, mode: str = "strict", custom_patterns: list[str] | None = None) -> str:
    """Redact sensitive strings from text based on mode."""
    if mode == "open":
        return text

    redacted = text
    compiled = _compile(custom_patterns)

    if mode == "balanced":
        compiled = compiled[:4]

    for regex, replacement in compiled:
        redacted = regex.sub(replacement, redacted)

    return redacted
