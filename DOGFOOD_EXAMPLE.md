# DocGenie - Self-Generated Documentation Example

*This file demonstrates DocGenie's capabilities by showing what it would generate for its own codebase.*

## Project Overview

DocGenie is a production-grade Python tool that automatically generates comprehensive documentation for any codebase. It analyzes source code, dependencies, and project structure to produce beautiful README files and HTML documentation.

## Features

- 🚀 **Multi-Language Support**: Python, JavaScript, TypeScript, Java, C++, Go, Rust
- 🎨 **Multiple Output Formats**: Markdown and HTML
- 🧩 **Plugin Architecture**: Extensible parser system with tree-sitter support
- ⚡ **High Performance**: Parallel processing with intelligent caching
- 🔒 **Security First**: XSS protection, security scanning, dependency updates
- 📊 **Rich CLI**: Beautiful terminal output with Typer and Rich
- 🐍 **Python API**: Programmatic usage for integration
- 🧪 **Well Tested**: 90%+ code coverage
- 📝 **Fully Typed**: mypy strict mode compliant

## Requirements

- Python 3.9 or higher
- pip

## Installation

### Basic Installation

```bash
pip install docgenie
```

### Full Installation (with tree-sitter)

```bash
pip install docgenie[full]
```

### Development Installation

```bash
git clone https://github.com/docgenie/docgenie.git
cd docgenie
pip install -e ".[dev]"
```

## Usage

### Command Line

```bash
# Generate README for current directory
docgenie .

# Generate both README and HTML
docgenie /path/to/project --format both

# Preview without saving
docgenie . --preview

# Verbose output with JSON logs
docgenie . --verbose --json-logs
```

### Python API

```python
from docgenie.core import CodebaseAnalyzer
from docgenie.generator import ReadmeGenerator
from docgenie.html_generator import HTMLGenerator

# Analyze codebase
analyzer = CodebaseAnalyzer("/path/to/project", enable_tree_sitter=True)
results = analyzer.analyze()

# Generate README
readme_gen = ReadmeGenerator()
readme_gen.generate(results, "README.md")

# Generate HTML
html_gen = HTMLGenerator()
html_gen.generate_from_analysis(results, "docs.html")
```

## Project Structure

```
DocGenie/
├── src/docgenie/           # Main package
│   ├── __init__.py         # Package initialization
│   ├── cli.py              # Typer-based CLI
│   ├── core.py             # Core analysis engine
│   ├── parsers.py          # Multi-language parsers
│   ├── models.py           # Data models
│   ├── generator.py        # README generator
│   ├── html_generator.py   # HTML generator
│   ├── utils.py            # Utility functions
│   ├── exceptions.py       # Custom exceptions
│   ├── logging.py          # Structured logging
│   └── sanitize.py         # Security utilities
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── docs/                   # MkDocs documentation
├── scripts/               # Utility scripts
├── .github/               # CI/CD workflows
├── pyproject.toml         # Project configuration
└── mkdocs.yml             # Documentation config
```

## Architecture

### Core Components

#### CodebaseAnalyzer
Multi-threaded analysis engine with caching support. Walks the project tree, delegates to language-specific parsers, and compiles comprehensive results.

#### ParserRegistry
Plugin-based parser system supporting:
- **PythonAstParser**: Native AST parsing (priority 0)
- **TreeSitterParser**: Optional tree-sitter support (priority 50)
- **RegexParser**: Fallback for unsupported languages (priority 500)

#### Generators
- **ReadmeGenerator**: Jinja2-based Markdown generation
- **HTMLGenerator**: Beautiful responsive HTML with Prism.js highlighting

### Security Features

- XSS protection via HTML sanitization
- Bandit security scanning in CI
- Dependabot for dependency updates
- Input validation and safe defaults

### Performance Optimizations

- Parallel file processing with ProcessPoolExecutor
- SHA256-based file hashing for cache invalidation
- Incremental analysis (only re-parse changed files)
- JSON cache at `.docgenie/cache.json`

## Dependencies

### Core
- typer (CLI framework)
- rich (Terminal formatting)
- structlog (Structured logging)
- jinja2 (Template engine)
- pyyaml (Config parsing)
- markdown (Markdown processing)

### Optional
- tree-sitter-languages (Enhanced parsing)

### Development
- pytest (Testing)
- ruff (Linting/formatting)
- mypy (Type checking)
- bandit (Security scanning)
- mkdocs-material (Documentation)

## Testing

Run the comprehensive test suite:

```bash
# All tests with coverage
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage report
pytest --cov=docgenie --cov-report=html
```

## Development

### Code Quality

```bash
# Format code
ruff format src

# Lint
ruff check src

# Type check
mypy src

# Security scan
bandit -r src
```

### Documentation

```bash
# Serve docs locally
mkdocs serve

# Build docs
mkdocs build
```

## Contributing

We welcome contributions! See [CONTRIBUTING.md](docs/contributing.md) for guidelines.

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## CI/CD

GitHub Actions workflow includes:
- Matrix testing (Python 3.9-3.12, Ubuntu/macOS/Windows)
- Linting (ruff, mypy)
- Security scanning (bandit)
- Automated PyPI publishing on tags

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with ❤️ for the open-source community
- Inspired by the need for better automated documentation
- Thanks to all contributors

---

*This README was generated by DocGenie to demonstrate its capabilities*
