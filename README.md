# llm-md

A CLI tool for generating LLM context from GitHub repositories. This tool scans through files in a repository and creates a single markdown file containing all relevant code, making it easy to provide context to Large Language Models.

## Features

- Automatically respects `.gitignore` patterns
- Automatically detects and uses `llm.md` configuration file in repository root
- Additional filtering via `llm.md` configuration file
- Generates table of contents for easy navigation
- Syntax highlighting for various programming languages
- Skips binary and non-text files automatically

## Installation

```bash
# Install using uv tool (for global cli setup)
uv tool install llm-md

# Or install directly
pip install llm-md
```

## Usage

Basic usage:
```bash
llm-md /path/to/repo
```

Specify output file:
```bash
llm-md /path/to/repo -o context.md
```

Override the llm.md configuration file:
```bash
llm-md /path/to/repo -c custom-llm.md
```

Verbose output:
```bash
llm-md /path/to/repo -v
```

## Configuration

### .gitignore

The tool automatically reads and respects `.gitignore` patterns in the repository root.

### llm.md

The tool automatically detects and uses an `llm.md` file if present in the repository root. You can override this by specifying a different configuration file with the `-c` option.

Create an `llm.md` file to control which files are included:

```
# Example llm.md

INCLUDE:
# If this section has patterns, ONLY these files will be included
src/**/*.py
docs/*.md

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

## Output Format

The generated markdown file includes:
1. Header with metadata (timestamp, repository path, file count)
2. Table of contents with links to each file section
3. Each file's content in a code block with appropriate syntax highlighting

## Example

```bash
# Generate context for the current directory (auto-detects llm.md if present)
llm-md .

# Generate context for a specific project
llm-md ~/projects/my-app -o my-app-context.md

# Use a different llm.md file than the one in the repository
llm-md ~/projects/my-app -c ~/configs/python-only.md

# Include only Python files (create llm.md in the repo)
echo "INCLUDE:\n**/*.py" > llm.md
llm-md .
```

## License

MIT