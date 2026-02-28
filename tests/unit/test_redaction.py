from docgenie.redaction import redact_text


def test_redaction_modes() -> None:
    sample = "api_key=abcdef1234567890 email=test@example.com"
    assert "[REDACTED]" in redact_text(sample, "strict")
    assert "[REDACTED_EMAIL]" in redact_text(sample, "strict")
    assert redact_text(sample, "open") == sample
    balanced = redact_text(sample, "balanced")
    assert "[REDACTED]" in balanced


def test_redaction_custom_pattern() -> None:
    sample = "internal-id: ZXCV-9999"
    out = redact_text(sample, "strict", [r"ZXCV-\d+"])
    assert "[REDACTED_CUSTOM]" in out
