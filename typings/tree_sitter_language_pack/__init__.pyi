from __future__ import annotations

from typing import Any, Protocol

class _Node(Protocol):
    start_byte: int
    end_byte: int
    start_point: tuple[int, int]
    type: str

    def child_by_field_name(self, name: str) -> _Node | None: ...
    def walk(self) -> _Cursor: ...

class _Cursor(Protocol):
    node: _Node

    def goto_first_child(self) -> bool: ...
    def goto_next_sibling(self) -> bool: ...
    def goto_parent(self) -> bool: ...

class _Tree(Protocol):
    root_node: _Node

class _Parser(Protocol):
    def parse(self, source: bytes) -> _Tree: ...

def get_parser(language: str) -> _Parser: ...
