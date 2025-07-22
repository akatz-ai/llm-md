## Important Documents

- The main PRD document for this project can be found in backlog/docs/PRD.md
- Claude hooks docs can be found in backlog/docs/claude-hooks.md
- Instructions for using backlog.md tool for task handling: backlog/docs/backlog-usage.md
- Also in the same docs/ directory is UV-docs.md

## Python Environment Management

- ALWAYS use uv and the commands below for python environment management! NEVER try to run the system python!
- uv commands should be run in the root repo directory in order to use the repo's .venv

### Development

- `uv add <package>` - Install dependencies
- `uv run ruff check --fix` - Lint and auto-fix with ruff
- `uv pip list` - View dependencies
- `uv run <command>` - Run cli tools locally installed (e.g. uv run python)

### Testing

- Always put new unit tests under tests/unit directory!
- Try to add new tests to existing test files rather than creating new files (unless necessary)
- `uv run python -m pytest tests/` - Run all tests
- `uv run python -m pytest <filename>` - Run specific test file
