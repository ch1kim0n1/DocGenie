# Contributing

Thanks for contributing to DocGenie.

## Development setup

```bash
git clone https://github.com/ch1kim0n1/DocGenie.git
cd DocGenie
pip install -e ".[dev]"
```

## Local quality checks

```bash
ruff check .
ruff format --check .
mypy src
bandit -r src -c pyproject.toml
pytest
```

## Workflow

1. Create a feature branch.
2. Add or update tests for behavior changes.
3. Keep docs/changelog in sync.
4. Open a pull request with clear scope.

## Artifact hygiene

- Do not commit generated packaging artifacts (`dist/`) or legacy metadata directories
	(`*.egg-info/`).
- Build and validate artifacts locally or in CI when preparing releases.

## Coding expectations

- Keep changes focused and minimal.
- Prefer typed interfaces.
- Preserve CLI/API compatibility when possible.
