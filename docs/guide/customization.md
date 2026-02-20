# Customization

Customize analysis and output through configuration and CLI flags.

## Ignore patterns

Use either config file or CLI:

```yaml
ignore_patterns:
  - "*.log"
  - "dist/"
  - "build/"
```

```bash
docgenie generate . --ignore "*.cache" --ignore "tmp/*"
```

## Template customizations

```yaml
template_customizations:
  include_api_docs: true
  include_directory_tree: true
  max_functions_documented: 25
```

## Tree-sitter behavior

```bash
docgenie generate . --tree-sitter
# or
docgenie generate . --no-tree-sitter
```

## Logging style

```bash
docgenie generate . --verbose
docgenie generate . --json-logs
```

## Output paths

```bash
docgenie generate . --output ./artifacts
```

If output path is a directory, DocGenie writes `README.md` / `docs.html` in that directory.
