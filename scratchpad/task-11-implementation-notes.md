# Task 11 Implementation Notes

## Status: 95% Complete - Need Sequential Processing Fix

### What Was Completed
- ✅ Removed `cli_only` parameter from LlmMdParser constructor 
- ✅ Removed `only_patterns` attribute and related methods (`has_only_patterns`, `matches_only`)
- ✅ Removed `_scan_with_only()` method from RepoScanner
- ✅ Removed ONLY pattern parsing from `_parse_legacy_format()`
- ✅ Updated CLI to not pass `cli_only` parameter
- ✅ Updated tests to expect ONLY pattern removal
- ✅ Fixed basic INCLUDE/EXCLUDE precedence (INCLUDE can rescue from EXCLUDE)

### Critical Issue Discovered
The current implementation treats INCLUDE/EXCLUDE as global precedence rules, but the PRD specifies **sequential processing** where order matters.

### What Sequential Processing Should Look Like
According to user examples:
1. `llmd -w src/ -e src/*.pyc` → Start with src/, then remove .pyc files
2. `llmd -w src/ -e src/random/ -i src/random/important-file.txt` → Start with src/, remove src/random/, then rescue the important file
3. `llmd -b tests/ -i tests/integration/ -e tests/integration/*.pyc` → Start with everything except tests/, rescue tests/integration/, then remove .pyc files

### Current Limitation
Click CLI groups `-e` and `-i` flags separately, losing the order. Need to design a solution that preserves flag order or uses a different approach.

### Next Steps Needed
1. Design CLI to preserve order of `-e` and `-i` flags
2. Implement sequential processing for CLI patterns
3. Ensure legacy INCLUDE/EXCLUDE patterns work correctly
4. Update tests to reflect sequential processing

### Files Modified
- `src/llmd/parser.py` - Removed ONLY pattern support
- `src/llmd/scanner.py` - Removed ONLY scanning, fixed INCLUDE precedence
- `src/llmd/cli.py` - Removed cli_only parameter
- `tests/test_parser.py` - Updated tests for ONLY removal
- `tests/test_patterns.py` - Updated tests for ONLY removal