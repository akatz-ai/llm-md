# llmd

A command-line tool that generates consolidated markdown files containing code repository contents for use with Large Language Models (LLMs). It provides flexible file filtering through whitelist/blacklist patterns, respects gitignore rules, and includes GitHub remote repository support.

## Features

- **Flexible Filtering**: Whitelist and blacklist modes with pattern refinement
- **GitHub Integration**: Clone and process remote GitHub repositories
- **Smart Defaults**: Automatically excludes gitignored, hidden, and binary files
- **Configuration File**: Optional `llm.md` configuration file support
- **Template Generation**: Built-in `init` command to create configuration templates
- **Pattern Matching**: Full gitignore-style glob pattern support
- **Dry Run Mode**: Preview files without generating output
- **Multiple Output Formats**: Generates structured markdown with table of contents
- **Binary Detection**: Automatically detects and skips binary files

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

# Generate context for specific repository
llmd /path/to/repo

# Process GitHub repository
llmd --github https://github.com/user/repo

# Create configuration template
llmd init --whitelist
```

## Usage

### Basic Usage

```bash
# Use current directory with default settings
llmd

# Specify repository path
llmd /path/to/repo

# Specify output file
llmd /path/to/repo -o my-context.md

# Preview files without generating output
llmd /path/to/repo --dry-run
```

### GitHub Integration

```bash
# Process GitHub repository directly
llmd --github https://github.com/user/repo

# GitHub with custom output
llmd --github https://github.com/user/repo -o github-context.md

# GitHub with filtering
llmd --github https://github.com/user/repo -w "*.py" -w "*.md"

# SSH URLs supported
llmd --github git@github.com:user/repo.git
```

### Filtering Modes

#### Whitelist Mode (Explicit Inclusion)
```bash
# Include only specific patterns
llmd . -w "src/" -w "*.md"

# Whitelist with additional refinement
llmd . -w "src/" -e "**/*.test.js" -i "src/important.test.js"
```

#### Blacklist Mode (Explicit Exclusion)
```bash
# Exclude specific patterns
llmd . -b "tests/" -b "*.log"

# Blacklist with refinement
llmd . -b "**/*.test.*" -i "tests/fixtures/"
```

### Pattern Refinement

Use `-i`/`--include` and `-e`/`--exclude` with mode flags for fine control:

```bash
# Whitelist with exceptions
llmd . -w "src/" -e "src/vendor/" -i "src/vendor/our-patches/"

# Blacklist with exceptions
llmd . -b "tests/" -i "tests/fixtures/" -i "tests/utils.py"
```

### Behavior Control

```bash
# Include hidden files
llmd . --with-hidden

# Include binary files
llmd . --with-binary

# Include gitignored files
llmd . --no-gitignore

# Combine multiple overrides
llmd . --with-hidden --with-binary --no-gitignore
```

### Utility Options

```bash
# Verbose output
llmd . -v

# Quiet mode (errors only)
llmd . -q

# Preview mode
llmd . --dry-run
```

## Configuration File (llm.md)

Create an `llm.md` file in your repository root to define default filtering rules.

### Generate Templates

```bash
# Create whitelist template
llmd init --whitelist

# Create blacklist template  
llmd init --blacklist

# Create minimal template
llmd init --minimal

# Create default template
llmd init
```

### Configuration Format

#### Whitelist Mode
```markdown
WHITELIST:
src/
lib/
*.md
package.json

OPTIONS:
output: my-context.md
respect_gitignore: true
include_hidden: false
include_binary: false

EXCLUDE:
src/__pycache__/
**/*.test.js

INCLUDE:
tests/fixtures/
important.test.js
```

#### Blacklist Mode
```markdown
BLACKLIST:
tests/
node_modules/
coverage/
*.log
.git/

OPTIONS:
output: project-context.md
respect_gitignore: true
include_hidden: false
include_binary: false

INCLUDE:
tests/fixtures/
debug.log
```

### Pattern Syntax

- `*` - matches any characters except `/`
- `**` - matches any characters including `/` (recursive)
- `?` - matches any single character
- `[abc]` - matches any character in brackets
- `pattern/` - matches directories
- Patterns are relative to repository root

### Processing Order

1. **Mode determines initial set**: WHITELIST (empty) or BLACKLIST (all files)
2. **Apply default exclusions**: gitignore, hidden files, binary files (unless overridden)
3. **Apply mode patterns**: Add (whitelist) or remove (blacklist) files
4. **Apply EXCLUDE sections**: Remove additional files
5. **Apply INCLUDE sections**: Force include files (highest priority)

## Command Reference

### Main Command

```bash
llmd [PATH] [OPTIONS]
```

**Arguments:**
- `PATH` - Repository path (default: current directory)

**Options:**
- `-o, --output PATH` - Output file path (default: ./llm-context.md)
- `--github URL` - Clone and process GitHub repository
- `-w, --whitelist PATTERN` - Use whitelist mode with patterns
- `-b, --blacklist PATTERN` - Use blacklist mode with patterns
- `-i, --include PATTERN` - Include additional files (can be repeated)
- `-e, --exclude PATTERN` - Exclude additional files (can be repeated)
- `--include-gitignore` / `--exclude-gitignore` - Control gitignore handling
- `--no-gitignore` - Alias for --include-gitignore
- `--include-hidden` / `--exclude-hidden` - Control hidden file handling
- `--with-hidden` - Alias for --include-hidden
- `--include-binary` / `--exclude-binary` - Control binary file handling
- `--with-binary` - Alias for --include-binary
- `-v, --verbose` - Enable verbose output
- `-q, --quiet` - Suppress non-error output
- `--dry-run` - Show files without generating output
- `--version` - Show version information
- `--help` - Show help message

### Init Command

```bash
llmd init [OPTIONS]
```

**Options:**
- `-w, --whitelist` - Create whitelist mode template
- `-b, --blacklist` - Create blacklist mode template  
- `--minimal` - Create minimal template
- `--help` - Show help message

## Examples

### Common Workflows

#### Documentation Generation
```bash
# Include only documentation and source
llmd . -w "src/" -w "docs/" -w "*.md" -w "*.rst"
```

#### Code Review Context
```bash
# Exclude tests and build artifacts
llmd . -b "tests/" -b "dist/" -b "build/" -b "coverage/"
```

#### Python Project
```bash
# Python files with configs
llmd . -w "**/*.py" -w "*.yaml" -w "*.toml" -w "requirements*.txt"
```

#### JavaScript/TypeScript Project
```bash
# Source code only
llmd . -w "src/" -w "*.json" -e "**/*.test.*" -e "**/node_modules/"
```

#### Configuration Files Only
```bash
# Just configuration
llmd . -w "*.json" -w "*.yaml" -w "*.toml" -w "*.ini" -w "*.env*"
```

### Advanced Usage

#### Multiple Repositories
```bash
# Process and compare multiple repos
llmd --github https://github.com/user/repo1 -o repo1-context.md
llmd --github https://github.com/user/repo2 -o repo2-context.md
```

#### Complex Filtering
```bash
# Include source but exclude tests, then rescue specific test files
llmd . -w "src/" -e "**/*.test.*" -i "src/critical.test.js" -i "src/fixtures/"
```

#### Override Configuration
```bash
# Override llm.md settings with CLI
llmd . -b "additional-exclude/" --with-hidden --no-gitignore
```

## Output Format

The generated markdown includes:

1. **Header**: Repository information, generation timestamp, file count
2. **Table of Contents**: Clickable links to each file section
3. **File Sections**: Each file's content with syntax highlighting

Example output structure:
```markdown
# LLM Context for my-project

Generated on: 2024-01-15 14:30:00
Repository: /path/to/my-project
Total files: 42

---

## Table of Contents

1. [src/main.py](#src-main-py)
2. [src/utils.py](#src-utils-py)
...

## src/main.py

```python
# File contents here
```

## src/utils.py

```python
# File contents here
```
```

## Default Behaviors

### No Configuration
When no `llm.md` exists and no CLI mode flags are used:
- Includes all repository files
- Excludes gitignored files
- Excludes hidden files (starting with `.`)
- Excludes binary files
- Outputs to `./llm-context.md`

### Binary File Detection
Files with these extensions are automatically excluded:
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.ico`, `.svg`
- **Documents**: `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`  
- **Archives**: `.zip`, `.tar`, `.gz`, `.bz2`, `.7z`, `.rar`
- **Executables**: `.exe`, `.dll`, `.so`, `.dylib`, `.bin`, `.obj`
- **Media**: `.mp3`, `.mp4`, `.avi`, `.mov`, `.wav`, `.flac`
- **Fonts**: `.ttf`, `.otf`, `.woff`, `.woff2`, `.eot`
- **Compiled**: `.pyc`, `.pyo`, `.class`, `.o`, `.a`
- **Databases**: `.db`, `.sqlite`, `.sqlite3`

### Always Skipped Directories
These directories are skipped unless explicitly included:
- `.git`, `__pycache__`, `node_modules`
- `.venv`, `venv`, `env`, `.env`
- `.tox`, `.pytest_cache`, `.mypy_cache`
- `dist`, `build`, `target`
- `.next`, `.nuxt`

## Error Handling

Common error conditions:
- **Invalid mode combination**: Using both `-w` and `-b` flags
- **Invalid patterns**: Malformed glob patterns
- **Access denied**: Insufficient permissions to read files
- **Network issues**: GitHub repository cloning failures
- **Invalid URLs**: Malformed GitHub repository URLs

## Contributing

This tool is part of a larger project. See the repository for contribution guidelines.

## License

MIT