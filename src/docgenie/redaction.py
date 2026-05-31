"""Redaction helpers for generated documentation content."""

from __future__ import annotations

import re
from re import Pattern

# Secret patterns: always applied in balanced/strict/paranoid modes.
SECRET_PATTERNS = [
    (
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?"
        r"-----END [A-Z ]*PRIVATE KEY-----",
        "[REDACTED_PRIVATE_KEY]",
    ),
    (r"(?i)(api[_-]?key\s*[:=]\s*)[\"']?[A-Za-z0-9_\-]{12,}[\"']?", r"\1[REDACTED]"),
    (r"(?i)(token\s*[:=]\s*)[\"']?[A-Za-z0-9_\-\.]{12,}[\"']?", r"\1[REDACTED]"),
    (r"(?i)(secret\s*[:=]\s*)[\"']?[A-Za-z0-9_\-\.]{8,}[\"']?", r"\1[REDACTED]"),
    (r"(?i)(password\s*[:=]\s*)[\"']?[^\s\"']{6,}[\"']?", r"\1[REDACTED]"),
]

# Email redaction is intentionally NOT part of the default secret set: emails are
# usually intended contact info (maintainer address, latest-commit author). It is
# only applied in ``paranoid`` mode or when ``redact_emails=True`` is passed.
EMAIL_PATTERN = (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]")

# Backwards-compatible alias (previously included the email pattern).
BASE_PATTERNS = SECRET_PATTERNS


def _compile(
    custom_patterns: list[str] | None = None,
    *,
    include_email: bool = False,
) -> list[tuple[Pattern[str], str]]:
    compiled: list[tuple[Pattern[str], str]] = []
    for pattern, replacement in SECRET_PATTERNS:
        compiled.append((re.compile(pattern), replacement))
    if include_email:
        compiled.append((re.compile(EMAIL_PATTERN[0]), EMAIL_PATTERN[1]))
    for pattern in custom_patterns or []:
        try:
            compiled.append((re.compile(pattern), "[REDACTED_CUSTOM]"))
        except re.error:
            continue
    return compiled


def redact_text(
    text: str,
    mode: str = "strict",
    custom_patterns: list[str] | None = None,
    *,
    redact_emails: bool | None = None,
) -> str:
    """Redact sensitive strings from text based on mode.

    Modes:
        - ``open``: no redaction.
        - ``balanced``: redact only key/token/secret/password secrets.
        - ``strict`` (default): redact all secret patterns, but preserve emails.
        - ``paranoid``: also redact email addresses.

    ``redact_emails`` overrides the mode default when set explicitly.
    """
    if mode == "open":
        return text

    include_email = mode == "paranoid" if redact_emails is None else bool(redact_emails)

    if mode == "balanced":
        # Balanced covers a subset of secret patterns; never emails.
        compiled = _compile(custom_patterns, include_email=False)
        secret_count = len(SECRET_PATTERNS)
        compiled = compiled[:4] + compiled[secret_count:]
    else:
        compiled = _compile(custom_patterns, include_email=include_email)

    redacted = text
    for regex, replacement in compiled:
        redacted = regex.sub(replacement, redacted)

    return redacted
