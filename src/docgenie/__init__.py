"""
DocGenie - Auto-documentation tool for codebases

A powerful Python library that automatically generates comprehensive README documentation
for any codebase by analyzing source code, dependencies, and project structure.
"""

__version__ = "1.1.0"
__author__ = "DocGenie Team"
__email__ = "contact@docgenie.dev"

from .core import CodebaseAnalyzer
from .generator import ReadmeGenerator

__all__ = ["CodebaseAnalyzer", "ReadmeGenerator"]