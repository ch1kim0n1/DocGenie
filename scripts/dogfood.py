#!/usr/bin/env python3
"""
Dogfooding script: Run DocGenie on itself to generate its own documentation.
"""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from docgenie.core import CodebaseAnalyzer
from docgenie.generator import ReadmeGenerator
from docgenie.html_generator import HTMLGenerator
from docgenie.logging import configure_logging, get_logger


def main() -> int:
    """Run DocGenie on itself."""
    configure_logging(verbose=True)
    logger = get_logger(__name__)

    repo_root = Path(__file__).parent.parent
    logger.info("Dogfooding: Running DocGenie on itself", path=str(repo_root))

    # Analyze the DocGenie codebase
    analyzer = CodebaseAnalyzer(
        str(repo_root),
        ignore_patterns=[
            "*.egg-info",
            ".docgenie",
            "examples/*",
            "docs/*",
        ],
        enable_tree_sitter=False,  # Don't require tree-sitter
    )

    logger.info("Starting analysis...")
    analysis_data = analyzer.analyze()

    logger.info(
        "Analysis complete",
        files=analysis_data["files_analyzed"],
        languages=list(analysis_data["languages"].keys()),
        functions=len(analysis_data["functions"]),
        classes=len(analysis_data["classes"]),
    )

    # Generate README
    logger.info("Generating README.md...")
    readme_gen = ReadmeGenerator()
    readme_path = repo_root / "DOGFOOD_README.md"
    readme_gen.generate(analysis_data, str(readme_path))
    logger.info("README generated", path=str(readme_path))

    # Generate HTML
    logger.info("Generating HTML documentation...")
    html_gen = HTMLGenerator()
    html_path = repo_root / "DOGFOOD_DOCS.html"
    html_gen.generate_from_analysis(analysis_data, str(html_path))
    logger.info("HTML documentation generated", path=str(html_path))

    logger.info("Dogfooding complete! Check DOGFOOD_README.md and DOGFOOD_DOCS.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
