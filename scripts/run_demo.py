"""
Demo script: Run DocGenie on the examples/demo_library template project.

Generates README.md and docs.html inside examples/demo_library/ so you can
immediately see the documentation output produced by DocGenie.

Usage:
    python scripts/run_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure we import from the local src/ rather than any installed version
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from docgenie.core import CodebaseAnalyzer
from docgenie.generator import ReadmeGenerator
from docgenie.html_generator import HTMLGenerator
from docgenie.logging import configure_logging, get_logger


def main() -> int:
    configure_logging(verbose=True)
    logger = get_logger(__name__)

    demo_path = Path(__file__).parent.parent / "examples" / "demo_library"
    if not demo_path.exists():
        logger.error("Demo project not found", path=str(demo_path))
        return 1

    logger.info("Running DocGenie on demo_library", path=str(demo_path))

    # Analyze the demo project (tree-sitter disabled for reproducibility)
    analyzer = CodebaseAnalyzer(str(demo_path), enable_tree_sitter=False)
    analysis = analyzer.analyze()

    logger.info(
        "Analysis complete",
        files=analysis["files_analyzed"],
        functions=len(analysis["functions"]),
        classes=len(analysis["classes"]),
        languages=list(analysis["languages"].keys()),
        is_website=analysis["is_website"],
    )

    # Generate README.md
    readme_path = demo_path / "README.md"
    ReadmeGenerator().generate(analysis, str(readme_path))
    logger.info("README.md generated", path=str(readme_path))

    # Generate docs.html
    html_path = demo_path / "docs.html"
    HTMLGenerator().generate_from_analysis(analysis, str(html_path))
    logger.info("docs.html generated", path=str(html_path))

    print("\n" + "=" * 60)
    print("DocGenie demo complete!")
    print(f"  README : {readme_path}")
    print(f"  HTML   : {html_path}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
