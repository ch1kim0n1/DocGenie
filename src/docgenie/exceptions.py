"""Custom exception hierarchy for DocGenie."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class DocGenieError(Exception):
    """Base exception for all DocGenie errors."""

    def __init__(self, message: str, path: Optional[Path] = None) -> None:
        self.message = message
        self.path = path
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.path:
            return f"{self.message} (path: {self.path})"
        return self.message


class ParserError(DocGenieError):
    """Raised when a parser fails to parse a file."""

    def __init__(self, message: str, path: Path, language: str) -> None:
        self.language = language
        super().__init__(message, path)

    def _format_message(self) -> str:
        return f"Failed to parse {self.language} file: {self.message} (path: {self.path})"


class CacheError(DocGenieError):
    """Raised when cache operations fail."""

    pass


class ConfigError(DocGenieError):
    """Raised when configuration is invalid."""

    pass


class DependencyError(DocGenieError):
    """Raised when a required dependency is missing."""

    def __init__(self, dependency: str, extra: Optional[str] = None) -> None:
        self.dependency = dependency
        self.extra = extra
        message = f"Missing required dependency: {dependency}"
        if extra:
            message += f" (install with: pip install docgenie[{extra}])"
        super().__init__(message)


class FileAccessError(DocGenieError):
    """Raised when file access fails."""

    pass


class GeneratorError(DocGenieError):
    """Raised when documentation generation fails."""

    pass
