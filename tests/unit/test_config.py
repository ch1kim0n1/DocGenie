"""Tests for DocGenie configuration loading and merging."""

from pathlib import Path

from docgenie.config import get_default_config, load_config, merge_configs


def test_get_default_config_shape() -> None:
    config = get_default_config()

    assert "ignore_patterns" in config
    assert isinstance(config["ignore_patterns"], list)

    assert "template_customizations" in config
    assert isinstance(config["template_customizations"], dict)
    assert "max_functions_documented" in config["template_customizations"]


def test_merge_configs_deep_merge_overrides_nested_values() -> None:
    default = {
        "ignore_patterns": ["*.log"],
        "template_customizations": {"include_api_docs": True, "max_functions_documented": 10},
    }
    user = {"template_customizations": {"include_api_docs": False}}

    merged = merge_configs(default, user)

    assert merged["template_customizations"]["include_api_docs"] is False
    # Unspecified nested values should remain from default
    assert merged["template_customizations"]["max_functions_documented"] == 10
    # Unrelated keys should remain intact
    assert merged["ignore_patterns"] == ["*.log"]


def test_load_config_missing_file_returns_default(tmp_path: Path) -> None:
    assert load_config(tmp_path) == get_default_config()


def test_load_config_empty_yaml_returns_default(tmp_path: Path) -> None:
    (tmp_path / ".docgenie.yaml").write_text("", encoding="utf-8")
    assert load_config(tmp_path) == get_default_config()


def test_load_config_valid_yaml_merges_with_defaults(tmp_path: Path) -> None:
    (tmp_path / ".docgenie.yaml").write_text(
        "\n".join(
            [
                "ignore_patterns:",
                "  - \"*.tmp\"",
                "template_customizations:",
                "  max_functions_documented: 25",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    config = load_config(tmp_path)
    assert config["ignore_patterns"] == ["*.tmp"]
    assert config["template_customizations"]["max_functions_documented"] == 25
    # Values not specified by user should remain from defaults
    assert "include_api_docs" in config["template_customizations"]


def test_load_config_invalid_yaml_falls_back_to_default(tmp_path: Path) -> None:
    (tmp_path / ".docgenie.yaml").write_text("ignore_patterns: [\n", encoding="utf-8")
    assert load_config(tmp_path) == get_default_config()

