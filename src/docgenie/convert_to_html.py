"""`docgenie-html` console-script entrypoint.

This provides backwards-compatible access to the `docgenie html ...` subcommand.
"""

from __future__ import annotations

import sys

from .cli import app


def main() -> None:
    # Forward all args to the Typer subcommand.
    app(args=["html", *sys.argv[1:]], prog_name="docgenie-html")


if __name__ == "__main__":
    main()
