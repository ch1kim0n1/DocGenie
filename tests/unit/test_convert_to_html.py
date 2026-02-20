"""Tests for docgenie.convert_to_html — docgenie-html console script."""

from __future__ import annotations

import sys

import pytest

from docgenie.convert_to_html import main


def test_main_help_exits_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """docgenie-html --help should exit with code 0."""
    monkeypatch.setattr(sys, "argv", ["docgenie-html", "--help"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


def test_main_invalid_subcommand_exits_nonzero(monkeypatch: pytest.MonkeyPatch) -> None:
    """An invalid source value should cause a non-zero exit."""
    monkeypatch.setattr(sys, "argv", ["docgenie-html", "--source", "invalid-value"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code != 0
