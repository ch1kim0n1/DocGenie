# Security

DocGenie includes security-minded defaults for generated output and CI checks.

## Built-in safeguards

- HTML sanitization for output content
- URL/protocol validation in rendering paths
- Bandit security scanning in CI

## Secure usage guidance

- Treat generated docs as build artifacts.
- Keep dependencies updated.
- Run security and quality checks before releases.

## Recommended pre-release checks

```bash
ruff check .
mypy src
bandit -r src -c pyproject.toml
pytest --cov-fail-under=90
python -m build
twine check dist/*
```
