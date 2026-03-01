# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.6] - 2026-03-01

### Changed

- Version bump to 1.1.6.

## [1.1.5] - 2026-03-01

### Fixed

- Exclude hidden files when `include_hidden` is false in analysis config.
- Exclude generated files (e.g. `*.lock`) when `exclude_generated` is true.
- HTML generator: add mobile menu button, back-to-top link, and TOC filter label for accessibility.
- Index store test and CLI integration test updated to match current API (e.g. `diff-index` command, `start_run` signature).
- Ruff: refactor `_skip_reason` to satisfy PLR0911 (too many returns) for macOS/Linux CI.

### Changed

- Documentation: removed emojis and updated wording for a professional tone across README, docs, and changelog.

## [1.1.0] - 2026-01-24

### Fixed

- Package the `docgenie-html` console script correctly (no repo-root shim or `sys.path` hacks).
- Remove unused snapshot test plugins that conflicted with pytest CLI options.
- Fix ruff formatting issues and mypy YAML stubs.
- Remove tracked cache/coverage artifacts from the repository.

