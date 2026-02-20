"""Text formatting utilities with decorator and class hierarchy examples."""

from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable[..., str])


def uppercase_result(func: F) -> F:
    """Decorator that converts the return value of *func* to uppercase.

    Args:
        func: A callable that returns a string.

    Returns:
        A wrapped callable whose return value is uppercased.
    """

    @wraps(func)
    def wrapper(*args: object, **kwargs: object) -> str:
        return func(*args, **kwargs).upper()

    return wrapper  # type: ignore[return-value]


def slugify(text: str) -> str:
    """Convert *text* to a URL-friendly slug.

    Replaces whitespace with hyphens and converts to lowercase.

    Args:
        text: Input text to slugify.

    Returns:
        A lowercase, hyphen-separated slug string.
    """
    return "-".join(text.lower().split())


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate *text* to at most *max_length* characters.

    If truncation occurs, *suffix* is appended.

    Args:
        text: The string to truncate.
        max_length: Maximum number of characters (including suffix).
        suffix: String appended when truncation occurs.

    Returns:
        Possibly-truncated string.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


class TextFormatter:
    """Formats text with configurable prefix, suffix, and transformation rules.

    Args:
        prefix: String prepended to all formatted text.
        suffix: String appended to all formatted text.
    """

    def __init__(self, prefix: str = "", suffix: str = "") -> None:
        self.prefix = prefix
        self.suffix = suffix

    def format(self, text: str) -> str:
        """Format *text* by wrapping it with :attr:`prefix` and :attr:`suffix`.

        Args:
            text: The content to format.

        Returns:
            Formatted string.
        """
        return f"{self.prefix}{text}{self.suffix}"

    @uppercase_result
    def format_upper(self, text: str) -> str:
        """Format *text* and convert the result to uppercase.

        Args:
            text: The content to format.

        Returns:
            Uppercased formatted string.
        """
        return self.format(text)

    @staticmethod
    def word_count(text: str) -> int:
        """Count the number of whitespace-separated words in *text*.

        Args:
            text: Input string.

        Returns:
            Number of words.
        """
        return len(text.split())

    @classmethod
    def bold(cls) -> "TextFormatter":
        """Create a formatter that wraps text in Markdown bold markers.

        Returns:
            A :class:`TextFormatter` with ``**`` prefix and suffix.
        """
        return cls(prefix="**", suffix="**")

    @classmethod
    def italic(cls) -> "TextFormatter":
        """Create a formatter that wraps text in Markdown italic markers.

        Returns:
            A :class:`TextFormatter` with ``_`` prefix and suffix.
        """
        return cls(prefix="_", suffix="_")

    @classmethod
    def code(cls) -> "TextFormatter":
        """Create a formatter that wraps text in Markdown inline-code markers.

        Returns:
            A :class:`TextFormatter` with `` ` `` prefix and suffix.
        """
        return cls(prefix="`", suffix="`")


class MarkdownFormatter(TextFormatter):
    """Extended formatter with Markdown-specific helpers.

    Inherits from :class:`TextFormatter` and adds heading and link generation.
    """

    def heading(self, text: str, level: int = 1) -> str:
        """Generate a Markdown heading.

        Args:
            text: Heading content.
            level: Heading level (1–6).

        Returns:
            Markdown heading string.
        """
        level = max(1, min(6, level))
        return f"{'#' * level} {text}"

    def link(self, label: str, url: str) -> str:
        """Generate a Markdown hyperlink.

        Args:
            label: Link display text.
            url: The target URL.

        Returns:
            Markdown link string ``[label](url)``.
        """
        return f"[{label}]({url})"
