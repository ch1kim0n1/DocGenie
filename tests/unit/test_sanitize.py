"""Tests for HTML sanitization."""

import pytest

from docgenie.sanitize import (
    sanitize_attribute,
    sanitize_css,
    sanitize_dict_values,
    sanitize_html,
    sanitize_url,
)


def test_sanitize_html_basic() -> None:
    """Test basic HTML escaping."""
    assert sanitize_html("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    assert sanitize_html("Normal text") == "Normal text"
    assert sanitize_html("A & B") == "A &amp; B"


def test_sanitize_html_quotes() -> None:
    """Test quote escaping."""
    assert sanitize_html('"quoted"') == "&quot;quoted&quot;"
    assert sanitize_html("'single'") == "&#x27;single&#x27;"


def test_sanitize_attribute() -> None:
    """Test attribute sanitization."""
    # Should remove quotes
    assert '"' not in sanitize_attribute('value"with"quotes')
    assert "'" not in sanitize_attribute("value'with'quotes")
    
    # Should escape special chars
    result = sanitize_attribute("normal-value")
    assert "normal-value" == result


def test_sanitize_url_safe() -> None:
    """Test that safe URLs pass through."""
    assert sanitize_url("https://example.com") == "https://example.com"
    assert sanitize_url("http://example.com/path") == "http://example.com/path"
    assert sanitize_url("mailto:test@example.com") == "mailto:test@example.com"
    assert sanitize_url("/relative/path") == "/relative/path"


def test_sanitize_url_dangerous() -> None:
    """Test that dangerous URLs are blocked."""
    assert sanitize_url("javascript:alert('xss')") == ""
    assert sanitize_url("data:text/html,<script>alert('xss')</script>") == ""
    assert sanitize_url("vbscript:msgbox('xss')") == ""
    assert sanitize_url("file:///etc/passwd") == ""


def test_sanitize_url_case_insensitive() -> None:
    """Test that protocol detection is case-insensitive."""
    assert sanitize_url("JavaScript:alert('xss')") == ""
    assert sanitize_url("JAVASCRIPT:alert('xss')") == ""
    assert sanitize_url("DaTa:text/html,evil") == ""


def test_sanitize_css() -> None:
    """Test CSS sanitization."""
    # Should remove dangerous patterns
    assert "javascript:" not in sanitize_css("background: url(javascript:alert('xss'))")
    assert "expression(" not in sanitize_css("width: expression(alert('xss'))")
    assert "import" not in sanitize_css("@import url(evil.css)")
    
    # Safe CSS should pass through
    safe_css = "color: red; font-size: 14px;"
    assert "color: red" in sanitize_css(safe_css)


def test_sanitize_dict_values_strings() -> None:
    """Test sanitizing strings in dictionaries."""
    data = {
        "name": "<script>alert('xss')</script>",
        "description": "Safe & normal text",
    }
    
    sanitized = sanitize_dict_values(data)
    
    assert "&lt;script&gt;" in sanitized["name"]
    assert "<script>" not in sanitized["name"]
    assert "Safe &amp; normal text" == sanitized["description"]


def test_sanitize_dict_values_nested() -> None:
    """Test sanitizing nested dictionaries."""
    data = {
        "outer": {
            "inner": "<script>xss</script>",
            "safe": "normal",
        }
    }
    
    sanitized = sanitize_dict_values(data)
    
    assert "&lt;script&gt;" in sanitized["outer"]["inner"]
    assert sanitized["outer"]["safe"] == "normal"


def test_sanitize_dict_values_lists() -> None:
    """Test sanitizing lists in dictionaries."""
    data = {
        "items": ["<b>item1</b>", "<i>item2</i>", "safe"],
    }
    
    sanitized = sanitize_dict_values(data)
    
    assert "&lt;b&gt;item1&lt;/b&gt;" == sanitized["items"][0]
    assert "&lt;i&gt;item2&lt;/i&gt;" == sanitized["items"][1]
    assert "safe" == sanitized["items"][2]


def test_sanitize_dict_values_preserves_types() -> None:
    """Test that non-string types are preserved."""
    data = {
        "number": 42,
        "boolean": True,
        "null": None,
        "list": [1, 2, 3],
    }
    
    sanitized = sanitize_dict_values(data)
    
    assert sanitized["number"] == 42
    assert sanitized["boolean"] is True
    assert sanitized["null"] is None
    assert sanitized["list"] == [1, 2, 3]


def test_sanitize_html_empty_string() -> None:
    """Test sanitizing empty string."""
    assert sanitize_html("") == ""


def test_sanitize_url_empty_string() -> None:
    """Test sanitizing empty URL."""
    assert sanitize_url("") == ""


def test_sanitize_url_whitespace() -> None:
    """Test URL with whitespace."""
    assert sanitize_url("  https://example.com  ") == "https://example.com"
