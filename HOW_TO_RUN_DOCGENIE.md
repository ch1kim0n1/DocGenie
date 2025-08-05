# How to Run DocGenie - Auto Documentation Tool

## Quick Start

### 1. Install DocGenie

```bash
# Navigate to the DocGenie project directory
cd /path/to/DocGenie

# Install in editable mode
pip install -e .
```

### 2. Basic Usage

```bash
# Generate README for any project
docgenie <project_path>

# Examples:
docgenie my_project/
docgenie /path/to/another/project
docgenie .
```

### 3. Advanced Options

#### Preview without saving

```bash
docgenie <project_path> --preview
```

#### Save to specific file

```bash
docgenie <project_path> --output README.md
docgenie <project_path> --output docs/README.md
```

#### Force overwrite existing files

```bash
docgenie <project_path> --force
```

#### Verbose output for debugging

```bash
docgenie <project_path> --verbose
```

#### Custom ignore patterns

```bash
docgenie <project_path> --ignore "*.log,*.tmp,node_modules/"
```

### 4. Command Line Options

```bash
docgenie --help
```

Available options:

- `--output, -o`: Output file path (default: README.md)
- `--preview, -p`: Preview without saving
- `--force, -f`: Force overwrite existing files
- `--ignore, -i`: Comma-separated ignore patterns
- `--verbose, -v`: Verbose output
- `--version`: Show version

### 5. Example Workflow

#### Step 1: Create a test project

```bash
mkdir my_test_project
cd my_test_project
```

#### Step 2: Add some code files

```python
# main.py
def hello_world():
    """Print hello world."""
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
```

#### Step 3: Generate documentation

```bash
# From the parent directory
docgenie my_test_project/

# Or from within the project
cd my_test_project
docgenie .
```

#### Step 4: Preview first

```bash
docgenie my_test_project/ --preview
```

#### Step 5: Generate final README

```bash
docgenie my_test_project/ --output README.md
```

### 6. Supported File Types

DocGenie automatically analyzes:

- **Python**: .py files
- **JavaScript**: .js files
- **TypeScript**: .ts, .tsx files
- **Java**: .java files
- **C++**: .cpp, .cc, .cxx, .h, .hpp files
- **Go**: .go files
- **Rust**: .rs files
- **Configuration**: requirements.txt, package.json, pom.xml, Cargo.toml, go.mod
- **Documentation**: README.md, LICENSE, .md files

### 7. What Gets Generated

The tool automatically creates a README with:

- ✅ Project description and features
- ✅ Installation instructions
- ✅ Usage examples with code snippets
- ✅ Project structure tree
- ✅ Language distribution statistics
- ✅ Complete API reference (functions, classes, methods)
- ✅ Dependencies and requirements
- ✅ Git repository information
- ✅ Contributing guidelines
- ✅ License information

### 8. Configuration

Create a `.docgenie.yaml` file in your project root for custom settings:

```yaml
# .docgenie.yaml
ignore:
  - "*.log"
  - "node_modules/"
  - "venv/"
  - ".git/"

template:
  custom_sections:
    - "Custom Section"
    - "Another Section"

output:
  filename: "README.md"
  format: "markdown"
```

### 9. Programmatic Usage

Use DocGenie as a Python library:

```python
from docgenie import CodebaseAnalyzer, ReadmeGenerator

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

### 10. Troubleshooting

#### Common Issues:

**"Command not found: docgenie"**

```bash
# Make sure you installed it correctly
pip install -e .
# Or check if it's in your PATH
which docgenie
```

**"No files found to analyze"**

```bash
# Check if the path is correct
ls <project_path>
# Make sure there are source files in the directory
```

**"Permission denied"**

```bash
# Use --force to overwrite existing files
docgenie <project_path> --force
```

**"Tree-sitter errors"**

```bash
# Install language-specific tree-sitter grammars
pip install tree-sitter-python tree-sitter-javascript
```

### 11. Real Example

The test case we created demonstrates the full workflow:

```bash
# 1. Navigate to DocGenie project
cd /path/to/DocGenie

# 2. Generate documentation for test_code project
docgenie test_code/ --preview

# 3. Save the generated README
docgenie test_code/ --output test_code/README_GENERATED.md

# 4. Check the results
ls test_code/
# Output: calculator.py, README.md, README_GENERATED.md, requirements.txt
```

### 12. Performance Tips

- Use `--preview` first to check output before saving
- Use `--ignore` to skip unnecessary files (logs, build artifacts)
- For large projects, consider running in background
- Use `--verbose` for debugging analysis issues

### 13. Integration

#### With CI/CD:

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
        run: docgenie . --output README.md
      - name: Commit changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add README.md
          git commit -m "Auto-generate README" || exit 0
          git push
```

#### With pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: docgenie
        name: Generate README
        entry: docgenie . --output README.md
        language: system
        files: ^(?!README\.md$).*\.(py|js|ts|java|cpp|go|rs)$
```

---

**That's it!** With just one command, you can generate comprehensive documentation for any codebase in minutes. The tool handles everything from code analysis to README generation automatically.
