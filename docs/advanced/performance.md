# Performance

DocGenie is optimized for practical codebase analysis speed and repeat runs.

## Current performance features

- Parallel analysis paths in core analyzer
- Optional tree-sitter parsing toggle
- Cache support for incremental analysis

## Practical tuning

```bash
# Use default parser set
docgenie generate . --no-tree-sitter

# Or enable tree-sitter for richer parsing
docgenie generate . --tree-sitter
```

## Large repository tips

- Maintain a focused `.docgenie.yaml` ignore list.
- Exclude build artifacts and generated files.
- Run in CI with stable dependency versions.
