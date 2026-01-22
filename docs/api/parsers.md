# Parsers API Reference

DocGenie uses a pluggable parser architecture to support multiple programming languages.

## ParserRegistry

::: docgenie.parsers.ParserRegistry
    options:
      show_source: true
      heading_level: 3

## ParserPlugin

::: docgenie.parsers.ParserPlugin
    options:
      show_source: true
      heading_level: 3

## Built-in Parsers

### PythonAstParser

::: docgenie.parsers.PythonAstParser
    options:
      show_source: true
      heading_level: 4

### TreeSitterParser

::: docgenie.parsers.TreeSitterParser
    options:
      show_source: true
      heading_level: 4

### RegexParser

::: docgenie.parsers.RegexParser
    options:
      show_source: true
      heading_level: 4

## Usage Example

```python
from pathlib import Path
from docgenie.parsers import ParserRegistry

# Create registry
registry = ParserRegistry(enable_tree_sitter=True)

# Parse a file
with open("example.py") as f:
    content = f.read()

result = registry.parse(
    content=content,
    path=Path("example.py"),
    language="python"
)

# Access parsed data
print(f"Functions: {[f.name for f in result.functions]}")
print(f"Classes: {[c.name for c in result.classes]}")
print(f"Imports: {result.imports}")
```

## Creating Custom Parsers

You can create custom parsers by subclassing `ParserPlugin`:

```python
from docgenie.parsers import ParserPlugin, ParseResult

class RubyParser(ParserPlugin):
    def __init__(self):
        super().__init__(
            name="ruby-parser",
            languages={"ruby"},
            priority=50
        )
    
    def parse(self, content, path, language):
        # Your parsing logic here
        return ParseResult(
            functions=[...],
            classes=[...],
            imports=set([...])
        )

# Register your parser
from docgenie.parsers import ParserRegistry
registry = ParserRegistry()
registry.register(RubyParser())
```
