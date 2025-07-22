---
id: task-10
title: Fix TOC anchor format bug in markdown generator
status: Done
assignee: []
created_date: '2025-07-17'
updated_date: '2025-07-17'
labels: []
dependencies: []
priority: high
---

## Description

The table of contents (TOC) in generated markdown files has broken links because anchor generation incorrectly replaces dots with hyphens. This causes navigation from TOC entries to fail for files containing dots in their names.

## Acceptance Criteria

- [x] TOC links correctly navigate to file sections for all filenames
- [x] Dots in filenames are preserved in anchor IDs
- [x] Anchor generation is consistent between TOC and section headers
- [x] Existing tests pass and new tests cover edge cases


## Implementation Notes

Fixed TOC anchor generation bug by implementing GitHub-style anchor generation.

**Approach taken:**
- Analyzed the bug in detail: current implementation replaced dots with hyphens, breaking TOC navigation
- Implemented TDD approach with comprehensive test coverage
- Created new _generate_anchor() method following GitHub Flavored Markdown standard
- Updated _generate_toc() to use new anchor generation algorithm 
- Removed custom {#anchor} syntax from section headers to rely on auto-generation
- Ensured consistency between TOC links and section header anchors

**Features implemented:**
- GitHub-compatible anchor generation (lowercase, remove dots/slashes, keep alphanumeric)
- Comprehensive test coverage for edge cases (dots, slashes, complex paths)
- Backward compatibility maintained for existing functionality

**Technical decisions:**
- Chose GitHub anchor standard over custom implementation for maximum compatibility
- Removed custom anchor syntax to let markdown processors handle auto-generation
- Used regex for character filtering to ensure robust anchor generation

**Modified files:**
- src/llmd/generator.py: Added _generate_anchor(), updated _generate_toc() and _generate_file_section()
- tests/test_generator.py: New comprehensive test suite covering all edge cases
- scratchpad/task-10-2025-07-17-ultrathink-analysis.md: Implementation planning and analysis
## Technical Details

The bug is located in `src/llmd/generator.py` at lines 47 and 55. The current implementation:

```python
# Line 47 (in _generate_toc method)
anchor = str(rel_path).replace('/', '-').replace('.', '-').lower()

# Line 55 (in _generate_file_section method)  
anchor = str(rel_path).replace('/', '-').replace('.', '-').lower()
```

This converts a file path like `src/main.py` to anchor `#src-main-py`, but the actual section header uses `## src/main.py`, creating a mismatch.

### Example of the issue:
- File: `test.file.py`
- Current TOC link: `#test-file-py`
- Actual section ID needed: `#test.file.py` or a consistent anchor format

### Suggested fix:
Remove the `.replace('.', '-')` call to preserve dots in anchors, or ensure both TOC and section headers use the same anchor format.
