"""Shared pytest fixtures for DocGenie test suite."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest


@pytest.fixture()
def minimal_analysis() -> dict:
    """Bare-minimum analysis dict that satisfies all generator/html_generator fields."""
    return {
        "project_name": "TestProject",
        "files_analyzed": 0,
        "languages": {},
        "main_language": "N/A",
        "dependencies": {},
        "project_structure": {"root": {"files": [], "dirs": []}},
        "functions": [],
        "classes": [],
        "imports": {},
        "documentation_files": [],
        "config_files": [],
        "git_info": {},
        "is_website": False,
        "website_detection_reason": "",
        "root_path": "test",
        "config": {},
    }


@pytest.fixture()
def rich_analysis() -> dict:
    """Full-featured analysis dict: functions (incl. async), classes, git info, multi-language."""
    return {
        "project_name": "RichProject",
        "files_analyzed": 12,
        "languages": {"python": 8, "javascript": 3, "typescript": 1},
        "main_language": "python",
        "dependencies": {
            "requirements.txt": ["requests", "click", "fastapi"],
            "package.json": {"dependencies": ["react"], "devDependencies": ["jest"]},
        },
        "project_structure": {
            "root": {
                "files": ["README.md", "main.py", "requirements.txt"],
                "dirs": ["src", "tests"],
            },
            "src": {"files": ["app.py", "utils.py", "client.py"], "dirs": []},
            "tests": {"files": ["test_app.py"], "dirs": []},
        },
        "functions": [
            {
                "name": "main",
                "line": 5,
                "docstring": "Entry point.",
                "args": [],
                "decorators": [],
                "file": "main.py",
                "is_async": False,
            },
            {
                "name": "helper",
                "line": 20,
                "docstring": None,
                "args": ["x", "y"],
                "decorators": [],
                "file": "utils.py",
                "is_async": False,
            },
            {
                "name": "fetch_data",
                "line": 30,
                "docstring": "Fetch remote data.",
                "args": ["url"],
                "decorators": [],
                "file": "client.py",
                "is_async": True,
            },
        ],
        "classes": [
            {
                "name": "App",
                "line": 10,
                "docstring": "Application class.",
                "bases": [],
                "decorators": [],
                "methods": [],
                "file": "app.py",
            },
            {
                "name": "_Internal",
                "line": 50,
                "docstring": None,
                "bases": ["Base"],
                "decorators": [],
                "methods": [],
                "file": "app.py",
            },
        ],
        "imports": {"python": ["os", "sys", "pathlib.Path"]},
        "documentation_files": ["README.md"],
        "config_files": [".docgenie.yaml"],
        "git_info": {
            "remote_url": "https://github.com/user/richproject",
            "repo_name": "user/richproject",
            "current_branch": "main",
            "contributor_count": 3,
            "latest_commit": {
                "hash": "abc123",
                "author_name": "Dev",
                "author_email": "dev@example.com",
                "date": "2026-01-01",
                "message": "Initial commit",
            },
        },
        "is_website": False,
        "website_detection_reason": "",
        "root_path": "richproject",
        "config": {
            "template_customizations": {
                "include_api_docs": True,
                "include_directory_tree": True,
                "max_functions_documented": 25,
            }
        },
    }


@pytest.fixture()
def website_analysis() -> dict:
    """Analysis dict representing a website/web application project."""
    return {
        "project_name": "MySite",
        "files_analyzed": 5,
        "languages": {"html": 3, "css": 1, "javascript": 1},
        "main_language": "html",
        "dependencies": {},
        "project_structure": {
            "root": {
                "files": ["index.html", "style.css", "script.js"],
                "dirs": ["assets"],
            },
            "assets": {"files": ["logo.png"], "dirs": []},
        },
        "functions": [],
        "classes": [],
        "imports": {},
        "documentation_files": [],
        "config_files": [],
        "git_info": {},
        "is_website": True,
        "website_detection_reason": "HTML entry point detected",
        "root_path": "mysite",
        "config": {},
    }


@pytest.fixture()
def py_source_file(tmp_path: Path) -> Path:
    """Write a moderately complex Python source file and return its path."""
    src = tmp_path / "sample.py"
    src.write_text(
        textwrap.dedent(
            """
            import os
            import sys
            from pathlib import Path

            CONSTANT = 42

            def simple_func(x: int) -> int:
                \"\"\"Add one to x.\"\"\"
                return x + 1

            async def async_fetch(url: str) -> str:
                \"\"\"Fetch URL asynchronously.\"\"\"
                return url

            class MyClass:
                \"\"\"A sample class.\"\"\"

                def __init__(self) -> None:
                    self.value = 0

                @staticmethod
                def static_method() -> None:
                    pass

                @classmethod
                def from_string(cls, s: str) -> "MyClass":
                    obj = cls()
                    return obj

                async def async_method(self) -> None:
                    pass
            """
        ).strip(),
        encoding="utf-8",
    )
    return src


@pytest.fixture()
def js_source_file(tmp_path: Path) -> Path:
    """Write a JavaScript source file and return its path."""
    src = tmp_path / "app.js"
    src.write_text(
        textwrap.dedent(
            """
            import React from 'react';
            const helper = require('./utils');

            function App() {
                return null;
            }

            const ArrowFunc = (x) => x + 1;

            class Component {
                render() { return null; }
            }

            export default App;
            """
        ).strip(),
        encoding="utf-8",
    )
    return src


@pytest.fixture()
def rust_source_file(tmp_path: Path) -> Path:
    """Write a Rust source file and return its path."""
    src = tmp_path / "main.rs"
    src.write_text(
        textwrap.dedent(
            """
            use std::io;

            struct Point { x: f64, y: f64 }

            enum Direction { North, South, East, West }

            fn add(a: i32, b: i32) -> i32 { a + b }

            fn main() { println!("hello"); }
            """
        ).strip(),
        encoding="utf-8",
    )
    return src


@pytest.fixture()
def go_source_file(tmp_path: Path) -> Path:
    """Write a Go source file and return its path."""
    src = tmp_path / "main.go"
    src.write_text(
        textwrap.dedent(
            """
            package main

            import "fmt"

            type Server struct {
                Port int
            }

            func NewServer(port int) *Server {
                return &Server{Port: port}
            }

            func (s *Server) Start() {
                fmt.Println(s.Port)
            }

            func main() {
                s := NewServer(8080)
                s.Start()
            }
            """
        ).strip(),
        encoding="utf-8",
    )
    return src
