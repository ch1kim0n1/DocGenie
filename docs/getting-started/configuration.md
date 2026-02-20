# Configuration

DocGenie loads optional project config from `.docgenie.yaml` in your target directory.

## Generate starter config

```bash
docgenie init
```

Use `--force` to overwrite an existing config.

## Example

```yaml
ignore_patterns:
  - "*.log"
  - "build/"
  - "dist/"

template_customizations:
  include_api_docs: true
  include_directory_tree: true
  max_functions_documented: 25
```

## How ignore rules are applied

- CLI `--ignore` patterns are merged with config `ignore_patterns`
- Duplicates are de-duplicated
- Final pattern set is applied during analysis

## Tip

Keep project-specific ignores in `.docgenie.yaml`, and use CLI `--ignore` for one-off runs.
