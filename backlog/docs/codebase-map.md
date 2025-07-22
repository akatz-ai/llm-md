# Codebase Map

```
.
├── CLAUDE.md                           # 📋 Project instructions and Python environment setup
├── LICENSE                             # MIT license
├── README.md                           # 📖 User documentation and usage examples
├── backlog/                            # 📁 Project management and documentation
│   ├── archive/                        # Archived tasks and drafts
│   │   ├── drafts/
│   │   └── tasks/
│   ├── config.yml                      # Backlog configuration
│   ├── decisions/                      # Architectural decisions
│   ├── docs/                           # 📁 Project documentation hub
│   │   ├── PRD.md                      # Product Requirements Document
│   │   ├── UV-docs.md                  # UV package manager documentation
│   │   ├── backlog-usage.md            # Instructions for task management
│   │   ├── claude-hooks.md             # Claude Code hooks documentation
│   │   └── codebase-map.md             # This file
│   ├── drafts/                         # Work in progress documents
│   └── tasks/                          # 📋 Active development tasks
├── dist/                               # Build artifacts
├── llm-context.md                      # Generated context file (output)
├── llm.md                              # 📝 Configuration file for this project
├── llm.md.example                      # Example configuration file
├── llm_md.egg-info/                    # Legacy build artifacts
├── llmd.egg-info/                      # Legacy build artifacts
├── main.py                             # 🚀 Development entry point
├── pyproject.toml                      # 📦 Python project configuration and dependencies
├── src/                                # 📁 Main source code directory
│   └── llmd/                           # 🔧 Core application package
│       ├── __init__.py                 # Package initialization
│       ├── cli.py                      # 🎯 CLI command interface with Click
│       ├── generator.py                # 📝 Markdown output generation
│       ├── parser.py                   # 🔍 Configuration and gitignore parsing
│       └── scanner.py                  # 📂 File system scanning and filtering
├── tests/                              # 🧪 Test suite
│   ├── __init__.py                     # Test package initialization
│   ├── conftest.py                     # Pytest configuration
│   ├── test_parser.py                  # Tests for configuration parsing
│   └── test_patterns.py                # Tests for pattern matching
└── uv.lock                             # UV dependency lock file
```

## Key Components

### Core Architecture
- **`src/llmd/cli.py`**: Main CLI entry point using Click framework. Handles command-line arguments, configuration loading, and orchestrates the scanning and generation process.
- **`src/llmd/scanner.py`**: Repository file system scanner with filtering logic. Implements pattern matching for include/exclude/only patterns and respects gitignore rules.
- **`src/llmd/parser.py`**: Configuration file parsers for both `.gitignore` and `llm.md` files. Uses pathspec library for glob pattern matching.
- **`src/llmd/generator.py`**: Markdown output generator that creates formatted documents with table of contents and syntax highlighting.

### Configuration System
- **`llm.md`**: Project configuration file supporting ONLY, INCLUDE, and EXCLUDE patterns
- **`.gitignore`**: Standard Git ignore patterns (automatically respected)
- **Command-line options**: Override configuration with `--only`, `--include`, `--exclude` flags

### Pattern Precedence (highest to lowest)
1. **ONLY patterns** - When present, ONLY these files are included (ignores all exclusions)
2. **INCLUDE patterns** - Rescue files from exclusions (gitignore, EXCLUDE, hidden files)
3. **EXCLUDE patterns** - Additional exclusions beyond gitignore
4. **Default behavior** - All files except gitignored, hidden, and binary files

### Key Features
- **Automatic gitignore respect**: Reads and applies `.gitignore` patterns
- **Binary file detection**: Skips common binary extensions automatically
- **Syntax highlighting**: Maps file extensions to appropriate language identifiers
- **Dry-run mode**: Preview files without generating output
- **Verbose logging**: Detailed output for debugging and verification

### Testing
- **Unit tests**: Located in `tests/unit/` directory
- **Integration tests**: Direct tests in `tests/` directory
- **Pattern testing**: Comprehensive tests for glob pattern matching

### Development Workflow
- **UV package manager**: Used for dependency management and virtual environments
- **Ruff linting**: Code formatting and linting with `uv run ruff check --fix`
- **Pytest testing**: Run tests with `uv run python -m pytest tests/`

### Build System
- **pyproject.toml**: Modern Python packaging configuration
- **Entry point**: `llmd = "llmd.cli:main"` console script
- **Dependencies**: Minimal dependencies (Click, pathspec)