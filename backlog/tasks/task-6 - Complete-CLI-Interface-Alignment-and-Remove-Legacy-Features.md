---
id: task-6
title: Complete CLI Interface Alignment and Remove Legacy Features
status: To Do
assignee: []
created_date: '2025-07-16'
updated_date: '2025-07-16'
labels: []
dependencies: []
priority: medium
---

## Description

Clean up remaining CLI discrepancies to fully match PRD specification. Remove legacy options not in PRD and fix default behaviors to ensure complete alignment with the specification.

## Acceptance Criteria

- [ ] Make PATH argument optional (default to current directory)
- [ ] Fix default output path to './llm-context.md' instead of 'llm-context.md'
- [ ] Remove legacy -O/--only option (not in PRD)
- [ ] Remove -c/--config option (not in PRD)
- [ ] Update CLI help text to match PRD specification exactly
- [ ] Pattern refinement options (-e/-i) only work with mode flags as specified
- [ ] Default behavior when no llm.md exists matches PRD (implicit BLACKLIST)
- [ ] Update llm.md.example to use new mode-based format
- [ ] All CLI error messages match PRD error conditions
- [ ] CLI synopsis matches PRD: llmd [PATH] [OPTIONS]

## Implementation Notes

Successfully implemented all CLI interface alignment requirements. Removed legacy -c/--config and -O/--only options, made PATH argument optional with default to current directory, fixed default output path to './llm-context.md', enhanced dry-run output with detailed information, updated error messages to match PRD format, and updated llm.md.example to new mode-based format. All 8 new tests passing, full test suite (63 tests) passing, linter clean. Note: Multiple argument syntax 'llmd . -w "src/" "tests/"' requires separate flags due to Click limitations, current working syntax is 'llmd . -w "src/" -w "tests/"'.
