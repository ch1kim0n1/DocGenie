from __future__ import annotations

from typing import Any

class Markdown:
    toc: str

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def convert(self, source: str) -> str: ...
