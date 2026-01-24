import sys

import pytest

from docgenie.__main__ import main


def test_python_module_entrypoint_help(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["docgenie", "--help"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0

