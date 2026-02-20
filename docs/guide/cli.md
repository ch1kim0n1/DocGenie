# CLI Usage

DocGenie exposes four commands:

- `generate` — generate markdown and/or HTML docs
- `analyze` — output analysis only
- `init` — create starter `.docgenie.yaml`
- `html` — convert README to HTML or generate HTML from codebase analysis

## Global help

```bash
docgenie --help
docgenie <command> --help
```

## `generate`

```bash
docgenie generate PATH [--format markdown|html|both] [--output PATH]
```

Useful options:

- `--preview` (print output instead of saving)
- `--force` (overwrite without prompt)
- `--ignore PATTERN` (repeatable)
- `--tree-sitter / --no-tree-sitter`
- `--verbose`
- `--json-logs`

## `analyze`

```bash
docgenie analyze PATH --format text|json|yaml
```

## `init`

```bash
docgenie init [--force]
```

## `html`

```bash
# README -> HTML
docgenie html README.md --source readme --output docs.html

# Codebase -> HTML
docgenie html . --source codebase --output docs.html
```

Optional:

- `--title` (README source mode)
- `--open-browser`
- `--tree-sitter / --no-tree-sitter`
