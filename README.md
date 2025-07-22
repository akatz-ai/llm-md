# llmd

A command-line tool that generates consolidated markdown files containing code repository contents for use with Large Language Models (LLMs). It provides flexible file filtering through whitelist/blacklist patterns, respects gitignore rules, and includes GitHub remote repository support.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Usage Examples](#usage-examples)
- [Configuration File](#configuration-file)
- [Command Reference](#command-reference)
- [Pattern Matching](#pattern-matching)
- [Output Path Resolution](#output-path-resolution)
- [Default Behaviors](#default-behaviors)
- [Troubleshooting](#troubleshooting)

## Features

- **Flexible Filtering**: Whitelist and blacklist modes with sequential pattern refinement
- **GitHub Integration**: Clone and process remote GitHub repositories
- **Smart Defaults**: Works out-of-the-box with sensible exclusions
- **Configuration File**: Optional `llm.md` configuration file support
- **Template Generation**: Built-in `init` command to create configuration templates
- **Pattern Matching**: Full gitignore-style glob pattern support
- **Dry Run Mode**: Preview files before generating output
- **Structured Output**: Generates markdown with table of contents and syntax highlighting

## Installation

```bash
# Install using uv (recommended)
uv tool install llmd

# Or install with pip
pip install llmd
```

## Quick Start

```bash
# Generate context for current directory
llmd

# Generate context for specific directory
llmd /path/to/repo

# Process a GitHub repository
llmd --github https://github.com/user/repo

# Create a configuration template
llmd init
```

## Core Concepts

### Filtering Modes

llmd operates in one of two modes:

1. **Whitelist Mode** (`-w`/`--whitelist`): Start with NO files, then add only matching patterns
2. **Blacklist Mode** (`-b`/`--blacklist`): Start with ALL files, then remove matching patterns

### Pattern Processing Order

Patterns are processed **sequentially** when using CLI flags:

```bash
# Sequential processing example:
llmd -w "src/" -e "src/vendor/" -i "src/vendor/critical.py"
# Result: Includes src/ EXCEPT src/vendor/ BUT includes src/vendor/critical.py
```

### Default Exclusions

Unless overridden, these are always excluded:
- Files matched by `.gitignore`
- Hidden files (starting with `.`)
- Binary files (images, executables, etc.)

## Usage Examples

### Basic Usage

```bash
# Current directory with defaults (blacklist mode, standard exclusions)
llmd

# Specific directory
llmd /path/to/repo

# Custom output file
llmd -o my-context.md

# Preview files without generating output
llmd --dry-run
```

### GitHub Repositories

```bash
# Clone and process a public repository
llmd --github https://github.com/user/repo

# With custom output
llmd --github https://github.com/user/repo -o analysis.md

# SSH URLs (requires SSH keys)
llmd --github git@github.com:user/private-repo.git
```

### Whitelist Mode (Include Only Specified Patterns)

```bash
# Include only Python files
llmd -w "*.py"

# Include multiple patterns
llmd -w "src/" -w "tests/" -w "*.md"

# Include directory with exceptions (sequential processing)
llmd -w "src/" -e "src/generated/" -e "src/vendor/"
```

### Blacklist Mode (Exclude Specified Patterns)

```bash
# Exclude test files
llmd -b "tests/" -b "**/*_test.py"

# Exclude with exceptions (sequential processing)
llmd -b "node_modules/" -i "node_modules/my-local-package/"
```

### Sequential Pattern Refinement

The order of `-i` and `-e` flags matters:

```bash
# Different results based on order:
llmd -w "*.py" -e "test.py" -i "test.py"  # test.py is INCLUDED (last rule wins)
llmd -w "*.py" -i "test.py" -e "test.py"  # test.py is EXCLUDED (last rule wins)

# Complex example:
llmd -w "src/" \
     -e "src/generated/" \
     -i "src/generated/important.py" \
     -e "src/temp/" \
     -i "src/temp/config.json"
```

### Override Default Exclusions

```bash
# Include hidden files
llmd --with-hidden
# Or: llmd --include-hidden

# Include binary files
llmd --with-binary
# Or: llmd --include-binary

# Include gitignored files
llmd --no-gitignore
# Or: llmd --include-gitignore

# Combine overrides
llmd --with-hidden --no-gitignore --with-binary
```

### Utility Options

```bash
# Verbose output (see which files are included/excluded)
llmd -v

# Quiet mode (errors only)
llmd -q

# Combine with other options
llmd -w "src/" -v --dry-run
```

## Configuration File

### Creating Templates

```bash
# Create default template (blacklist mode)
llmd init

# Create whitelist template
llmd init --whitelist

# Create blacklist template
llmd init --blacklist

# Create minimal template
llmd init --minimal
```

### Configuration Format (llm.md)

Place an `llm.md` file in your repository root:

#### Whitelist Configuration
```markdown
WHITELIST:
src/
lib/
*.py
*.md

OPTIONS:
output: docs/llm-context.md
respect_gitignore: true
include_hidden: false
include_binary: false

EXCLUDE:
**/__pycache__/
**/*.pyc

INCLUDE:
tests/fixtures/
.env.example
```

#### Blacklist Configuration
```markdown
BLACKLIST:
tests/
coverage/
*.log
tmp/

OPTIONS:
output: llm-context.md
respect_gitignore: true
include_hidden: false
include_binary: false

INCLUDE:
tests/fixtures/
tests/test_utils.py
```

### Processing Order with Configuration

1. Mode patterns (WHITELIST/BLACKLIST section)
2. EXCLUDE section patterns
3. INCLUDE section patterns (highest priority)

### CLI Override Behavior

- CLI mode flags (`-w`/`-b`) completely override `llm.md` configuration
- CLI behavior flags override OPTIONS settings
- CLI output path (`-o`) overrides OPTIONS output setting

## Command Reference

### Main Command

```
llmd [PATH] [OPTIONS]
```

#### Arguments
- `PATH` - Repository path (optional, defaults to current directory)

#### Options
| Option | Description |
|--------|-------------|
| `-o, --output PATH` | Output file path (default: `./llm-context.md`) |
| `--github URL` | Clone and process GitHub repository |
| `-w, --whitelist PATTERN` | Use whitelist mode with pattern (repeatable) |
| `-b, --blacklist PATTERN` | Use blacklist mode with pattern (repeatable) |
| `-i, --include PATTERN` | Include files matching pattern (repeatable) |
| `-e, --exclude PATTERN` | Exclude files matching pattern (repeatable) |
| `--include-gitignore` | Include gitignored files |
| `--no-gitignore` | Alias for `--include-gitignore` |
| `--include-hidden` | Include hidden files |
| `--with-hidden` | Alias for `--include-hidden` |
| `--include-binary` | Include binary files |
| `--with-binary` | Alias for `--include-binary` |
| `-v, --verbose` | Show detailed processing information |
| `-q, --quiet` | Suppress non-error output |
| `--dry-run` | Preview files without generating output |
| `--version` | Show version information |
| `--help` | Show help message |

### Init Command

```
llmd init [OPTIONS]
```

#### Options
| Option | Description |
|--------|-------------|
| `-w, --whitelist` | Create whitelist mode template |
| `-b, --blacklist` | Create blacklist mode template |
| `--minimal` | Create minimal template |
| `--help` | Show help message |

## Pattern Matching

### Syntax
- `*` - matches any characters except `/`
- `**` - matches any characters including `/` (recursive)
- `?` - matches any single character
- `[abc]` - matches any character in brackets
- `[!abc]` - matches any character NOT in brackets
- `{a,b}` - matches either pattern a or b

### Examples
| Pattern | Matches |
|---------|---------|
| `*.py` | All Python files in root directory |
| `**/*.py` | All Python files recursively |
| `src/` | Everything in src directory |
| `test_*.py` | Files starting with test_ and ending in .py |
| `data/????.csv` | CSV files with 4-character names in data/ |
| `*.{js,ts}` | All JavaScript and TypeScript files |

## Output Path Resolution

### From Command Line
- Absolute paths used as-is: `/home/user/output.md`
- Relative paths resolved from current directory: `docs/output.md`

### From llm.md OPTIONS
- Just filename: resolved relative to `llm.md` location
- Relative path: resolved from current working directory
- Absolute path: used as-is
- Directory only (ends with `/`): appends `llm-context.md`

### Examples
```yaml
# In /project/llm.md:
output: context.md           # → /project/context.md
output: docs/context.md      # → /current/working/dir/docs/context.md
output: /tmp/context.md      # → /tmp/context.md
output: output/              # → /current/working/dir/output/llm-context.md
```

## Default Behaviors

### When No Configuration Exists
- Mode: Blacklist (include all files by default)
- Exclude: gitignored files, hidden files, binary files
- Output: `./llm-context.md`

### Binary File Extensions
Automatically excluded unless `--with-binary` is used:
- Images: `.jpg .jpeg .png .gif .bmp .ico .svg`
- Documents: `.pdf .doc .docx .xls .xlsx .ppt .pptx`
- Archives: `.zip .tar .gz .bz2 .7z .rar`
- Executables: `.exe .dll .so .dylib .bin .obj`
- Media: `.mp3 .mp4 .avi .mov .wav .flac`
- Fonts: `.ttf .otf .woff .woff2 .eot`
- Compiled: `.pyc .pyo .class .o .a`
- Databases: `.db .sqlite .sqlite3`

### Always Skipped Directories
- `.git` (for safety)
- `__pycache__`, `node_modules`
- `.venv`, `venv`, `env`, `.env`
- `.tox`, `.pytest_cache`, `.mypy_cache`
- `dist`, `build`, `target`
- `.next`, `.nuxt`

## Troubleshooting

### Common Issues

#### Files Not Included
```bash
# Check what files would be included
llmd --dry-run -v

# Ensure files aren't gitignored
llmd --no-gitignore --dry-run

# Include hidden files
llmd --with-hidden --dry-run
```

#### Pattern Not Working
```bash
# Use verbose mode to see pattern matching
llmd -w "src/**/*.py" -v --dry-run

# Check pattern syntax (use quotes to prevent shell expansion)
llmd -w '*.{js,ts}' -v --dry-run
```

#### GitHub Clone Failing
```bash
# Verify Git is installed
git --version

# Check URL format
llmd --github https://github.com/owner/repo  # No trailing slash

# For private repos, ensure SSH keys are configured
llmd --github git@github.com:owner/repo.git
```

### For AI Agents

When using llmd programmatically:

1. **Always use explicit mode**: Specify `-w` or `-b` to avoid ambiguity
2. **Quote patterns**: Prevent shell expansion with quotes
3. **Use absolute paths**: More predictable than relative paths
4. **Check dry-run first**: Verify file selection before generating
5. **Parse errors**: Check stderr for error messages

Example robust usage:
```bash
# Explicit, quoted, with verification
llmd /absolute/path/to/repo \
     -w '**/*.py' \
     -w '**/*.md' \
     -e '**/test_*.py' \
     -o /tmp/context.md \
     --dry-run \
     && llmd /absolute/path/to/repo \
        -w '**/*.py' \
        -w '**/*.md' \
        -e '**/test_*.py' \
        -o /tmp/context.md
```