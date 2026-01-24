from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

class TomlDecodeError(ValueError): ...

def load(f: str | Path) -> dict[str, Any]: ...
