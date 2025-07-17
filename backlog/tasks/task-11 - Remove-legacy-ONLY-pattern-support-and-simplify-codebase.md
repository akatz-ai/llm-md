---
id: task-11
title: Remove legacy ONLY pattern support and simplify codebase
status: To Do
assignee: []
created_date: '2025-07-17'
labels: []
dependencies: []
priority: medium
---

## Description

The codebase contains legacy support for ONLY patterns from an older configuration format that is no longer needed with the new WHITELIST/BLACKLIST mode implementation. This backwards compatibility code adds unnecessary complexity and should be removed to simplify the codebase.

## Acceptance Criteria

- [ ] All ONLY pattern handling code is removed from parser.py
- [ ] All ONLY pattern handling code is removed from scanner.py
- [ ] CLI no longer accepts --only flag or processes ONLY patterns
- [ ] Legacy format parsing code is removed from LlmMdParser
- [ ] Tests for ONLY patterns are removed or updated
- [ ] Documentation no longer mentions ONLY patterns
- [ ] All tests pass after removal

## Technical Details

The legacy ONLY pattern support exists in multiple locations throughout the codebase:

### In `src/llmd/parser.py`:
- Lines 49-54: `only_patterns` and `cli_only` attributes
- Lines 271-272: Pattern parsing for ONLY sections
- Lines 278-280: `has_only_patterns()` method
- Lines 324-341: `matches_only()` method
- Line 133: Reference in `_might_have_includes_in_directory()`

### In `src/llmd/scanner.py`:
- Lines 66-80: `_scan_with_only()` method
- Lines 186-187: ONLY pattern check in `_scan_legacy()`
- Lines 120-121: ONLY pattern check in `_might_have_includes_in_directory()`
- Line 133: Reference to `cli_only`

### In `src/llmd/cli.py`:
- References to `cli_only` parameter in LlmMdParser initialization (lines 368, 379)

### Legacy format parsing to remove:
The entire `_parse_legacy_format()` method (lines 248-276 in parser.py) handles the old ONLY/INCLUDE/EXCLUDE format and can be removed along with its usage.

### Benefits of removal:
1. Simplifies pattern processing logic
2. Reduces code complexity and maintenance burden
3. Makes the codebase more aligned with the PRD specification
4. Removes confusion between old and new configuration formats
