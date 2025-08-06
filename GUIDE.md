# DocGenie Complete Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Installation and Setup](#installation-and-setup)
3. [Basic Usage](#basic-usage)
4. [Advanced Usage](#advanced-usage)
5. [Configuration System](#configuration-system)
6. [HTML Documentation](#html-documentation)
7. [CLI Reference](#cli-reference)
8. [API and Programmatic Usage](#api-and-programmatic-usage)
9. [Integration](#integration)
10. [Troubleshooting](#troubleshooting)
11. [Implementation Details](#implementation-details)

---

## Introduction

DocGenie is an auto-documentation tool that generates comprehensive documentation for any codebase by analyzing source code, dependencies, and project structure. It supports multiple output formats including markdown (README.md) and HTML documentation.

### Key Features

- **Automatic Analysis**: Analyzes source code across multiple programming languages
- **Multiple Formats**: Generate markdown README files and HTML documentation
- **Modern HTML Output**: Responsive design with syntax highlighting and interactive navigation
- **Flexible Configuration**: Supports YAML, JSON, and TOML configuration files
- **Comprehensive Coverage**: Includes project structure, dependencies, API documentation, and more
- **Integration Ready**: Works with CI/CD pipelines and development workflows

### Supported Languages

DocGenie automatically analyzes and documents:

- **Python**: .py files
- **JavaScript**: .js files
- **TypeScript**: .ts, .tsx files
- **Java**: .java files
- **C++**: .cpp, .cc, .cxx, .h, .hpp files
- **Go**: .go files
- **Rust**: .rs files
- **Configuration**: requirements.txt, package.json, pom.xml, Cargo.toml, go.mod
- **Documentation**: README.md, LICENSE, .md files

---

## Installation and Setup

### Prerequisites

- Python 3.8 or higher
- Git (for repository analysis)

### Installation

```bash
# Navigate to the DocGenie project directory
cd /path/to/DocGenie

# Install in editable mode
pip install -e .
```

### Verify Installation

```bash
# Check if DocGenie is installed correctly
docgenie --help

# Check version
docgenie --version
```

### Dependencies

DocGenie automatically installs required dependencies:

- **click**: Command-line interface framework
- **gitpython**: Git repository analysis
- **jinja2**: Template engine for documentation generation
- **markdown**: Markdown processing for HTML output
- **pyyaml**: YAML configuration file support
- **tomli**: TOML configuration file support
- **pathspec**: Advanced file pattern matching

---

## Basic Usage

### Quick Start

#### Generate Documentation for Current Directory

```bash
# Generate README.md for current directory
docgenie generate

# Generate HTML documentation
docgenie generate --format html

# Generate both README.md and HTML
docgenie generate --format both
```

#### Generate Documentation for Specific Project

```bash
# Generate README.md for specific project
docgenie generate /path/to/project

# Generate HTML with custom output location
docgenie generate /path/to/project --format html --output docs.html
```

#### Convert Existing README to HTML

```bash
# Convert README.md to HTML
docgenie convert README.md

# Convert with custom theme and title
docgenie convert README.md --theme dark --title "My Project Documentation"
```

### Common Options

- `--output, -o`: Specify output path
- `--format`: Choose output format (markdown, html, both)
- `--theme, -t`: Select HTML theme (default, dark, minimal)
- `--force, -f`: Overwrite existing files without prompting
- `--verbose, -v`: Enable verbose output
- `--preview, -p`: Preview output without saving

### Example Workflow

1. **Create a test project**:

   ```bash
   mkdir my_test_project
   cd my_test_project
   ```

2. **Add some code files**:

   ```python
   # main.py
   def hello_world():
       """Print hello world."""
       print("Hello, World!")

   if __name__ == "__main__":
       hello_world()
   ```

3. **Generate documentation**:

   ```bash
   # Preview first
   docgenie generate --preview

   # Generate final documentation
   docgenie generate --format both
   ```

---

## Advanced Usage

### Ignoring Files and Directories

#### Using Command Line

```bash
# Ignore specific patterns
docgenie generate --ignore "*.log" --ignore "temp/*" --ignore "node_modules/"

# Multiple patterns in one option
docgenie generate --ignore "*.log,*.tmp,node_modules/"
```

#### Using Configuration File

Create `.docgenie.yml` in your project root:

```yaml
codebase:
  exclude_patterns:
    - "*.log"
    - "*.tmp"
    - "node_modules/**"
    - "__pycache__/**"
    - ".git/**"

  exclude_files:
    - secret_config.py

  exclude_directories:
    - temp
    - build
    - dist
```

### Custom Titles and Output Paths

```bash
# Custom title
docgenie generate --title "My Amazing Project"

# Custom output directory
docgenie generate --output documentation/ --format html

# Custom filename
docgenie generate --output my-docs.html --format html
```

### Preview Mode

Preview generated documentation without saving:

```bash
# Preview README content
docgenie generate --preview

# Preview HTML structure
docgenie convert README.md --preview
```

### Force Overwrite

```bash
# Overwrite existing files without prompting
docgenie generate --force
```

### Verbose Output

```bash
# Enable detailed output for debugging
docgenie generate --verbose
```

---

## Configuration System

DocGenie supports flexible configuration through configuration files, environment variables, and command-line arguments.

### Configuration Priority

Configuration is loaded in the following priority order (highest to lowest):

1. **Command line arguments** (highest priority)
2. **Environment variables**
3. **Project-specific config file** (`.docgenie.yml`, `.docgenie.json`, `.docgenie.toml`)
4. **User-specific config file** (`~/.docgenie/config.yml`)
5. **Default values** (lowest priority)

### Configuration File Formats

DocGenie supports multiple configuration file formats:

- **YAML**: `.docgenie.yml` or `.docgenie.yaml`
- **JSON**: `.docgenie.json`
- **TOML**: `.docgenie.toml`

### Creating Configuration Files

#### Quick Start

```bash
# Create sample configuration file
docgenie config

# Create in specific location
docgenie config --output my-config.yml
```

#### Manual Configuration

Create a `.docgenie.yml` file in your project root:

```yaml
# Output configuration
output:
  directory: documentation # Output directory for HTML files
  filename: index.html # Output filename
  theme: default # HTML theme: default, dark, minimal

# Generation settings
generation:
  title: "My Project Docs" # Custom title for documentation
  force_overwrite: false # Always overwrite existing files
  open_browser: true # Open generated HTML in browser
  verbose: true # Enable verbose output

# Codebase analysis configuration
codebase:
  exclude_patterns:
    - .git/**
    - __pycache__/**
    - node_modules/**
    - "*.pyc"
    - "*.log"
    - temp/**

  exclude_files:
    - secret_config.py

  exclude_directories:
    - private_docs
    - legacy_code

  include_patterns:
    - "src/important_file.py"

# HTML customization
html:
  custom_css: assets/custom.css
  custom_js: assets/custom.js
  favicon: assets/favicon.ico
  meta_description: "Project documentation"
  meta_keywords: "docs, api, guide"
```

### Configuration Options

#### Output Section

- `directory`: Output directory for HTML files (default: `docs`)
- `filename`: Output HTML filename (default: `docs.html`)
- `theme`: HTML theme style (default: `default`)

#### Generation Section

- `title`: Custom title for documentation (default: auto-detected from README or project)
- `force_overwrite`: Always overwrite existing files without prompting (default: `false`)
- `open_browser`: Open generated HTML in browser automatically (default: `false`)
- `verbose`: Enable verbose output (default: `false`)

#### Codebase Section

- `exclude_patterns`: List of glob patterns to exclude from analysis
- `exclude_files`: List of specific files to exclude
- `exclude_directories`: List of specific directories to exclude
- `include_patterns`: List of patterns to explicitly include (overrides excludes)

#### HTML Section

- `custom_css`: Path to custom CSS file
- `custom_js`: Path to custom JavaScript file
- `favicon`: Path to favicon file
- `meta_description`: HTML meta description
- `meta_keywords`: HTML meta keywords

### Environment Variables

Configure DocGenie using environment variables:

- `DOCGENIE_OUTPUT_DIR`: Output directory
- `DOCGENIE_OUTPUT_FILE`: Output filename
- `DOCGENIE_THEME`: HTML theme
- `DOCGENIE_TITLE`: Documentation title
- `DOCGENIE_FORCE`: Force overwrite (true/false)
- `DOCGENIE_VERBOSE`: Verbose output (true/false)
- `DOCGENIE_OPEN_BROWSER`: Open browser (true/false)

#### Example

```bash
# Set environment variables
export DOCGENIE_OUTPUT_DIR=documentation
export DOCGENIE_TITLE="My API Documentation"
export DOCGENIE_VERBOSE=true

# Run DocGenie
docgenie generate
```

### Pattern Matching

#### Common Exclude Patterns

```yaml
codebase:
  exclude_patterns:
    # Version control
    - .git/**
    - .svn/**

    # Python
    - __pycache__/**
    - "*.pyc"
    - "*.pyo"
    - .venv/**
    - venv/**
    - "*.egg-info/**"

    # Node.js
    - node_modules/**
    - "*.min.js"
    - "*.min.css"

    # Build directories
    - build/**
    - dist/**
    - target/**

    # IDEs
    - .idea/**
    - .vscode/**

    # Temporary files
    - "*.log"
    - "*.tmp"
    - "*.temp"

    # Test coverage
    - coverage/**
    - .pytest_cache/**
```

#### Advanced Patterns

```yaml
codebase:
  exclude_patterns:
    - "test_*.py" # All files starting with test_
    - "tests/**/*.py" # All Python files in tests directory
    - "**/temp/**" # Any temp directory at any level
    - "*.{log,tmp,temp}" # Files with specific extensions
```

#### Include Patterns

Use `include_patterns` to explicitly include files that would otherwise be excluded:

```yaml
codebase:
  exclude_patterns:
    - "*.py" # Exclude all Python files

  include_patterns:
    - "src/main.py" # But include this specific file
    - "api/**/*.py" # And all Python files in api directory
```

---

## HTML Documentation

DocGenie generates beautiful, responsive HTML documentation with modern web features.

### HTML Features

#### Visual Design

- **Modern UI**: Clean, professional design with gradient headers and smooth animations
- **Responsive Layout**: Automatically adapts to desktop, tablet, and mobile devices
- **Interactive Navigation**: Sticky sidebar with clickable table of contents
- **Syntax Highlighting**: Code blocks with proper language detection and highlighting

#### Technical Features

- **Multiple Input Sources**: Generate from codebase analysis or convert existing README files
- **Markdown Processing**: Full markdown support with extensions (tables, code blocks, etc.)
- **SEO Optimized**: Proper heading hierarchy and meta tags
- **Performance Optimized**: Minimal external dependencies, fast loading

### HTML Generation Options

#### Generate HTML from Codebase

```bash
# Generate HTML documentation
docgenie generate --format html

# With custom theme
docgenie generate --format html --theme dark

# With custom output location
docgenie generate --format html --output documentation/index.html
```

#### Convert README to HTML

```bash
# Basic conversion
docgenie convert README.md

# With options
docgenie convert README.md --theme minimal --title "Project Guide" --open-browser
```

#### Generate Both Formats

```bash
# Create both README.md and HTML documentation
docgenie generate --format both
```

### HTML Themes

Currently available themes:

- **default**: Professional blue gradient theme
- **dark**: Dark mode theme (coming soon)
- **minimal**: Clean, minimal styling (coming soon)

### HTML Structure

The generated HTML includes:

- **Responsive header** with project branding
- **Sidebar navigation** with table of contents
- **Main content area** with proper typography
- **Syntax-highlighted code blocks**
- **Mobile-friendly design**

### Performance

#### File Sizes

- **Small Project** (< 10 files): ~15-25 KB HTML file
- **Medium Project** (10-50 files): ~25-50 KB HTML file
- **Large Project** (50+ files): ~50-100 KB HTML file

#### External Dependencies

- **Prism.js**: Syntax highlighting (~50 KB from CDN)
- **Font Awesome**: Icons (~75 KB from CDN)
- **Web Fonts**: System fonts used (no external fonts)

---

## CLI Reference

### Main Commands

#### docgenie generate

Generate documentation from codebase analysis (default command).

```bash
docgenie generate [OPTIONS] [PATH]
```

**Options:**

- `-o, --output PATH`: Output path for generated documentation
- `--format, --fmt [markdown|html|both]`: Output format (default: markdown)
- `-t, --theme [default|dark|minimal]`: HTML theme style
- `--title TEXT`: Custom title for documentation
- `-i, --ignore TEXT`: Additional patterns to ignore (multiple allowed)
- `-f, --force`: Overwrite existing files without prompting
- `--open-browser, --open`: Open generated HTML in browser
- `-p, --preview`: Preview without saving

#### docgenie convert

Convert README.md file to HTML documentation.

```bash
docgenie convert [OPTIONS] README_PATH
```

**Options:**

- `-o, --output PATH`: Output path for HTML file
- `-t, --theme [default|dark|minimal]`: HTML theme style
- `--title TEXT`: Custom title for HTML documentation
- `-f, --force`: Overwrite existing HTML file without prompting
- `--open-browser, --open`: Open generated HTML in browser
- `-p, --preview`: Preview without saving

#### docgenie analyze

Analyze codebase and output detailed information.

```bash
docgenie analyze [OPTIONS] [PATH]
```

**Options:**

- `-f, --format [json|yaml|text]`: Output format for analysis results (default: text)

#### docgenie config

Create a sample configuration file.

```bash
docgenie config [OPTIONS]
```

**Options:**

- `-o, --output PATH`: Output path for config file (default: .docgenie.yml)

#### docgenie init

Initialize a new project with a basic README template.

```bash
docgenie init
```

### Global Options

Available for all commands:

- `-c, --config PATH`: Path to configuration file
- `-v, --verbose`: Enable verbose output
- `--version`: Show version and exit
- `--help`: Show help message and exit

### Examples

```bash
# Basic usage
docgenie generate

# Generate HTML with dark theme
docgenie generate --format html --theme dark

# Convert README with custom title
docgenie convert README.md --title "API Documentation"

# Analyze project and output JSON
docgenie analyze --format json

# Create configuration file
docgenie config --output project-config.yml

# Use custom configuration
docgenie --config project-config.yml generate --format both
```

---

## API and Programmatic Usage

Use DocGenie as a Python library for custom integrations.

### Basic Usage

```python
from docgenie import CodebaseAnalyzer, ReadmeGenerator
from docgenie.html_generator import HTMLGenerator

# Analyze a codebase
analyzer = CodebaseAnalyzer("path/to/project")
data = analyzer.analyze()

# Generate README
generator = ReadmeGenerator()
readme_content = generator.generate(data)

# Save to file
with open("README.md", "w") as f:
    f.write(readme_content)
```

### HTML Generation

```python
from docgenie.core import CodebaseAnalyzer
from docgenie.html_generator import HTMLGenerator

# Analyze codebase
analyzer = CodebaseAnalyzer('/path/to/project')
analysis_data = analyzer.analyze()

# Generate HTML
html_generator = HTMLGenerator()
html_content = html_generator.generate_from_analysis(
    analysis_data,
    'output.html'
)

# Or convert existing README
with open('README.md', 'r') as f:
    readme_content = f.read()

html_content = html_generator.generate_from_readme(
    readme_content,
    'docs.html',
    'My Project'
)
```

### Configuration Integration

```python
from docgenie.config import load_config
from docgenie.core import CodebaseAnalyzer

# Load configuration
config = load_config('/path/to/project')

# Use with analyzer
analyzer = CodebaseAnalyzer('/path/to/project', config=config)
data = analyzer.analyze()
```

### Custom Ignore Patterns

```python
# With custom ignore patterns
analyzer = CodebaseAnalyzer(
    '/path/to/project',
    ignore_patterns=['*.log', 'temp/**', 'node_modules/**']
)
data = analyzer.analyze()
```

---

## Integration

### CI/CD Integration

#### GitHub Actions

```yaml
# .github/workflows/docs.yml
name: Generate Documentation
on: [push, pull_request]
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install DocGenie
        run: pip install -e .
      - name: Generate README
        run: docgenie generate --output README.md
      - name: Commit changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add README.md
          git commit -m "Auto-generate README" || exit 0
          git push
```

#### GitHub Pages

```yaml
# .github/workflows/docs.yml
name: Generate Documentation
on: [push]
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: "3.9"
      - name: Install DocGenie
        run: pip install docgenie
      - name: Generate Documentation
        run: docgenie generate --format html --output docs/index.html
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

#### Netlify

```toml
# netlify.toml
[build]
  command = "pip install docgenie && docgenie generate --format html --output public/index.html"
  publish = "public"
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: docgenie
        name: Generate README
        entry: docgenie generate --output README.md
        language: system
        files: ^(?!README\.md$).*\.(py|js|ts|java|cpp|go|rs)$
```

### Docker Integration

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

# Generate documentation on build
RUN docgenie generate --format both

EXPOSE 8000
CMD ["python", "-m", "http.server", "8000"]
```

---

## Troubleshooting

### Common Issues

#### Installation Problems

**"Command not found: docgenie"**

```bash
# Make sure you installed it correctly
pip install -e .

# Check if it's in your PATH
which docgenie

# Try reinstalling
pip uninstall docgenie
pip install -e .
```

#### Analysis Issues

**"No files found to analyze"**

```bash
# Check if the path is correct
ls <project_path>

# Make sure there are source files in the directory
# Use --verbose to see what files are being processed
docgenie generate --verbose
```

**"Tree-sitter errors"**

```bash
# Install language-specific tree-sitter grammars
pip install tree-sitter-python tree-sitter-javascript
```

#### Permission Issues

**"Permission denied"**

```bash
# Use --force to overwrite existing files
docgenie generate --force

# Check file permissions
ls -la README.md

# Make sure output directory is writable
chmod 755 docs/
```

#### Configuration Issues

**"Configuration not loading"**

1. Check file format (YAML, JSON, TOML)
2. Verify file syntax with a validator
3. Use `--verbose` to see which config file is being loaded

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('.docgenie.yml'))"

# Check JSON syntax
python -c "import json; json.load(open('.docgenie.json'))"
```

**"Patterns not working"**

1. Use `--verbose` to see which files are being processed
2. Test patterns with simple glob tools
3. Remember that patterns are relative to the project root

```bash
# Test glob patterns
python -c "import glob; print(glob.glob('**/*.py', recursive=True))"
```

#### HTML Generation Issues

**"Markdown rendering problems"**

- Ensure proper markdown syntax
- Check for unsupported markdown extensions
- Validate special characters encoding

**"Styling issues"**

- Clear browser cache
- Check console for CSS/JS errors
- Verify external CDN accessibility

**"Large file sizes"**

- Use `--ignore` flag to exclude unnecessary files
- Consider splitting large projects into sections
- Optimize images and media files

### Debug Mode

```bash
# Enable verbose output for debugging
docgenie generate --verbose

# Check environment variables
env | grep DOCGENIE

# Unset all DocGenie environment variables
unset DOCGENIE_OUTPUT_DIR DOCGENIE_TITLE DOCGENIE_VERBOSE
```

### Performance Tips

- Use `--preview` first to check output before saving
- Use `--ignore` to skip unnecessary files (logs, build artifacts)
- For large projects, consider running in background
- Use `--verbose` for debugging analysis issues

---

## Implementation Details

### Architecture Overview

DocGenie consists of several key components:

1. **CodebaseAnalyzer**: Analyzes source code and extracts metadata
2. **ReadmeGenerator**: Generates markdown documentation
3. **HTMLGenerator**: Creates HTML documentation
4. **Configuration System**: Manages settings and preferences
5. **CLI Interface**: Provides command-line access

### Configuration System

#### Configuration Class Structure

```python
class DocGenieConfig:
    def __init__(self, project_path=None, config_file=None)
    def get(self, section, key=None, default=None)
    def set(self, section, key, value)
    def get_output_path(self, input_path=None, source_type='readme')
    def get_exclude_patterns(self)
    def get_include_patterns(self)
    def create_sample_config(self, output_path=None)
```

#### Pattern Matching Enhancement

- Upgraded from simple `fnmatch` to `pathspec` for better glob support
- Added support for gitignore-style patterns
- Implemented include/exclude priority logic

### HTML Generation System

#### HTML Structure

```html
<!DOCTYPE html>
<html>
  <head>
    <!-- Meta tags, CSS, external libraries -->
  </head>
  <body>
    <div class="container">
      <nav class="sidebar">
        <!-- Navigation and TOC -->
      </nav>
      <main class="content">
        <!-- Main documentation content -->
      </main>
    </div>
  </body>
</html>
```

#### CSS Framework

- **CSS Custom Properties**: For easy theming and customization
- **Flexbox/Grid Layout**: Modern layout techniques for responsive design
- **Progressive Enhancement**: Works without JavaScript, enhanced with it

#### JavaScript Features

- **Smooth Scrolling**: Enhanced navigation experience
- **Mobile Menu**: Touch-friendly navigation
- **Syntax Highlighting**: Prism.js for code block highlighting
- **Intersection Observer**: Active section highlighting in navigation

### File Processing

DocGenie processes files in the following order:

1. **Discovery**: Find all files in the project directory
2. **Filtering**: Apply exclude/include patterns
3. **Analysis**: Extract metadata from each file
4. **Aggregation**: Combine analysis results
5. **Generation**: Create documentation output

### Supported File Types

- **Python**: Function and class extraction, docstring parsing
- **JavaScript/TypeScript**: Function and class detection, JSDoc support
- **Java**: Class and method analysis, Javadoc parsing
- **C/C++**: Function and class detection, Doxygen support
- **Go**: Package and function analysis
- **Rust**: Module and function detection
- **Configuration Files**: Dependency analysis for package managers

### Future Roadmap

#### Planned Features

- Multiple theme support
- Custom template system
- Search functionality
- PDF export
- Multi-language support (i18n)
- API documentation enhancements
- Interactive code examples

#### Community Contributions

We welcome contributions for:

- New themes and styling options
- Additional markdown extensions
- Performance optimizations
- Accessibility improvements
- Mobile experience enhancements

---

This comprehensive guide covers all aspects of DocGenie usage, from basic commands to advanced configuration and integration scenarios. For additional support or to contribute to the project, please refer to the project repository and documentation.
