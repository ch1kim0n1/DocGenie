# Core API Reference

This page documents the core analysis functionality of DocGenie.

## CodebaseAnalyzer

::: docgenie.core.CodebaseAnalyzer
    options:
      show_source: true
      heading_level: 3

## CacheManager

::: docgenie.core.CacheManager
    options:
      show_source: true
      heading_level: 3

## Usage Example

```python
from docgenie.core import CodebaseAnalyzer

# Create analyzer
analyzer = CodebaseAnalyzer(
    root_path="/path/to/project",
    ignore_patterns=["*.log", "temp/"],
    enable_tree_sitter=True
)

# Perform analysis
results = analyzer.analyze()

# Access results
print(f"Files analyzed: {results['files_analyzed']}")
print(f"Languages found: {results['languages']}")
print(f"Functions: {len(results['functions'])}")
print(f"Classes: {len(results['classes'])}")
```

## Analysis Result Structure

The `analyze()` method returns a dictionary with the following structure:

```python
{
    "project_name": str,           # Project name
    "files_analyzed": int,         # Number of files processed
    "languages": Dict[str, int],   # Language: file count mapping
    "main_language": str,          # Primary language
    "dependencies": Dict,          # Detected dependencies
    "project_structure": Dict,     # Directory tree
    "functions": List[Dict],       # All functions found
    "classes": List[Dict],         # All classes found
    "imports": Dict[str, List],    # Imports by language
    "git_info": Dict,             # Git repository info
    "is_website": bool,           # Website detection
}
```
