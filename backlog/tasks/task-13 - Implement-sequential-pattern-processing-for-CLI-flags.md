---
id: task-13
title: Implement sequential pattern processing for CLI flags
status: To Do
assignee: []
created_date: '2025-07-17'
labels: [enhancement, cli, patterns]
dependencies: [task-11]
priority: high
---

## Description

The current implementation treats `-e` and `-i` CLI flags as having simple precedence rules (INCLUDE always overrides EXCLUDE), but the PRD specifies that patterns should be processed sequentially where order matters. Users should be able to build complex file sets by chaining include/exclude operations in order.

## Acceptance Criteria

- [ ] CLI preserves the order of `-e` and `-i` flags
- [ ] Patterns are processed sequentially, not as global precedence rules
- [ ] Sequential processing works for examples like:
  - `llmd -w src/ -e src/*.pyc` (start with src/, remove .pyc files)
  - `llmd -w src/ -e src/random/ -i src/random/important-file.txt` (start with src/, remove random/, rescue important file)
  - `llmd -b tests/ -i tests/integration/ -e tests/integration/*.pyc` (exclude tests/, rescue integration/, remove .pyc from integration/)
- [ ] Sequential processing can continue indefinitely (ad-infinitum as user described)
- [ ] Legacy llm.md files continue to work with current precedence rules
- [ ] New mode-based llm.md files use proper sequential section processing
- [ ] All existing tests continue to pass
- [ ] New tests validate sequential processing behavior

## Technical Details

### Current Problem
Click CLI framework groups `-e` and `-i` flags separately into tuples, losing the order information needed for sequential processing.

### Potential Solutions
1. **Custom Click callback**: Use a custom callback to capture flags in order
2. **Single combined flag**: Replace `-e` and `-i` with a single flag like `--pattern exclude:*.pyc --pattern include:important.txt`
3. **Context preservation**: Modify Click setup to preserve argument order

### Implementation Requirements
- CLI interface changes must be backward compatible where possible
- Sequential processing should apply to CLI mode only (when `-w` or `-b` is used)
- Legacy INCLUDE/EXCLUDE behavior for llm.md files should remain unchanged initially
- Error handling for invalid pattern sequences

### Related Code Locations
- `src/llmd/cli.py` - CLI argument parsing and mode setup
- `src/llmd/scanner.py` - Pattern processing logic
- `src/llmd/parser.py` - CLI pattern storage and application
- `tests/test_cli_modes.py` - CLI behavior tests
- `tests/test_patterns.py` - Pattern processing tests

## Implementation Plan

1. Research Click options for preserving argument order
2. Design new CLI pattern processing architecture
3. Implement sequential pattern processing engine
4. Update CLI argument handling to preserve order
5. Add comprehensive tests for sequential processing
6. Update documentation to reflect new capabilities
7. Ensure backward compatibility with existing usage

## Implementation Notes

This task builds on task-11 (ONLY pattern removal) and addresses the sequential processing requirement identified during that implementation.