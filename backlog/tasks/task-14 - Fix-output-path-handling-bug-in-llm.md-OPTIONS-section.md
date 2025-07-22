---
id: task-14
title: Fix output path handling bug in llm.md OPTIONS section
status: To Do
assignee: []
created_date: '2025-07-17'
labels: []
dependencies: []
priority: medium
---

## Description

Currently the output path handling in llm.md has incorrect behavior for different path scenarios. Need to fix the logic to properly handle file names, paths, and default naming.
User notes:
Currently the llm.md file has an OPTIONS: category with an output: key 
where users can add the name of the file and path to output to. If there is no path and just a file 
name then it should be created or placed in the same dir as the llm.md. If there is a path it should
 be written there. If there is a path and no file name, then it should be written to that path with 
the default file name llm-context.md. This is a bug task

## Acceptance Criteria

- [x] Output with just filename creates file in same directory as llm.md
- [x] Output with path writes to specified path
- [x] Output with path but no filename uses default name llm-context.md
- [x] All path scenarios work correctly

## Implementation Notes

**Approach taken:**
Fixed the output path handling bug by implementing proper output path resolution and precedence logic in both the parser and CLI modules.

**Root cause identified:**
The CLI was completely ignoring the `output:` option from llm.md OPTIONS section. The option was being parsed correctly but never used - CLI always used its own `--output` parameter (default: `./llm-context.md`).

**Features implemented:**

1. **Added `resolve_output_path()` method to LlmMdParser** (`src/llmd/parser.py`):
   - Handles all path scenarios: filename-only, relative paths, absolute paths, directory-only
   - Resolves filename-only paths relative to llm.md directory
   - Resolves relative paths with directories relative to current working directory  
   - Uses absolute paths as-is
   - Appends default filename `llm-context.md` to directory-only paths (ending with `/`)

2. **Enhanced CLI output resolution logic** (`src/llmd/cli.py`):
   - Added detection of explicit CLI `--output` usage vs default value
   - Implemented proper precedence: CLI explicit > llm.md output > CLI default
   - Added verbose logging for output path selection

**Technical decisions:**
- Used string comparison to detect default CLI output value (`'./llm-context.md'` or `'llm-context.md'`)
- Chose to resolve filename-only paths relative to llm.md directory (not cwd) for better user experience
- Maintained backward compatibility - existing behavior unchanged when no llm.md options exist

**Modified files:**
- `src/llmd/parser.py` - Added `resolve_output_path()` method
- `src/llmd/cli.py` - Added output path resolution logic with proper precedence
- `tests/test_parser.py` - Added comprehensive test suite (11 new tests)

**Test coverage added:**
- Output option parsing from llm.md (4 tests)
- Path resolution for all scenarios (5 tests) 
- CLI integration with precedence rules (2 tests)

All tests pass and linter is clean. The fix properly handles all acceptance criteria scenarios.

