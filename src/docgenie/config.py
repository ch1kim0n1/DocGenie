"""Configuration management for DocGenie."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(root_path: Path) -> dict[str, Any]:
    """
    Load configuration from .docgenie.yaml in the project root.
    Returns a default configuration if the file doesn't exist.
    """
    config_path = root_path / ".docgenie.yaml"
    if not config_path.exists():
        return get_default_config()

    try:
        with open(config_path, encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
            return merge_configs(get_default_config(), user_config)
    except (yaml.YAMLError, OSError):
        # Return default config if loading fails
        return get_default_config()


def get_default_config() -> dict[str, Any]:
    """Return the default configuration."""
    return {
        "ignore_patterns": [
            "*.log",
            "build/",
            "dist/",
            "*.egg-info",
            "__pycache__",
            ".git",
            ".idea",
            ".vscode",
            "node_modules",
            "venv",
            ".venv",
            "env",
        ],
        "template_customizations": {
            "include_api_docs": True,
            "include_directory_tree": True,
            "max_functions_documented": 10,
        },
    }


def merge_configs(default: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    """Deep merge user config into default config."""
    result = default.copy()
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    return result
