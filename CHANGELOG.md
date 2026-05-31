# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.85] - 2026-05-31

### Security

- HTML generator: sanitize the converted markdown body with an allow-list HTML
  sanitizer before inlining, preventing stored XSS from analyzed source content
  (docstrings, identifiers, dependency names). `javascript:`/`data:` URLs are
  neutralized.

### Fixed

- README "Documentation Quality" section now renders the computed quality score,
  confidence level, and warnings (previously blank).
- README "Run Metrics" section and `analyze --metrics-json` now emit real metrics
  (scanned/changed/skipped files, duration, cache hit ratio).
- README readiness gate now uses the real computed analysis confidence instead of
  always defaulting to `low` (removing a spurious -20 penalty).
- `diff_engine`: rename detection is now controlled correctly; the diff direction
  matches `from_ref -> to_ref` (previously `R=` reversed the diff and the rename
  toggle was a no-op). `--no-rename-detection` now surfaces renames as add+delete.
- External parser plugin loader now catches any exception from `entry_points()`
  and plugin loading, so a broken third-party entry point can no longer crash the
  parser registry.
- `PythonAstParser` now extracts `async def` functions and methods with
  `is_async=True`.
- `generate` now records produced documentation artifacts so `diff-index` reports
  real changes between runs.
- Generated README footer links to the real repository
  (`https://github.com/ch1kim0n1/DocGenie`).
- Generated README version requirements now derive from project metadata
  (`requires-python`, package.json `engines`, `rust-version`, `go` directive)
  instead of fabricated hardcoded minimums.
- Malformed `.docgenie.yaml` and dependency manifests now emit a visible warning
  naming the file instead of being silently ignored.
- `IndexStore` is now a context manager and is closed deterministically in
  `analyze()` (no longer relies on `__del__`), avoiding Windows DB locks.

### Changed

- Default (`strict`) redaction no longer blanket-removes contact emails; email
  redaction now requires `paranoid` mode or an explicit `redact_emails` option.
  Secret patterns (keys/tokens/passwords) are still redacted by default.
- `scan_output_links` now prunes ignored/vendored directories (`.git`,
  `node_modules`, `.venv`, etc.) instead of traversing the whole tree.
- On cache miss, each changed file is read and hashed once per run (was twice).
- Documentation, error messages, and the `docgenie` console-script entry point now
  match the published distribution name `docgenie-cli`.
- Removed duplicated quality-scoring and impact-graph implementations; the HTML
  generator now uses the shared `html_sections`/`readme_quality` modules.

## [1.1.6] - 2025-03-01

### Changed

- Version bump to 1.1.6.

## [1.1.5] - 2025-03-01

### Fixed

- Exclude hidden files when `include_hidden` is false in analysis config.
- Exclude generated files (e.g. `*.lock`) when `exclude_generated` is true.
- HTML generator: add mobile menu button, back-to-top link, and TOC filter label for accessibility.
- Index store test and CLI integration test updated to match current API (e.g. `diff-index` command, `start_run` signature).
- Ruff: refactor `_skip_reason` to satisfy PLR0911 (too many returns) for macOS/Linux CI.

### Changed

- Documentation: removed emojis and updated wording for a professional tone across README, docs, and changelog.

## [1.1.0] - 2025-01-24

### Fixed

- Package the `docgenie-html` console script correctly (no repo-root shim or `sys.path` hacks).
- Remove unused snapshot test plugins that conflicted with pytest CLI options.
- Fix ruff formatting issues and mypy YAML stubs.
- Remove tracked cache/coverage artifacts from the repository.

