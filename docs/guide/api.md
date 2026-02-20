# Python API

Use DocGenie programmatically for custom tooling and automation.

## Core flow

```python
from docgenie import CodebaseAnalyzer, ReadmeGenerator, HTMLGenerator

analyzer = CodebaseAnalyzer("/path/to/project")
analysis = analyzer.analyze()

readme = ReadmeGenerator().generate(analysis)
html = HTMLGenerator().generate_from_analysis(analysis)
```

## Analyzer

`CodebaseAnalyzer` gathers project structure, functions/classes, imports, dependencies, and metadata.

## Generators

- `ReadmeGenerator` builds markdown docs from analysis data
- `HTMLGenerator` renders HTML from README markdown or analysis data

## Parsers

Use `ParserRegistry` for language parsing and plugin integration.
See API reference for registration and priority behavior.
