# llmd

A CLI tool for generating LLM context from GitHub repositories. This tool scans through files in a repository and creates a single markdown file containing all relevant code, making it easy to provide context to Large Language Models.

## Features

- Automatically respects `.gitignore` patterns
- Automatically detects and uses `llm.md` configuration file in repository root
- Additional filtering via `llm.md` configuration file
- Command-line include/exclude patterns with `--include` and `--exclude`
- Dry run mode to preview files without generating output
- Generates table of contents for easy navigation
- Syntax highlighting for various programming languages
- Skips binary and non-text files automatically

## Installation

```bash
# Install using uv tool (for global cli setup)
uv tool install llmd

# Or install directly
pip install llmd
```

## Usage

Basic usage:
```bash
llmd /path/to/repo
```

Specify output file:
```bash
llmd /path/to/repo -o context.md
```

Override the llm.md configuration file:
```bash
llmd /path/to/repo -c custom-llm.md
```

Include only specific file patterns (ignoring all exclusions):
```bash
llmd /path/to/repo --only "*.py" --only "*.js"
```

Include additional files that would normally be excluded:
```bash
llmd /path/to/repo --include ".github/**" --include "build/*.js"
```

Exclude specific file patterns:
```bash
llmd /path/to/repo --exclude "**/test_*.py" --exclude "*.log"
```

Preview files without generating output:
```bash
llmd /path/to/repo --dry-run
```

Verbose output:
```bash
llmd /path/to/repo -v
```

## Configuration

### .gitignore

The tool automatically reads and respects `.gitignore` patterns in the repository root.

### llm.md

The tool automatically detects and uses an `llm.md` file if present in the repository root. You can override this by specifying a different configuration file with the `-c` option.

Create an `llm.md` file to control which files are included:

```
# Example llm.md

ONLY:
# When present, ONLY these files are included, ignoring all exclusions
src/**/*.py
docs/*.md

INCLUDE:
# These patterns rescue files from exclusions (.gitignore, EXCLUDE, hidden files)
.github/workflows/*.yml
build/dist.js

EXCLUDE:
# These files will be excluded (in addition to .gitignore)
tests/**
*.test.js
```

Pattern syntax follows gitignore conventions:
- `*` matches any characters except `/`
- `**` matches any number of directories
- `?` matches any single character
- `[abc]` matches any character in the brackets
- `!` at the start negates the pattern

### Command-line Options

The pattern options allow you to control file inclusion/exclusion:

- `--only`/`-O`: Include ONLY files matching these patterns, ignoring all exclusions (can be specified multiple times)
- `--include`/`-i`: Rescue files matching these patterns from exclusions (can be specified multiple times)
- `--exclude`/`-e`: Exclude files matching these patterns (can be specified multiple times)
- `--dry-run`: Preview which files would be included without generating output

**Pattern precedence (highest to lowest):**
1. `ONLY` patterns (CLI or llm.md) - when present, ONLY these files are included
2. `INCLUDE` patterns - rescue files from exclusions (gitignore, EXCLUDE, hidden files)
3. `EXCLUDE` patterns - additional exclusions beyond gitignore
4. Default behavior - all files except gitignored, hidden, and binary files

**Priority rules:**
- CLI `--only` patterns override any ONLY patterns in `llm.md`
- CLI `--include` patterns override any INCLUDE patterns in `llm.md`
- CLI `--exclude` patterns are additive with `llm.md` EXCLUDE patterns

## Output Format

The generated markdown file includes:
1. Header with metadata (timestamp, repository path, file count)
2. Table of contents with links to each file section
3. Each file's content in a code block with appropriate syntax highlighting

## Examples

```bash
# Generate context for the current directory (auto-detects llm.md if present)
llmd .

# Generate context for a specific project
llmd ~/projects/my-app -o my-app-context.md

# Use a different llm.md file than the one in the repository
llmd ~/projects/my-app -c ~/configs/python-only.md

# Include only Python files, ignoring all exclusions
llmd . --only "*.py"

# Include only specific file types
llmd . -O "*.py" -O "*.js" -O "*.tsx"

# Rescue hidden files and gitignored files that match patterns
llmd . --include ".github/**" --include "build/dist.js"

# Exclude test files
llmd . --exclude "**/test_*.py" --exclude "**/*.test.js"

# Preview files that would be included
llmd . --dry-run --only "src/**/*.py"

# Use ONLY to get test files that would normally be excluded
llmd . --only "**/test_*.py" --only "**/*.test.js"

# Combine rescue patterns with excludes
llmd . --include ".env" --exclude "**/migrations/**"

# Include only Python files (create llm.md in the repo)
echo "INCLUDE:\n**/*.py" > llm.md
llmd .
```

## License

MIT