"""
DocGenie - Auto-documentation tool for codebases

A powerful Python library that automatically generates comprehensive README documentation
for any codebase by analyzing source code, dependencies, and project structure.
"""

__version__ = "1.1.6"
__author__ = "ch1kim0n1"
__email__ = "vxk230059@utdallas.edu"

from .core import CodebaseAnalyzer
from .generator import ReadmeGenerator

__all__ = ["CodebaseAnalyzer", "ReadmeGenerator"]
