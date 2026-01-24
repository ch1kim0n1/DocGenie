# DocGenie

Auto-documentation tool that generates `README.md` and HTML docs for a codebase.

## Quick Guide

### Installation

```bash
python3 -m pip install "docgenie"
```

Requirements: **Python 3.10+**

### Setup (from source)

```bash
git clone https://github.com/ch1kim0n1/DocGenie.git
cd DocGenie
python3 -m pip install -e "."
```

### Usage

#### Generate Markdown README

```bash
docgenie generate /path/to/project --format markdown
```

#### Generate HTML Documentation

```bash
docgenie generate /path/to/project --format html
```

#### Generate Both Formats

```bash
docgenie generate /path/to/project --format both
```

#### Convert Existing README to HTML

```bash
docgenie html README.md --source readme --output docs.html
# or, using the legacy convenience command:
docgenie-html README.md --source readme --output docs.html
```

#### Programmatic Usage (Python API)

```python
from docgenie.core import CodebaseAnalyzer
from docgenie.html_generator import HTMLGenerator

analyzer = CodebaseAnalyzer('/path/to/project')
data = analyzer.analyze()

html_generator = HTMLGenerator()
html_content = html_generator.generate_from_analysis(data, "output.html")
```

## Troubleshooting

- Ensure all dependencies are installed
- Check write permissions for output directory
- Use UTF-8 encoding for source files

## License

MIT License. See LICENSE file for details.

## What DocGenie Analyzes

- **📁 Project Structure**: Directory tree and file organization
- **💻 Source Code**: Functions, classes, methods, and documentation
- **📦 Dependencies**: Package files (requirements.txt, package.json, etc.)
- **🔧 Configuration**: Config files and project settings
- **📝 Documentation**: Existing docs and README files
- **🌿 Git Information**: Repository details, branches, contributors
- **📊 Statistics**: Language distribution, code metrics

## Example Output

DocGenie generates README files with:

- **Project Overview**: Auto-generated description and features
- **Installation Instructions**: Detected from your dependency files
- **Usage Examples**: Based on your code structure
- **API Documentation**: Extracted from functions and classes
- **Project Structure**: Visual directory tree
- **Dependencies**: Organized by package manager
- **Contributing Guidelines**: Standard open-source templates

## Advanced Usage

### Command Line Options

```bash
# Basic usage
docgenie --help                                 # Show help
docgenie generate . --verbose                   # Enable detailed output
docgenie generate . --force                     # Overwrite existing files

# Format options
docgenie generate . --format markdown           # README.md only (default)
docgenie generate . --format html               # HTML documentation only
docgenie generate . --format both               # Generate both README.md and HTML

# Output options
docgenie generate . --output custom_path        # Custom output location
docgenie generate . --preview                   # Preview without saving

# HTML converter
docgenie html README.md --source readme         # Convert README to HTML
docgenie html . --source codebase               # Generate HTML from code

# Analysis tools
docgenie analyze . --format json                # Output analysis as JSON
docgenie init                                   # Create basic README template
```

### Configuration

Create a `.docgenie.yaml` file in your project root:

```yaml
ignore_patterns:
  - "*.log"
  - "temp/*"
  - "private/"

template_customizations:
  include_api_docs: true
  include_directory_tree: true
  max_functions_documented: 20
```

## 🏗️ Architecture

DocGenie consists of several key components:

- **CodebaseAnalyzer**: Multi-language code analysis engine with caching and concurrency
- **ParserRegistry**: Pluggable parsers (AST, tree-sitter, regex fallback) per language
- **ReadmeGenerator**: Jinja2-based template rendering system for markdown
- **HTMLGenerator**: Beautiful HTML documentation generator with responsive design
- **CLI Interface**: Typer + Rich powered user experience

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Run the test suite (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/ch1kim0n1/DocGenie.git
cd DocGenie
pip install -e ".[dev]"
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to all contributors who help make DocGenie better
- Inspired by the need for better automated documentation tools
- Built with love for the open-source community

---

**⭐ If DocGenie helps you, please star this repository to support the project!**
