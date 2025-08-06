# DocGenie Configuration Guide

DocGenie supports flexible configuration through configuration files, environment variables, and command-line arguments. This guide explains how to customize DocGenie's behavior for your projects.

## Configuration Priority

Configuration is loaded in the following priority order (highest to lowest):

1. **Command line arguments** (highest priority)
2. **Environment variables**
3. **Project-specific config file** (`.docgenie.yml`, `.docgenie.json`, `.docgenie.toml`)
4. **User-specific config file** (`~/.docgenie/config.yml`)
5. **Default values** (lowest priority)

## Configuration File Formats

DocGenie supports multiple configuration file formats:

- **YAML**: `.docgenie.yml` or `.docgenie.yaml`
- **JSON**: `.docgenie.json`
- **TOML**: `.docgenie.toml`

## Creating a Configuration File

### Quick Start

Create a sample configuration file in your project directory:

```bash
python convert_to_html.py init-config
```

Or specify a custom location:

```bash
python convert_to_html.py init-config -o my-config.yml
```

### Manual Configuration

Create a `.docgenie.yml` file in your project root:

```yaml
# Output configuration
output:
  directory: documentation    # Output directory for HTML files
  filename: index.html       # Output filename
  theme: default            # HTML theme: default, dark, minimal

# Generation settings
generation:
  title: "My Project Docs"  # Custom title for documentation
  force_overwrite: false    # Always overwrite existing files
  open_browser: true        # Open generated HTML in browser
  verbose: true            # Enable verbose output

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

## Configuration Options

### Output Section

- `directory`: Output directory for HTML files (default: `docs`)
- `filename`: Output HTML filename (default: `docs.html`)
- `theme`: HTML theme style (default: `default`)

### Generation Section

- `title`: Custom title for documentation (default: auto-detected from README or project)
- `force_overwrite`: Always overwrite existing files without prompting (default: `false`)
- `open_browser`: Open generated HTML in browser automatically (default: `false`)
- `verbose`: Enable verbose output (default: `false`)

### Codebase Section

- `exclude_patterns`: List of glob patterns to exclude from analysis
- `exclude_files`: List of specific files to exclude
- `exclude_directories`: List of specific directories to exclude
- `include_patterns`: List of patterns to explicitly include (overrides excludes)

### HTML Section

- `custom_css`: Path to custom CSS file
- `custom_js`: Path to custom JavaScript file
- `favicon`: Path to favicon file
- `meta_description`: HTML meta description
- `meta_keywords`: HTML meta keywords

## Environment Variables

You can also configure DocGenie using environment variables:

- `DOCGENIE_OUTPUT_DIR`: Output directory
- `DOCGENIE_OUTPUT_FILE`: Output filename
- `DOCGENIE_THEME`: HTML theme
- `DOCGENIE_TITLE`: Documentation title
- `DOCGENIE_FORCE`: Force overwrite (true/false)
- `DOCGENIE_VERBOSE`: Verbose output (true/false)
- `DOCGENIE_OPEN_BROWSER`: Open browser (true/false)

### Examples

```bash
# Set environment variables
export DOCGENIE_OUTPUT_DIR=documentation
export DOCGENIE_TITLE="My API Documentation"
export DOCGENIE_VERBOSE=true

# Run DocGenie
python convert_to_html.py README.md
```

## Using Configuration with CLI

### Specify Configuration File

```bash
# Use specific config file
python convert_to_html.py --config my-config.yml README.md

# Config file can override default behavior
python convert_to_html.py --config my-config.yml --source codebase ./src
```

### Override Configuration

Command line arguments always take precedence over config files:

```bash
# Config says verbose=false, but this will be verbose
python convert_to_html.py --config my-config.yml --verbose README.md

# Config says output=docs/, but this will output to custom/
python convert_to_html.py --config my-config.yml --output custom/ README.md
```

## Exclude Patterns

The `exclude_patterns` support glob-style wildcards:

### Common Patterns

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

### Advanced Patterns

```yaml
codebase:
  exclude_patterns:
    - "test_*.py"          # All files starting with test_
    - "tests/**/*.py"      # All Python files in tests directory
    - "**/temp/**"         # Any temp directory at any level
    - "*.{log,tmp,temp}"   # Files with specific extensions
```

## Include Patterns

Use `include_patterns` to explicitly include files that would otherwise be excluded:

```yaml
codebase:
  exclude_patterns:
    - "*.py"              # Exclude all Python files
  
  include_patterns:
    - "src/main.py"       # But include this specific file
    - "api/**/*.py"       # And all Python files in api directory
```

## User-Wide Configuration

Create a user-wide configuration at `~/.docgenie/config.yml`:

```yaml
# User preferences that apply to all projects
generation:
  verbose: true
  open_browser: true

output:
  theme: dark

html:
  custom_css: ~/.docgenie/my-theme.css
```

## Best Practices

### Project-Specific Configuration

1. **Create a `.docgenie.yml`** in your project root
2. **Commit it to version control** so team members use the same settings
3. **Document custom settings** in your project README

### Exclude Patterns

1. **Start with defaults** and add project-specific exclusions
2. **Use specific patterns** rather than broad exclusions
3. **Test your patterns** with `--verbose` to see what's being excluded

### Themes and Customization

1. **Keep custom CSS minimal** and focused on branding
2. **Test custom themes** with different content types
3. **Consider accessibility** when customizing colors and fonts

## Troubleshooting

### Configuration Not Loading

1. Check file format (YAML, JSON, TOML)
2. Verify file syntax with a validator
3. Use `--verbose` to see which config file is being loaded

### Patterns Not Working

1. Use `--verbose` to see which files are being processed
2. Test patterns with simple glob tools
3. Remember that patterns are relative to the project root

### Environment Variables

```bash
# Check current environment variables
env | grep DOCGENIE

# Unset all DocGenie environment variables
unset DOCGENIE_OUTPUT_DIR DOCGENIE_TITLE DOCGENIE_VERBOSE
```

## Examples

### Minimal Configuration

```yaml
# .docgenie.yml
output:
  directory: docs
generation:
  title: "My Project"
```

### Complex Configuration

```yaml
# .docgenie.yml
output:
  directory: documentation
  filename: index.html
  theme: dark

generation:
  title: "Advanced Project Documentation"
  force_overwrite: true
  open_browser: true
  verbose: true

codebase:
  exclude_patterns:
    - .git/**
    - __pycache__/**
    - "*.pyc"
    - temp/**
    - backup/**
    
  exclude_files:
    - secret_config.py
    - private_settings.json
    
  exclude_directories:
    - legacy_code
    - experimental
    
  include_patterns:
    - "src/**/*.py"
    - "docs/**/*.md"

html:
  custom_css: assets/theme.css
  custom_js: assets/analytics.js
  favicon: assets/icon.ico
  meta_description: "Comprehensive API documentation for advanced users"
  meta_keywords: "api, documentation, python, advanced"
```
