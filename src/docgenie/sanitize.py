"""HTML sanitization utilities for security."""

from __future__ import annotations

import html
import re
from typing import Any

import nh3

# Tags allowed in rendered documentation bodies. This is the markdown output
# surface (headings, lists, tables, code blocks, links, images, etc.). Raw
# <script>/<style>/<iframe>/event-handler attributes are NOT in this set and are
# therefore stripped by nh3.
_ALLOWED_TAGS: set[str] = {
    "a",
    "abbr",
    "b",
    "blockquote",
    "br",
    "caption",
    "cite",
    "code",
    "col",
    "colgroup",
    "dd",
    "del",
    "details",
    "div",
    "dl",
    "dt",
    "em",
    "figcaption",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "img",
    "ins",
    "kbd",
    "li",
    "mark",
    "ol",
    "p",
    "pre",
    "q",
    "s",
    "samp",
    "small",
    "span",
    "strong",
    "sub",
    "summary",
    "sup",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
    "var",
}

_ALLOWED_ATTRIBUTES: dict[str, set[str]] = {
    "a": {"href", "title", "id", "name"},
    "img": {"src", "alt", "title", "width", "height"},
    "code": {"class"},
    "pre": {"class"},
    "span": {"class", "id"},
    "div": {"class", "id"},
    "td": {"align"},
    "th": {"align", "scope"},
    "ol": {"start"},
    "h1": {"id"},
    "h2": {"id"},
    "h3": {"id"},
    "h4": {"id"},
    "h5": {"id"},
    "h6": {"id"},
}

# Only safe link/image protocols survive sanitization; javascript:/data:/vbscript:
# URLs are dropped by nh3 because they are not in this allow-list.
_ALLOWED_URL_SCHEMES: set[str] = {"http", "https", "mailto", "tel", "ftp"}


def sanitize_markdown_html(html_body: str) -> str:
    """
    Sanitize HTML produced from markdown using an allow-list cleaner.

    Removes executable/dangerous content (``<script>``, event handlers,
    ``javascript:``/``data:`` URLs, etc.) while preserving normal documentation
    markup. Used on the rendered README body before inlining it into the
    generated HTML document to prevent stored XSS from analyzed source content.

    Args:
        html_body: HTML produced by the markdown converter.

    Returns:
        Sanitized HTML safe to inline into a document body.
    """
    return nh3.clean(
        html_body,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        url_schemes=_ALLOWED_URL_SCHEMES,
        link_rel="nofollow noopener noreferrer",
    )


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
    result: dict[str, Any] = {}

    for key, value in data.items():
        if isinstance(value, str):
            result[key] = sanitize_html(value)
        elif isinstance(value, dict):
            result[key] = sanitize_dict_values(value)
        elif isinstance(value, list):
            result[key] = [sanitize_html(item) if isinstance(item, str) else item for item in value]
        else:
            result[key] = value

    return result
