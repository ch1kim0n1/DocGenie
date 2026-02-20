# DocGenie - Test & Quality Results

**Date**: 2026-02-20  
**Status**: ✅ **RELEASE GATES PASSING**

## Executive Summary

- Unit + integration suite passes fully.
- Global coverage gate (`>=90%`) passes.
- Type checks (`mypy src`) pass.
- Security scan (`bandit`) reports no issues.
- Packaging validation (`python -m build`, `twine check`) passes.
- Docs build (`mkdocs build --strict`) passes.

## Verified Commands

```bash
pytest --cov-fail-under=90
ruff check src tests
ruff format --check src
mypy src
bandit -r src -c pyproject.toml
python -m build
twine check dist/*
mkdocs build --strict
```

## Test Results

```text
250 passed
```

## Coverage Report (latest)

```text
TOTAL 1265 statements, 119 missed, 91% coverage
Required test coverage of 90% reached. Total coverage: 90.59%
```

### Coverage by module

- `src/docgenie/core.py`: 95%
- `src/docgenie/html_generator.py`: 98%
- `src/docgenie/utils.py`: 93%
- `src/docgenie/generator.py`: 86%
- `src/docgenie/parsers.py`: 87%
- `src/docgenie/cli.py`: 83%

## Notes

- Coverage gate is enforced in CI test command (`pytest --cov-fail-under=90`).
- Parser system now includes runtime registration tests and tree-sitter failure-path tests.
- `pytest-asyncio` loop-scope warning addressed via explicit pytest config.

## Maintenance Policy

For each release candidate:

1. Run all commands listed in **Verified Commands**.
2. Update this file with exact command outcomes and date.
3. Ensure `CHANGELOG.md` reflects functional and quality-gate changes.
