from docgenie.redaction import redact_text


def test_redaction_modes() -> None:
    sample = "api_key=abcdef1234567890 email=test@example.com"
    # Secrets are redacted in strict mode...
    assert "[REDACTED]" in redact_text(sample, "strict")
    # ...but ordinary contact emails are preserved by default (issue #43).
    assert "test@example.com" in redact_text(sample, "strict")
    assert "[REDACTED_EMAIL]" not in redact_text(sample, "strict")
    assert redact_text(sample, "open") == sample
    balanced = redact_text(sample, "balanced")
    assert "[REDACTED]" in balanced
    assert "test@example.com" in balanced


def test_paranoid_mode_redacts_emails() -> None:
    sample = "Contact: jane@example.com"
    assert "[REDACTED_EMAIL]" in redact_text(sample, "paranoid")
    # Opt-in email redaction in strict mode.
    assert "[REDACTED_EMAIL]" in redact_text(sample, "strict", redact_emails=True)


def test_default_preserves_email_but_redacts_secret() -> None:
    sample = "maintainer jane@example.com password=supersecret123"
    out = redact_text(sample, "strict")
    assert "jane@example.com" in out
    assert "[REDACTED]" in out
    assert "supersecret123" not in out


def test_redaction_custom_pattern() -> None:
    sample = "internal-id: ZXCV-9999"
    out = redact_text(sample, "strict", [r"ZXCV-\d+"])
    assert "[REDACTED_CUSTOM]" in out
