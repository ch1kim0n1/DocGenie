#!/usr/bin/env python3
"""Legacy shim to the Typer-based DocGenie CLI."""

import sys
from pathlib import Path

repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root / "src"))

from docgenie.cli import app


def main() -> None:
    app(args=["html", *sys.argv[1:]], prog_name="docgenie-html")


if __name__ == "__main__":
    main()
