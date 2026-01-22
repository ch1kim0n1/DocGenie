# DocGenie Documentation

**DocGenie** is a professional, production-grade Python tool that automatically generates comprehensive documentation for any codebase. It analyzes your project structure, source code, dependencies, and configuration to produce beautiful README files and HTML documentation.

## Features

- 🚀 **Multi-Language Support**: Python, JavaScript, TypeScript, Java, C++, Go, Rust, and more
- 🎨 **Multiple Output Formats**: Markdown (README.md) and HTML documentation
- 🧩 **Plugin Architecture**: Extensible parser system with tree-sitter support
- ⚡ **High Performance**: Parallel processing and intelligent caching
- 🔒 **Security First**: XSS protection, security scanning, automated dependency updates
- 📊 **Rich CLI**: Beautiful terminal output with progress bars and tables
- 🐍 **Python API**: Use DocGenie programmatically in your own tools
- 🧪 **Well Tested**: 90%+ code coverage with comprehensive test suite
- 📝 **Type Safe**: Full type hints with mypy strict mode

## Quick Example

```bash
# Install DocGenie
pip install docgenie[full]

# Generate documentation for your project
docgenie /path/to/project --format both

# That's it! README.md and docs.html are now in your project
```

## Why DocGenie?

Traditional documentation tools are often limited to single languages or require extensive configuration. DocGenie works out of the box:

- **No Configuration Required**: Analyzes your project automatically
- **Intelligent Detection**: Recognizes project types, frameworks, and patterns
- **Beautiful Output**: Professional-grade documentation that looks great
- **Incremental Updates**: Smart caching means fast re-generation
- **Battle-Tested**: Production-grade code quality

## Use Cases

- **Open Source Projects**: Generate comprehensive README files for GitHub
- **Internal Tools**: Create documentation for company codebases
- **CI/CD Integration**: Auto-generate docs on every commit
- **Project Onboarding**: Help new developers understand codebases quickly
- **Documentation as Code**: Keep docs in sync with code automatically

## What's Next?

- [Installation Guide](getting-started/installation.md) - Get DocGenie installed
- [Quick Start](getting-started/quickstart.md) - Generate your first documentation
- [CLI Usage](guide/cli.md) - Learn all the commands and options
- [Python API](guide/api.md) - Use DocGenie in your code

## Community

- **GitHub**: [github.com/docgenie/docgenie](https://github.com/docgenie/docgenie)
- **Issues**: Report bugs and request features
- **Contributing**: We welcome contributions!

## License

DocGenie is licensed under the MIT License. See [LICENSE](https://github.com/docgenie/docgenie/blob/main/LICENSE) for details.
