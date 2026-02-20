# Quick Start

Generate docs in under a minute.

## 1) Install

```bash
pip install docgenie
```

## 2) Generate README or HTML

```bash
# README only (default)
docgenie generate . --format markdown

# HTML only
docgenie generate . --format html

# Both
docgenie generate . --format both
```

## 3) Preview without writing files

```bash
docgenie generate . --preview
```

## 4) Convert an existing README to HTML

```bash
docgenie html README.md --source readme --output docs.html
```

## 5) Analyze only

```bash
docgenie analyze . --format json
```

## Next

- Configure ignore and template options in `.docgenie.yaml`
- Use `--tree-sitter/--no-tree-sitter` depending on your environment
- See the CLI guide for full options
