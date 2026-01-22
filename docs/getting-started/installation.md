# Installation

## Requirements

- Python 3.9 or higher
- pip package manager

## Basic Installation

Install DocGenie using pip:

```bash
pip install docgenie
```

This installs the core functionality with essential dependencies.

## Full Installation (Recommended)

For the best experience with enhanced parsing capabilities:

```bash
pip install docgenie[full]
```

This includes:

- **tree-sitter**: Advanced syntax-aware parsing for multiple languages
- Better accuracy for JavaScript, TypeScript, Java, C++, Go, and Rust
- Improved handling of complex code structures

## Development Installation

If you want to contribute to DocGenie:

```bash
git clone https://github.com/docgenie/docgenie.git
cd docgenie
pip install -e ".[dev]"
```

This installs DocGenie in editable mode with all development dependencies:

- pytest (testing)
- ruff (linting/formatting)
- mypy (type checking)
- bandit (security scanning)
- pre-commit (git hooks)

## Verify Installation

Test that DocGenie is installed correctly:

```bash
docgenie --help
```

You should see the help message with available commands.

## Platform-Specific Notes

### macOS

No special requirements. Use pip as shown above.

### Linux

You may need to install Python development headers:

```bash
# Debian/Ubuntu
sudo apt-get install python3-dev

# Fedora/RHEL
sudo dnf install python3-devel
```

### Windows

DocGenie works on Windows with Python 3.9+. Use pip in PowerShell or Command Prompt.

## Troubleshooting

### Permission Errors

If you get permission errors, use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install docgenie[full]
```

### tree-sitter Installation Issues

If tree-sitter installation fails, you can still use DocGenie without it:

```bash
pip install docgenie  # Without [full]
docgenie /path/to/project --no-tree-sitter
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Generate your first documentation
- [Configuration](configuration.md) - Customize DocGenie behavior
