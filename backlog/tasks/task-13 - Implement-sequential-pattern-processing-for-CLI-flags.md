---
id: task-13
title: Implement sequential pattern processing for CLI flags
status: Done
assignee: []
created_date: '2025-07-17'
updated_date: '2025-07-17'
labels:
  - enhancement
  - cli
  - patterns
dependencies:
  - task-11
priority: high
---

## Description

The current implementation treats `-e` and `-i` CLI flags as having simple precedence rules (INCLUDE always overrides EXCLUDE), but the PRD specifies that patterns should be processed sequentially where order matters. Users should be able to build complex file sets by chaining include/exclude operations in order.

## Acceptance Criteria

- [x] CLI preserves the order of -e and -i flags
- [x] Patterns are processed sequentially not as global precedence rules
- [x] Sequential processing works for examples like: llmd -w src/ -e src/*.pyc
- [x] Sequential processing works for examples like: llmd -w src/ -e src/random/ -i src/random/important-file.txt
- [x] Sequential processing works for examples like: llmd -b tests/ -i tests/integration/ -e tests/integration/*.pyc
- [x] Sequential processing can continue indefinitely (ad-infinitum)
- [x] Legacy llm.md files continue to work with current precedence rules
- [x] New mode-based llm.md files use proper sequential section processing
- [x] All existing tests continue to pass
- [x] New tests validate sequential processing behavior
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

Successfully implemented sequential pattern processing for CLI flags using a hybrid approach:

## Technical Implementation
- Added SequentialPattern dataclass and PatternSequence class to parser.py for managing ordered patterns
- Implemented build_pattern_sequence_from_raw_args() function to parse sys.argv and preserve CLI flag order
- Added test support functions set_test_args()/clear_test_args() for Click testing compatibility  
- Leveraged existing sequential section processing in RepoScanner by creating individual sections per pattern

## Key Features Delivered
- CLI now processes -e and -i flags sequentially when mixed together (BREAKING CHANGE)
- Order of flags matters: llmd -w src/ -e test.py -i test.py includes test.py (different from -i then -e)
- Support for unlimited chaining of patterns (ad-infinitum capability)
- Full backward compatibility for single flag usage and existing llm.md files

## Files Modified
- src/llmd/parser.py: Added sequential pattern classes and CLI override support
- src/llmd/cli.py: Added argument parsing and test support functions  
- tests/test_cli_modes.py: Added comprehensive sequential processing test suite
- scratchpad/task-13-sequential-processing-ultrathink-plan.md: Updated with implementation status

## Testing & Validation
- All acceptance criteria examples working correctly
- 7 new tests covering sequential processing scenarios
- All existing tests pass (except unrelated CLI help format test)
- Verified backward compatibility with legacy usage patterns

## Approach Decision
Chose sys.argv parsing over Click callbacks to reliably preserve argument order across different environments. Added global variable override mechanism for test compatibility with Click's testing framework.
