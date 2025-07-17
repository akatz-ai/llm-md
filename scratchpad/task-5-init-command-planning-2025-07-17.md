# Task 5 Implementation Planning - llmd init Command
## Timestamp: 2025-07-17 Initial Planning
## Task: Implement llmd init Command with Template Generation
## Status: 0% - Planning Phase

## Deep Analysis of Requirements

### Core Functionality
From the PRD and task description, the `llmd init` command needs to:

1. **Create llm.md template files** - The primary function
2. **Support multiple template types** via command line flags
3. **Graceful error handling** when llm.md already exists
4. **Integration with existing CLI** via Click framework

### Template Types Analysis

Based on PRD examples, I need to support:

1. **Default template** (when no flags specified)
   - Should probably be blacklist mode as it's more intuitive for beginners
   - Include common patterns that users typically want to exclude

2. **Whitelist template** (-w/--whitelist flag)
   - Start with WHITELIST: mode
   - Include common source code patterns
   - Show example EXCLUDE/INCLUDE sections

3. **Blacklist template** (-b/--blacklist flag)  
   - Start with BLACKLIST: mode
   - Include common exclusion patterns
   - Show example INCLUDE section for rescue patterns

4. **Minimal template** (--minimal flag)
   - Just the mode declaration and minimal examples
   - No complex patterns or extensive OPTIONS

### Template Format Requirements

From PRD section "Configuration File Format (llm.md)":

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

### CLI Integration Analysis

Current CLI structure (from codebase-map.md):
- Main entry point: `src/llmd/cli.py`
- Uses Click framework
- Need to add `init` subcommand

### Implementation Plan

#### Phase 1: CLI Structure Setup
1. **Modify cli.py** to add `init` subcommand
   - Add @click.group() if not already present
   - Add init subcommand with proper options
   - Handle mutually exclusive flags (-w, -b, --minimal)

#### Phase 2: Template Content Design
1. **Create template content constants/functions**
   - Default blacklist template
   - Whitelist template 
   - Blacklist template
   - Minimal template
   - Each should follow exact PRD format

#### Phase 3: File Generation Logic
1. **Implement template generation function**
   - Check if llm.md already exists (fail gracefully)
   - Generate appropriate template based on flags
   - Write to llm.md in current directory
   - Provide user feedback

#### Phase 4: Error Handling
1. **Implement proper error cases**
   - File already exists
   - Write permissions issues
   - Invalid flag combinations

#### Phase 5: Help Integration
1. **Ensure help text is proper**
   - init command shows in main help
   - init subcommand has its own help
   - Flag descriptions match PRD

### Template Content Design Details

#### Default Template (Blacklist Mode)
Should include common exclusions that most projects want:
```markdown
BLACKLIST:
tests/
node_modules/
__pycache__/
.git/
dist/
build/
coverage/
*.log
*.tmp

OPTIONS:
output: llm-context.md
respect_gitignore: true
include_hidden: false
include_binary: false

INCLUDE:
README.md
```

#### Whitelist Template  
Should include common source patterns:
```markdown
WHITELIST:
src/
lib/
*.py
*.js
*.ts
*.md
package.json
pyproject.toml

OPTIONS:
output: llm-context.md
respect_gitignore: true
include_hidden: false
include_binary: false

EXCLUDE:
**/__pycache__/
**/*.test.js
**/*.test.py

INCLUDE:
tests/fixtures/
```

#### Blacklist Template
Similar to default but with more comprehensive patterns:
```markdown
BLACKLIST:
tests/
node_modules/
__pycache__/
.git/
dist/
build/
coverage/
*.log
*.tmp
.env
.venv/
venv/

OPTIONS:
output: llm-context.md
respect_gitignore: true
include_hidden: false
include_binary: false

INCLUDE:
tests/fixtures/
debug.log
```

#### Minimal Template
Just the basics:
```markdown
WHITELIST:
src/

OPTIONS:
output: llm-context.md
```

### Technical Implementation Details

#### CLI Flag Handling
- Use Click's mutually exclusive groups for -w/-b/--minimal
- Default behavior when no flags specified
- Proper error messages for invalid combinations

#### File Operations
- Use pathlib for cross-platform path handling
- Check current working directory for llm.md
- Atomic file writing (write to temp, then rename)
- Proper error handling for filesystem issues

#### User Experience
- Clear success messages
- Helpful error messages
- Consistent with existing CLI patterns

### Testing Strategy (TDD Approach)

#### Test Cases Needed
1. **Basic functionality tests**
   - `llmd init` creates default template
   - `llmd init -w` creates whitelist template
   - `llmd init -b` creates blacklist template
   - `llmd init --minimal` creates minimal template

2. **Error handling tests**
   - Fails when llm.md already exists
   - Handles write permission errors
   - Rejects invalid flag combinations

3. **Template content tests**
   - Generated templates have correct format
   - Templates match PRD specifications
   - All required sections present

4. **CLI integration tests**
   - Help text includes init command
   - init --help works properly
   - Command appears in main help

### File Modifications Required

1. **src/llmd/cli.py** - Add init subcommand and logic
2. **tests/unit/** - Add test file for init command tests
3. Possibly new module for template content if cli.py gets too large

### Dependencies
- No new external dependencies needed
- Uses existing Click framework
- Uses standard library pathlib, os modules

This plan provides a comprehensive approach to implementing the init command that fully satisfies the PRD requirements and acceptance criteria.