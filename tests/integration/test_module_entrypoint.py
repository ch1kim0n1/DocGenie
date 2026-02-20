import sys

import pytest

from docgenie.__main__ import main


def test_python_module_entrypoint_help(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["docgenie", "--help"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


def test_python_module_analyze_command(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.TempPathFactory
) -> None:
    """python -m docgenie analyze <dir> --format text should exit 0."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "sample.py").write_text("def hello(): pass\n", encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["docgenie", "analyze", tmpdir, "--format", "text"])
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 0


def test_python_module_invalid_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unrecognised command should produce a non-zero exit code."""
    monkeypatch.setattr(sys, "argv", ["docgenie", "nonexistent-command-xyz"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code != 0

