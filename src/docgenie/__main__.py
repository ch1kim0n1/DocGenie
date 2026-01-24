"""Module entry point for `python -m docgenie`."""

from __future__ import annotations

from .cli import app


def main() -> None:
    app(prog_name="docgenie")


if __name__ == "__main__":
    main()
