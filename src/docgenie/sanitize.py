"""HTML sanitization utilities for security."""

from __future__ import annotations

import html
import re
from typing import Any


def sanitize_html(text: str) -> str:
    """
    Escape HTML special characters to prevent XSS attacks.

    Args:
        text: Input text that may contain HTML

    Returns:
        HTML-safe string with special characters escaped
    """
    return html.escape(text, quote=True)


def sanitize_attribute(value: str) -> str:
    """
    Sanitize value for use in HTML attributes.

    Removes potentially dangerous characters and escapes the rest.

    Args:
        value: Attribute value

    Returns:
        Sanitized attribute value
    """
    # Remove any quotes and control characters
    value = re.sub(r'["\'\x00-\x1f\x7f]', "", value)
    return html.escape(value, quote=True)


def sanitize_url(url: str) -> str:
    """
    Sanitize URL to prevent javascript: and data: URLs.

    Args:
        url: URL to sanitize

    Returns:
        Safe URL or empty string if dangerous
    """
    url = url.strip()
    
    # Block dangerous protocols
    dangerous_protocols = ["javascript:", "data:", "vbscript:", "file:"]
    url_lower = url.lower()
    
    for protocol in dangerous_protocols:
        if url_lower.startswith(protocol):
            return ""
    
    return url


def sanitize_css(css: str) -> str:
    """
    Basic CSS sanitization to prevent CSS injection.

    Args:
        css: CSS code

    Returns:
        Sanitized CSS
    """
    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r"javascript:",
        r"expression\(",
        r"import\s+",
        r"@import",
        r"behavior:",
        r"binding:",
    ]
    
    for pattern in dangerous_patterns:
        css = re.sub(pattern, "", css, flags=re.IGNORECASE)
    
    return css


def sanitize_dict_values(data: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively sanitize all string values in a dictionary.

    Args:
        data: Dictionary with potentially unsafe strings

    Returns:
        Dictionary with sanitized string values
    """
    result = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = sanitize_html(value)
        elif isinstance(value, dict):
            result[key] = sanitize_dict_values(value)
        elif isinstance(value, list):
            result[key] = [
                sanitize_html(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            result[key] = value
    
    return result
