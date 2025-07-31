# Product Requirements Document: llmd

## Overview

`llmd` is a command-line tool that generates consolidated markdown files containing code repository contents for use with Large Language Models (LLMs). It provides flexible file filtering through whitelist/blacklist patterns, respecting gitignore rules and binary file detection by default.

## Core Concepts

### Modes

The tool operates in two mutually exclusive modes:

1. **WHITELIST Mode**: Start with no files, explicitly add what you want
2. **BLACKLIST Mode**: Start with all files, explicitly remove what you don't want

### Pattern Processing

Patterns are processed sequentially:
- The mode determines the initial file set
- Subsequent EXCLUDE patterns remove files
- Subsequent INCLUDE patterns add files back (rescue)

### Default Exclusions

Unless explicitly overridden, the tool always excludes:
- Files matching `.gitignore` patterns
- Hidden files (starting with `.`)
- Binary files (common non-text extensions)

## Configuration File Format (llm.md)

### Basic Structure

```markdown
# Mode declaration (REQUIRED: must be first non-comment line)
WHITELIST:  # or BLACKLIST:

# Patterns for the implicit first section
pattern1
pattern2
dir/
*.extension

# Optional configuration
OPTIONS:
output: my-context.md
respect_gitignore: true    # default: true
include_hidden: false      # default: false  
include_binary: false      # default: false

# Explicit sections for refinement
EXCLUDE:
pattern3
pattern4

INCLUDE:
pattern5
```

### Pattern Syntax

- Uses gitignore-style glob patterns
- `*` matches any characters except `/`
- `**` matches any characters including `/`
- Patterns are relative to repository root
- Directory patterns should end with `/` for clarity

### Examples

#### Whitelist Mode
```markdown
WHITELIST:
src/
lib/
package.json
*.md

EXCLUDE:
src/__pycache__/
src/vendor/
**/*.test.js

INCLUDE:
src/vendor/our-patches/
```

#### Blacklist Mode
```markdown
BLACKLIST:
tests/
node_modules/
coverage/
*.log
.git/

INCLUDE:
tests/fixtures/
tests/utils.py
debug.log
```

## CLI Specification

### Basic Usage

```bash
# Default behavior (no llm.md): include all files with default exclusions
llmd .
llmd /path/to/repo

# Use llm.md if it exists
llmd .

# Override with CLI patterns
llmd . --whitelist "src/" "lib/"
llmd . --blacklist "tests/" "*.log"
```

### Command Synopsis

```bash
llmd [PATH] [OPTIONS]

PATH: Repository path (default: current directory)
```

### Mode Options (mutually exclusive)

```bash
-w, --whitelist PATTERN...   Use whitelist mode with specified patterns
-b, --blacklist PATTERN...   Use blacklist mode with specified patterns
```

### Pattern Refinement Options

Only valid when using `-w` or `-b`:

```bash
-e, --exclude PATTERN        Exclude files matching pattern (can be repeated)
-i, --include PATTERN        Include files matching pattern (can be repeated)
```

### Output Options

```bash
-o, --output PATH            Output file or directory path
                            If PATH ends with /, append default filename
                            Default: ./llm-context.md
```

### Behavior Control Options

```bash
--include-gitignore          Include files matched by .gitignore
--include-hidden             Include hidden files (starting with .)
--include-binary             Include binary files

--exclude-gitignore          Exclude files matched by .gitignore (default)
--exclude-hidden             Exclude hidden files (default)
--exclude-binary             Exclude binary files (default)

# Aliases
--no-gitignore              Same as --include-gitignore
--with-hidden               Same as --include-hidden
--with-binary               Same as --include-binary
```

### Utility Options

```bash
-v, --verbose               Show detailed processing information
-q, --quiet                 Suppress non-error output
--dry-run                   Show files that would be included without writing
-h, --help                  Show help message
--version                   Show version information
```

### Init Command

```bash
llmd init [OPTIONS]         Create llm.md template in current directory

Options:
  -w, --whitelist          Create whitelist mode template
  -b, --blacklist          Create blacklist mode template
  --minimal                Create minimal template
```

## Processing Logic

### File Discovery Order

1. If `-w` or `-b` flags are used, ignore any llm.md file
2. If no mode flags and llm.md exists, use its configuration
3. If no mode flags and no llm.md, use implicit blacklist mode with no explicit exclusions

### Pattern Processing Order

1. **Determine initial file set based on mode**:
   - WHITELIST: Start with empty set
   - BLACKLIST: Start with all files in repository

2. **Apply default exclusions** (unless overridden):
   - Remove files matching `.gitignore`
   - Remove hidden files
   - Remove binary files

3. **Process mode patterns**:
   - WHITELIST: Add files matching patterns
   - BLACKLIST: Remove files matching patterns

4. **Process EXCLUDE sections**: Remove matching files

5. **Process INCLUDE sections**: Add matching files (force include)

### Precedence Rules

1. CLI mode flags (`-w`/`-b`) completely override llm.md
2. Individual option flags override corresponding OPTIONS in llm.md
3. INCLUDE patterns can force-include files that would otherwise be excluded
4. Pattern order matters - later patterns can override earlier ones

## Default Behaviors

### When No Configuration Exists

```bash
llmd .
# Equivalent to:
# llmd . --blacklist --exclude-gitignore --exclude-hidden --exclude-binary
```

- Includes all repository files
- Excludes files matching `.gitignore`
- Excludes hidden files
- Excludes binary files
- Outputs to `./llm-context.md`

### Binary File Detection

Files with these extensions are considered binary:
- Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.ico`, `.svg`
- Documents: `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`
- Archives: `.zip`, `.tar`, `.gz`, `.bz2`, `.7z`, `.rar`
- Executables: `.exe`, `.dll`, `.so`, `.dylib`, `.bin`, `.obj`
- Media: `.mp3`, `.mp4`, `.avi`, `.mov`, `.wav`, `.flac`
- Fonts: `.ttf`, `.otf`, `.woff`, `.woff2`, `.eot`
- Compiled: `.pyc`, `.pyo`, `.class`, `.o`, `.a`
- Databases: `.db`, `.sqlite`, `.sqlite3`

### Always Skipped Directories

These directories are skipped during traversal (unless force-included):
- `.git`
- `__pycache__`
- `node_modules`
- `.venv`, `venv`, `env`, `.env`
- `.tox`, `.pytest_cache`, `.mypy_cache`
- `dist`, `build`, `target`
- `.next`, `.nuxt`

## Output Format

The generated markdown file contains:

```markdown
# LLM Context for [repository-name]

Generated on: YYYY-MM-DD HH:MM:SS
Repository: `/full/path/to/repository`
Total files: N

---

## Table of Contents

1. [path/to/file1.ext](#path-to-file1-ext)
2. [path/to/file2.ext](#path-to-file2-ext)
...

## path/to/file1.ext {#path-to-file1-ext}

```language
[file contents]
```

## path/to/file2.ext {#path-to-file2-ext}

```language
[file contents]
```
```

## Usage Examples

### Common Scenarios

#### 1. Default Usage (No Configuration)
```bash
# Include entire repository with default exclusions
llmd .

# Specify output location
llmd . -o ../docs/context.md
```

#### 2. Quick Whitelist
```bash
# Just source code
llmd . -w "src/" "lib/" -e "**/*.test.js"

# Include configs and docs
llmd . -w "src/" "*.json" "*.md" -e "**/node_modules/"
```

#### 3. Quick Blacklist
```bash
# Everything except tests and builds
llmd . -b "tests/" "dist/" "coverage/"

# Exclude but rescue specific files
llmd . -b "**/*.log" -i "debug.log" "error.log"
```

#### 4. Override Default Exclusions
```bash
# Include hidden files
llmd . --with-hidden

# Include everything (hidden, binary, gitignored)
llmd . --no-gitignore --with-hidden --with-binary
```

### With Configuration File

#### Project Structure
```
myproject/
├── llm.md
├── src/
├── tests/
├── docs/
└── ...
```

#### llm.md
```markdown
WHITELIST:
src/
docs/
README.md

OPTIONS:
output: project-context.md
include_hidden: true

EXCLUDE:
**/__pycache__/
**/*.test.js
```

#### Usage
```bash
# Use configuration
llmd

# Override output only
llmd -o /tmp/context.md

# Complete override
llmd -b "tests/" -o test-context.md
```

## Error Conditions

1. **Invalid mode combination**: Using both `-w` and `-b`
2. **Invalid output path**: Output directory doesn't exist
3. **No read permissions**: Cannot access repository files
4. **Invalid patterns**: Malformed glob patterns
5. **Invalid llm.md**: Missing mode declaration or invalid syntax

## Implementation Notes

1. Patterns use gitignore-style matching (via pathspec library)
2. File encoding assumes UTF-8, with fallback for binary detection
3. Large repositories may require progress indication
4. Symbolic links are not followed
5. Empty directories are not included in output