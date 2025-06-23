# Claude Context for llmd Project

## Python Execution
Always run Python commands using the local uv virtual environment:
```bash
uv run python ...
```

## Testing Commands
- Run tests: `uv run pytest`
- Run linting: `uv run ruff check`
- Run type checking: `uv run mypy`

## Version Management
When committing changes (via "add commit push"):
- Always bump the version in pyproject.toml if it hasn't already been updated for the current set of changes
- Use semantic versioning: patch version for bug fixes, minor for new features