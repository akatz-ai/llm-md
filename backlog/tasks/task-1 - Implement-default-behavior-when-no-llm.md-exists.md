---
id: task-1
title: Implement default behavior when no llm.md exists
status: To Do
assignee: []
created_date: '2025-07-16'
updated_date: '2025-07-16'
labels: []
dependencies: []
---

## Description

The tool currently requires an llm.md configuration file to work properly. To improve usability, the tool should work out-of-the-box without requiring configuration. When no llm.md file exists, the tool should default to blacklist mode with no explicit exclusions, while still applying the standard default exclusions (gitignore, hidden files, binary files).

## Acceptance Criteria

- [x] CLI runs successfully when no llm.md file exists
- [x] Default behavior includes all files except gitignore hidden and binary files
- [x] Default output filename is llm-context.md in current directory
- [x] Scanner operates in blacklist mode with empty exclusion patterns
- [x] Default exclusions (gitignore hidden binary) are still applied
- [x] LlmMdParser constructor accepts default_mode parameter
- [x] Existing functionality with llm.md files remains unchanged
- [x] All existing tests pass
- [x] New tests cover default behavior scenarios

## Implementation Plan

1. Update LlmMdParser constructor to accept default_mode parameter\n2. Modify CLI to handle missing llm.md gracefully\n3. Update scanner to handle blacklist mode with no patterns\n4. Ensure default exclusions are preserved\n5. Add tests for default behavior\n6. Update documentation if needed

## Implementation Notes

Successfully implemented default behavior when no llm.md exists using TDD approach:

**Approach taken:**
- Used Test-Driven Development: wrote failing tests first, then implemented functionality
- Added default_mode parameter to LlmMdParser constructor 
- Created _setup_default_config() method to configure BLACKLIST mode with empty patterns
- Updated CLI to pass default_mode='BLACKLIST' when no llm.md file exists

**Features implemented:**
- LlmMdParser accepts optional default_mode parameter
- When no llm.md exists and default_mode provided, creates default configuration
- Default BLACKLIST mode with no explicit patterns (includes all files)
- Default exclusions still applied (gitignore, hidden files, binary files)
- Default output filename: llm-context.md
- Existing llm.md files override default_mode parameter

**Technical decisions:**
- Made default_mode optional parameter to maintain backward compatibility
- Only applies default when both config_path is None/missing AND default_mode is provided
- Used same mode-based format structure for consistency with new parser format
- CLI determines default_mode based on llm_config_path existence

**Modified files:**
- src/llmd/parser.py: Added default_mode parameter and _setup_default_config method
- src/llmd/cli.py: Added logic to pass default_mode when no llm.md exists
- tests/test_parser.py: Added comprehensive TDD tests for default behavior

All acceptance criteria met and tests passing.
