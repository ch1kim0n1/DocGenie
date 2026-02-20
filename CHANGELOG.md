# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.5] - 2026-02-20

### Changed
- Documentation refreshed for the 1.2.0 release:
  - Added an explicit "What's New in 1.2.0" section to the main README.
  - Updated docs home quick-start examples to use current CLI commands.
  - Clarified parser behavior around `async def` discovery in API docs.
  - Corrected docs repository links to `ch1kim0n1/DocGenie`.
- Completed MkDocs documentation structure to match navigation and pass strict builds.
- CI quality gates hardened:
  - Added package verification (`python -m build`, `twine check dist/*`).
  - Enforced coverage gate in tests (`pytest --cov-fail-under=90`).
  - Scope linting to maintained code paths (`src`, `tests`) with formatting checks on `src`.
- `pytest-asyncio` loop scope explicitly configured to remove deprecation warnings.
- Removed tracked legacy package metadata (`docgenie.egg-info/*`) from version control.

### Added
- Public runtime parser registration API: `ParserRegistry.register(plugin)` with
  replace-by-name and priority re-sorting semantics.
- Expanded unit coverage for parser internals, plugin loading paths, utils classification
  branches, and generator website metadata paths.

### Fixed
- `TreeSitterParser` now safely returns empty parse results when parser resolution fails or
  runtime parse errors occur, instead of propagating parser exceptions.
- README generator footer repository link updated to the active repository URL.

## [1.2.0] - 2026-02-20

### Added
- Comprehensive test suite expansion: new unit tests for `models`, `utils`, `logging`,
  `html_generator`, `convert_to_html`, and `parsers` modules; integration tests covering
  all CLI commands (`generate`, `analyze`, `init`, `html`).
- Shared `tests/conftest.py` and `tests/integration/conftest.py` fixtures for reuse
  across unit and integration tests.
- New integration test validating module entrypoint execution via `python -m docgenie`.
- `HTMLGenerator` exported from the top-level `docgenie` package (`__all__`).
- `keywords` field in `pyproject.toml` for better PyPI discoverability.
- `"Typing :: Typed"` PyPI classifier (since `py.typed` marker is present).
- `"Bug Tracker"` URL in `pyproject.toml`.
- `demo_library/` example project and `scripts/run_demo.py` to demonstrate end-to-end
  documentation generation.
- `build` and `twine` added to dev dependencies for local PyPI verification.

### Fixed
- **`PythonAstParser` async bug**: `async def` functions at module scope and async methods
  inside class bodies were silently dropped. Fixed by broadening the `isinstance` guard to
  `(ast.FunctionDef, ast.AsyncFunctionDef)` at both the module and class levels.
- **`HTMLGenerator` state bleed**: calling `generate_from_readme()` multiple times on the
  same instance produced incorrect TOC output because the `markdown.Markdown` instance was
  never reset. Fixed by calling `self.markdown_processor.reset()` before each conversion.

### Changed
- Development status classifier upgraded from `4 - Beta` to `5 - Production/Stable`.
- Outdated `typing.Dict` / `typing.List` annotations modernized to built-in `dict`/`list`
  in `utils.py` and `generator.py`; removed the now-unnecessary `UP006`/`UP035` ruff
  per-file suppressions.
- `pyproject.toml` TOML formatting normalized (removed stray leading spaces from section
  headers).
- Ruff configuration updated to modern `[tool.ruff.lint]` / `[tool.ruff.lint.per-file-ignores]`
  layout and expanded test-file lint ignores.
- HTML sidebar TOC presentation improved (clearer nested heading hierarchy and active-link
  styling).

## [1.1.0] - 2026-01-24

### Fixed
- Package the `docgenie-html` console script correctly (no repo-root shim / `sys.path` hacks).
- Remove unused snapshot test plugins that conflicted with pytest CLI options.
- Fix ruff formatting issues and mypy YAML stubs.
- Remove tracked cache/coverage artifacts from the repository.

