# DocGenie

A simple Python tool to automatically generate documentation for your codebase. Supports both Markdown (README.md) and HTML formats.

## Quick Guide

### Installation

1. Make sure you have Python 3.8 or higher installed.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

### Setup

Clone the repository (if not using PyPI):

```bash
git clone https://github.com/yourusername/DocGenie.git
cd DocGenie
pip install -e .
```

### Usage

#### Generate Markdown README

```bash
docgenie /path/to/project --format markdown
```

#### Generate HTML Documentation

```bash
docgenie /path/to/project --format html
```

#### Generate Both Formats

```bash
docgenie /path/to/project --format both
```

#### Convert Existing README to HTML

```bash
docgenie-html README.md --source readme --output docs.html
```

#### Programmatic Usage (Python API)

```python
from docgenie.core import CodebaseAnalyzer
from docgenie.html_generator import HTMLGenerator

analyzer = CodebaseAnalyzer('/path/to/project')
data = analyzer.analyze()

html_generator = HTMLGenerator()
html_content = html_generator.generate_from_analysis(data, 'output.html')
```

## Troubleshooting

- Ensure all dependencies are installed
- Check write permissions for output directory
- Use UTF-8 encoding for source files

## License

MIT License. See LICENSE file for details.

```bash
# Generate HTML documentation
docgenie /path/to/project --format html

# Convert existing README to HTML
docgenie-html README.md --source readme --open-browser

# Generate from codebase analysis
docgenie-html /path/to/project --source codebase
```

### Use as Python Library

```python
from docgenie import CodebaseAnalyzer, ReadmeGenerator, HTMLGenerator

# Analyze codebase
analyzer = CodebaseAnalyzer('/path/to/project')
analysis_data = analyzer.analyze()

# Generate README
readme_generator = ReadmeGenerator()
readme_content = readme_generator.generate(analysis_data)

# Generate HTML documentation
html_generator = HTMLGenerator()
html_content = html_generator.generate_from_analysis(analysis_data)

# Or convert README to HTML
html_content = html_generator.generate_from_readme(readme_content, project_name="My Project")
```

## 🎯 What DocGenie Analyzes

- **📁 Project Structure**: Directory tree and file organization
- **💻 Source Code**: Functions, classes, methods, and documentation
- **📦 Dependencies**: Package files (requirements.txt, package.json, etc.)
- **🔧 Configuration**: Config files and project settings
- **📝 Documentation**: Existing docs and README files
- **🌿 Git Information**: Repository details, branches, contributors
- **📊 Statistics**: Language distribution, code metrics

## 📚 Example Output

DocGenie generates README files with:

- **Project Overview**: Auto-generated description and features
- **Installation Instructions**: Detected from your dependency files
- **Usage Examples**: Based on your code structure
- **API Documentation**: Extracted from functions and classes
- **Project Structure**: Visual directory tree
- **Dependencies**: Organized by package manager
- **Contributing Guidelines**: Standard open-source templates

## 🛠️ Advanced Usage

### Command Line Options

```bash
# Basic usage
docgenie --help                         # Show help
docgenie . --verbose                    # Enable detailed output
docgenie . --force                      # Overwrite existing files

# Format options
docgenie . --format markdown            # Generate README.md only (default)
docgenie . --format html                # Generate HTML documentation only
docgenie . --format both                # Generate both README.md and HTML

# Output options
docgenie . --output custom_path         # Custom output location
docgenie . --preview                    # Preview without saving

# HTML converter
docgenie-html README.md --source readme         # Convert README to HTML
docgenie-html /path --source codebase          # Generate HTML from code
docgenie-html README.md --open-browser         # Open result in browser

# Analysis tools
docgenie analyze . --format json        # Output analysis as JSON
docgenie init                           # Create basic README template
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

- **CodebaseAnalyzer**: Multi-language code analysis engine
- **LanguageParser**: Syntax-aware parsers for different languages
- **ReadmeGenerator**: Jinja2-based template rendering system for markdown
- **HTMLGenerator**: Beautiful HTML documentation generator with responsive design
- **CLI Interface**: User-friendly command-line interface with format options

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
git clone https://github.com/yourusername/DocGenie.git
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
