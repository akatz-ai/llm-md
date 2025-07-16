# Task 2 Implementation Plan: Update LlmMdParser to Support New Mode-Based Format

**Timestamp:** 2025-07-16
**Task:** Update LlmMdParser to Support New Mode-Based Format
**Status:** Planning (0% complete)

## Current Analysis

### Current Parser Structure (LEGACY)
From `/src/llmd/parser.py`, the LlmMdParser currently supports:
- **ONLY:** patterns that bypass all exclusions
- **INCLUDE:** patterns that rescue files from exclusions  
- **EXCLUDE:** / **NOT INCLUDE:** patterns that exclude files
- CLI overrides via `cli_include`, `cli_exclude`, `cli_only`

### New Requirements (from PRD)
Need to support new mode-based format:
- **WHITELIST:** mode - start with empty set, add patterns
- **BLACKLIST:** mode - start with all files, remove patterns
- **Implicit patterns** following mode declaration
- **EXCLUDE:** sections to remove files
- **INCLUDE:** sections to add files back (rescue)
- **OPTIONS:** section with typed values (boolean, int, string)

### Key Methods to Update

Current methods that need changes:
1. `__init__()` - handle new CLI parameters
2. `_parse_config()` - core parsing logic for new format
3. `has_only_patterns()` - remove or replace with `get_mode()`
4. `matches_only()` - remove or refactor
5. Add new methods: `get_mode()`, `get_sections()`, `get_options()`

## Implementation Plan

### 1. Update Class Structure
- Add new class attributes for mode, sections, and options
- Modify constructor to support new CLI parameters
- Remove legacy ONLY-specific attributes

### 2. Refactor Core Parsing Logic
- Rewrite `_parse_config()` for mode-based parsing
- Add mode detection (WHITELIST/BLACKLIST required first line)
- Parse implicit patterns after mode declaration
- Parse EXCLUDE/INCLUDE/OPTIONS sections in order
- Add option value type conversion (boolean, int, string)

### 3. Add New Public Methods
- `get_mode()` -> returns 'WHITELIST' or 'BLACKLIST'
- `get_sections()` -> returns ordered list of pattern sections
- `get_options()` -> returns parsed OPTIONS as dictionary
- `get_implicit_patterns()` -> returns patterns after mode declaration

### 4. Update/Remove Legacy Methods
- Remove or deprecate `has_only_patterns()` and `matches_only()`
- Update `should_include()` and `should_exclude()` if needed
- Ensure backward compatibility or clean migration path

### 5. Error Handling
- Validate mode declaration exists and is first
- Handle invalid configurations gracefully
- Provide clear error messages for format violations

### 6. Testing Strategy (TDD)
- Write tests for new mode parsing FIRST
- Test implicit pattern parsing
- Test EXCLUDE/INCLUDE/OPTIONS sections
- Test option type conversion
- Test error conditions
- Update existing tests or ensure they still pass

## Expected File Changes

1. **`src/llmd/parser.py`** - Major refactoring of LlmMdParser class
2. **`tests/test_parser.py`** - New tests for mode-based format
3. **Other components** may need updates if they use deprecated methods

## Risk Assessment

- **Breaking changes:** Legacy ONLY/INCLUDE/EXCLUDE format will be deprecated
- **Integration impact:** RepoScanner and CLI may need updates for new methods
- **Test coverage:** Extensive new tests needed for new functionality
- **Backward compatibility:** May need migration strategy

## Success Criteria

All acceptance criteria from task description:
- [x] Analysis complete
- [ ] Mode declarations parsed correctly
- [ ] Implicit patterns parsed correctly  
- [ ] EXCLUDE/INCLUDE/OPTIONS sections parsed in order
- [ ] OPTIONS values converted to appropriate types
- [ ] get_sections() method implemented
- [ ] get_mode() method implemented
- [ ] get_options() method implemented
- [ ] Invalid configurations handled gracefully
- [ ] All existing tests pass or updated appropriately
- [ ] New tests cover new functionality

---

## Implementation Status Update

**Timestamp:** 2025-07-16 - Implementation Complete
**Task:** Update LlmMdParser to Support New Mode-Based Format  
**Status:** Implementation complete (100% complete)

### Implementation Results

✅ **Successfully implemented all acceptance criteria:**
- [x] LlmMdParser correctly parses WHITELIST/BLACKLIST mode declarations
- [x] Implicit patterns following mode declaration are parsed correctly
- [x] EXCLUDE/INCLUDE/OPTIONS sections are parsed in order
- [x] OPTIONS values are converted to appropriate types (boolean, int, string)
- [x] get_sections() method returns ordered list of pattern sections
- [x] get_mode() method returns current mode (WHITELIST/BLACKLIST)
- [x] get_options() method returns parsed OPTIONS as dictionary
- [x] get_implicit_patterns() method returns patterns after mode declaration
- [x] Invalid configurations are handled gracefully
- [x] All existing tests pass (maintained backward compatibility)
- [x] New tests cover the new functionality

### Key Implementation Details

1. **Backward Compatibility:** The parser first tries to parse as new mode-based format. If no WHITELIST/BLACKLIST mode is found, it falls back to legacy ONLY/INCLUDE/EXCLUDE format.

2. **New Class Attributes Added:**
   - `mode`: Stores WHITELIST or BLACKLIST mode
   - `implicit_patterns`: Patterns immediately following mode declaration
   - `sections`: Ordered list of all sections with their types and patterns
   - `options`: Dictionary of parsed OPTIONS with type conversion

3. **New Public Methods:**
   - `get_mode()`: Returns current mode or None for legacy format
   - `get_sections()`: Returns ordered list of pattern sections
   - `get_options()`: Returns parsed OPTIONS as dictionary
   - `get_implicit_patterns()`: Returns patterns after mode declaration

4. **Option Type Conversion:** Automatically converts option values to:
   - Boolean: "true"/"false" → True/False
   - Integer: "42" → 42
   - Float: "3.14" → 3.14 (future enhancement)
   - String: default fallback

5. **Error Handling:** Gracefully handles invalid configurations, missing mode declarations, and malformed options.

### Testing Results

- **8 new TDD tests** added for mode-based format - all pass
- **11 existing tests** still pass - no regressions
- **All linter checks** pass
- **Total test coverage:** 19 tests passing

### Files Modified

1. **`src/llmd/parser.py`** - Major refactoring with new parsing logic
2. **`tests/test_parser.py`** - Added comprehensive test suite for new format

The implementation successfully meets all requirements while maintaining full backward compatibility with existing llm.md files.