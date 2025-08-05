# DocGenie

**Auto-documentation tool for any codebase - Generate comprehensive README files and beautiful HTML documentation in minutes!**

<img width="660" height="338" alt="image" src="https://github.com/user-attachments/assets/7f32a0a7-8360-459c-a20e-5d34b74b8c43" />

DocGenie is a powerful Python library that automatically analyzes your codebase and generates comprehensive, professional documentation. Choose between README.md files, beautiful HTML documentation, or both formats. Simply run one command and get detailed documentation with project structure, dependencies, API documentation, and more!

## Features

- **🔍 Multi-language Support**: Analyzes Python, JavaScript, TypeScript, Java, C++, Go, Rust, and more
- **📊 Comprehensive Analysis**: Extracts functions, classes, dependencies, and project structure
- **🎨 Beautiful Templates**: Generates professional README files with modern formatting
- **🌐 HTML Documentation**: Creates responsive HTML documentation with interactive navigation
- **⚡ One-Command Operation**: `docgenie .` - that's it!
- **📱 Multiple Formats**: Generate README.md, HTML docs, or both simultaneously
- **🔧 Highly Configurable**: Customize ignore patterns, output format, and more
- **📈 Smart Detection**: Automatically detects project type, main language, and features
- **🌐 Git Integration**: Includes repository information and contributor statistics
- **📦 Dependency Analysis**: Supports requirements.txt, package.json, Cargo.toml, go.mod, and more

## Requirements

- Python 3.8 or higher
- Git (optional, for repository information)

## Installation

### Install from PyPI (Coming Soon)

```bash
pip install docgenie
```

### Install from Source

```bash
git clone https://github.com/yourusername/DocGenie.git
cd DocGenie
pip install -e .
```

## Quick Start

## Simple CLI Usage

```bash
# Generate HTML documentation only
docgenie /path/to/project --format html

# Generate both README.md and HTML
docgenie /path/to/project --format both

# Convert existing README to HTML
docgenie-html README.md --source readme --open-browser

# Preview HTML without saving
docgenie /path/to/project --format html --preview
```

### Generate Documentation

```bash
# Generate README.md only (default)
docgenie .

# Generate HTML documentation only
docgenie . --format html

# Generate both README.md and HTML documentation
docgenie . --format both

# Preview without saving
docgenie . --preview

# Specify custom output location
docgenie . --output /path/to/custom/README.md
```

### HTML Documentation Features

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
