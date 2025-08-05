# DocGenie HTML Documentation Guide

This guide covers how to use DocGenie's new HTML documentation generation features.

## 🌐 HTML Documentation Features

DocGenie now supports generating beautiful, responsive HTML documentation in addition to README.md files. Key features include:

- **Modern Design**: Clean, professional styling with responsive layout
- **Interactive Navigation**: Sidebar table of contents with smooth scrolling
- **Syntax Highlighting**: Code blocks with proper syntax highlighting
- **Mobile Friendly**: Responsive design that works on all devices
- **Multiple Themes**: Support for different visual themes
- **Fast Loading**: Optimized CSS and JavaScript for quick loading

## 📋 Available Formats

### Command Line Options

```bash
# Generate README.md only (default)
docgenie /path/to/project --format markdown

# Generate HTML documentation only
docgenie /path/to/project --format html

# Generate both README.md and HTML documentation
docgenie /path/to/project --format both
```

### Output Files

- **Markdown format**: Creates `README.md`
- **HTML format**: Creates `docs.html`
- **Both formats**: Creates both `README.md` and `docs.html`

## 🛠️ Installation and Setup

Make sure you have the required dependencies:

```bash
pip install -r requirements.txt
```

The HTML generator requires the `markdown` package with extensions, which is already included in `requirements.txt`.

## 🚀 Usage Examples

### 1. Basic HTML Generation

```bash
# Generate HTML documentation for current directory
docgenie . --format html

# Generate HTML for specific project
docgenie /path/to/my-project --format html

# Specify custom output location
docgenie /path/to/project --format html --output /path/to/docs.html
```

### 2. Generate Both Formats

```bash
# Create both README.md and docs.html
docgenie /path/to/project --format both

# Preview both formats without saving
docgenie /path/to/project --format both --preview
```

### 3. Convert Existing README to HTML

Use the standalone HTML converter:

```bash
# Convert README.md to HTML
docgenie-html README.md --source readme

# Convert with custom title and output location
docgenie-html README.md --source readme --title "My Project Docs" --output docs.html

# Convert and open in browser
docgenie-html README.md --source readme --open-browser
```

### 4. Generate HTML from Codebase

```bash
# Analyze codebase and generate HTML directly
docgenie-html /path/to/project --source codebase

# With custom output path
docgenie-html /path/to/project --source codebase --output documentation.html
```

## 🎨 HTML Features and Styling

### Design Elements

- **Gradient header** with project branding
- **Sidebar navigation** with clickable table of contents
- **Syntax-highlighted code blocks** using Prism.js
- **Responsive tables** and lists
- **Font Awesome icons** for visual enhancement
- **Smooth animations** and hover effects

### Responsive Design

The HTML documentation automatically adapts to different screen sizes:

- **Desktop**: Full sidebar navigation with main content area
- **Tablet**: Collapsible sidebar with touch-friendly navigation
- **Mobile**: Stack layout with hamburger menu for navigation

### Code Highlighting

Supports syntax highlighting for all major programming languages:

- Python, JavaScript, TypeScript
- Java, C++, C#, Go, Rust
- HTML, CSS, JSON, YAML
- Shell scripts and more

## 🔧 Advanced Usage

### Python API

You can also use the HTML generator programmatically:

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

### Customization Options

The HTML generator includes several customization points:

1. **Custom Titles**: Use `--title` flag or set programmatically
2. **Output Paths**: Specify custom output locations
3. **Project Branding**: Automatically extracts project information
4. **Theme Support**: Built-in themes with more coming

## 📁 File Structure

When generating HTML documentation, DocGenie creates:

```
your-project/
├── README.md           # Markdown documentation (if requested)
├── docs.html          # HTML documentation (if requested)
└── ... (your project files)
```

## 🌟 Best Practices

### For README to HTML Conversion

1. **Use proper markdown formatting** for best HTML conversion
2. **Include clear headings** for automatic table of contents generation
3. **Use code blocks with language specification** for syntax highlighting
4. **Add emojis and icons** to make documentation more engaging

### For Direct HTML Generation

1. **Run from project root** for best analysis results
2. **Use `--verbose` flag** to see detailed generation process
3. **Preview first** with `--preview` before final generation
4. **Use `--both` format** to maintain both documentation formats

## 🐛 Troubleshooting

### Common Issues

1. **Missing dependencies**: Ensure `markdown` package is installed
2. **Permission errors**: Check write permissions for output directory
3. **Large codebases**: Use `--ignore` flag to exclude unnecessary files
4. **Encoding issues**: Ensure source files use UTF-8 encoding

### Performance Tips

- Use `.gitignore` patterns to exclude large binary files
- Consider using `--ignore` for build directories and dependencies
- For very large projects, generate documentation in sections

## 🔄 Migration from README-only

If you're upgrading from README-only DocGenie:

```bash
# Your old command
docgenie /path/to/project

# New equivalent (same behavior)
docgenie /path/to/project --format markdown

# To get both formats
docgenie /path/to/project --format both
```

## 📊 Example Output

Here's what you can expect from the HTML documentation:

- **Professional appearance** suitable for project websites
- **Full project analysis** including file structure, dependencies, and code statistics
- **Interactive elements** like collapsible sections and smooth scrolling
- **Print-friendly styling** for offline documentation
- **SEO-friendly structure** with proper heading hierarchy

## 🚀 Next Steps

1. Try generating HTML documentation for your projects
2. Experiment with different formats and options
3. Share the generated HTML documentation with your team
4. Customize the styling for your organization's branding needs

---

For more advanced usage and API documentation, check out the Python examples in the `examples/` directory.
