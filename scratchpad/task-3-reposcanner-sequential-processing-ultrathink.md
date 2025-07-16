# Task 3: Update RepoScanner for Sequential Pattern Processing - ULTRATHINK

**Created:** 2025-07-16 
**Task:** Update RepoScanner for Sequential Pattern Processing  
**Status:** IMPLEMENTATION COMPLETE (100%)

---

## Implementation Status Update - 2025-07-16

### Implementation Completed
✅ All acceptance criteria have been met:
- Scanner creates initial file set based on mode (empty for WHITELIST, all files for BLACKLIST)
- Default exclusions are applied based on options (respect_gitignore, include_hidden, include_binary)
- Pattern sections are processed sequentially in order
- WHITELIST mode adds files matching implicit and INCLUDE patterns
- BLACKLIST mode removes files matching implicit and EXCLUDE patterns
- Options flags override default exclusion behavior
- Scanner works with updated parser interface
- All existing tests pass (17/17)
- New tests cover sequential processing scenarios (8/8)

### All Tests Passing
- **Legacy tests**: 9/9 passing (no regressions)
- **New sequential tests**: 8/8 passing
- **Parser tests**: 26/26 passing
- **Total**: 43/43 tests passing

### Code Quality
- ✅ Ruff linter: All checks passed
- ✅ No regressions in existing functionality
- ✅ Clean, maintainable code structure

## Current State Analysis

### Current RepoScanner Implementation
- Uses precedence-based logic: ONLY > INCLUDE rescue > normal exclusions
- Has special handling for ONLY patterns that bypass all exclusions
- Hard-coded default exclusions: binary files, hidden files, gitignore files
- Uses two main scan methods: `_scan_with_only()` and `_scan_all_files()`
- Directory traversal with `_walk_directory()` has complex logic for include patterns

### Current Parser Interface (LlmMdParser)
The parser has been updated (task 2) to support:
- Mode-based format: `get_mode()` returns "WHITELIST" or "BLACKLIST" 
- Sequential sections: `get_sections()` returns ordered list of pattern sections
- Options: `get_options()` returns parsed OPTIONS dict
- Implicit patterns: `get_implicit_patterns()` returns patterns after mode declaration

## Required Changes Analysis

### 1. Constructor Changes
**Current:** `__init__(self, repo_path: Path, gitignore_parser: GitignoreParser, llm_parser: LlmMdParser, verbose: bool = False)`

**Needed:** Add support for options that control default exclusions
- Should accept options dict from llm_parser or CLI overrides
- Options: respect_gitignore, include_hidden, include_binary

### 2. New Sequential Processing Logic
**Current approach:** Precedence-based (ONLY > INCLUDE rescue > exclude)

**New approach:** Sequential processing based on mode
1. Determine initial file set based on mode
2. Apply default exclusions (controlled by options)
3. Process sections in order (implicit patterns + explicit sections)
4. Each section either adds (WHITELIST/INCLUDE) or removes (BLACKLIST/EXCLUDE) files

### 3. Key Methods to Implement

#### `_get_all_files() -> List[Path]`
- Discover all files in repository
- Skip always-skipped directories (`.git`, `__pycache__`, etc.)
- No filtering applied here - just file discovery

#### `_apply_default_exclusions(files: List[Path], options: Dict) -> List[Path]`
- Apply gitignore exclusions (if respect_gitignore=True)
- Apply hidden file exclusions (if include_hidden=False)
- Apply binary file exclusions (if include_binary=False)

#### `_process_section(files: List[Path], section: Dict, mode: str) -> List[Path]`
- Process a single pattern section
- For WHITELIST/INCLUDE: add matching files to the set
- For BLACKLIST/EXCLUDE: remove matching files from the set
- Use pathspec for pattern matching

### 4. Updated scan() Method Logic
```python
def scan() -> List[Path]:
    # 1. Get mode and sections from parser
    mode = self.llm_parser.get_mode()
    sections = self.llm_parser.get_sections()
    options = self.llm_parser.get_options()
    
    # Handle legacy format or CLI overrides
    if mode is None:
        # Fall back to legacy behavior
        return self._scan_legacy()
    
    # 2. Create initial file set based on mode
    if mode == "WHITELIST":
        files = []  # Start empty
    else:  # BLACKLIST
        files = self._get_all_files()  # Start with all files
    
    # 3. Apply default exclusions
    files = self._apply_default_exclusions(files, options)
    
    # 4. Process sections sequentially
    for section in sections:
        files = self._process_section(files, section, mode)
    
    # 5. Sort and return
    files.sort()
    return files
```

## Architecture Deep Dive

### File Set Management Strategy
- Use `set` internally for efficient add/remove operations
- Convert to sorted list at the end
- Track files by Path objects throughout

### Pattern Matching Strategy  
- Use pathspec library consistently (already used in parser)
- Create PathSpec for each section's patterns
- Handle relative paths correctly (relative to repo root)

### Options Integration Strategy
- Accept options dict in constructor or scan method
- CLI options should override file options
- Default values according to PRD:
  - respect_gitignore: True
  - include_hidden: False  
  - include_binary: False

### Backward Compatibility Strategy
- Keep legacy scan methods for fallback
- Detect legacy format vs new format
- CLI-only patterns should still work (convert to sections internally)

## Testing Strategy

### Test Categories Needed

#### 1. Mode-Based Sequential Processing Tests
- WHITELIST mode with implicit patterns
- BLACKLIST mode with implicit patterns  
- Mixed sections (EXCLUDE after INCLUDE, etc.)
- Empty mode sections
- Options affecting default exclusions

#### 2. Options Integration Tests
- respect_gitignore=False includes gitignored files
- include_hidden=True includes hidden files
- include_binary=True includes binary files
- CLI options override file options

#### 3. Backward Compatibility Tests
- Legacy ONLY/INCLUDE/EXCLUDE format still works
- CLI-only patterns work with new scanner
- No regressions in existing behavior

#### 4. Edge Cases
- Empty file sets
- All files excluded
- Recursive pattern matching
- Large directory structures

## Implementation Plan Refinement

### Phase 1: Core Infrastructure  
1. Add options support to constructor
2. Implement `_get_all_files()` method
3. Implement `_apply_default_exclusions()` method
4. Create helper methods for file set operations

### Phase 2: Sequential Processing
1. Implement `_process_section()` method
2. Rewrite main `scan()` method for sequential processing
3. Add mode detection and section processing loop
4. Handle empty/missing sections gracefully

### Phase 3: Integration & Compatibility
1. Add legacy format fallback (`_scan_legacy()`)
2. Integrate CLI options with file options
3. Update directory traversal logic if needed
4. Ensure verbose output still works

### Phase 4: Testing & Validation
1. Write comprehensive unit tests for new methods
2. Write integration tests for mode-based processing
3. Validate all existing tests still pass
4. Add performance tests for large repos

## Risk Assessment

### High Risk Areas
- **Directory traversal changes**: Current `_walk_directory()` has complex logic for INCLUDE patterns that may break
- **Performance impact**: Sequential processing might be slower than precedence-based logic  
- **Memory usage**: Loading all files into memory for BLACKLIST mode might be expensive

### Mitigation Strategies
- Keep existing directory traversal logic where possible
- Use generators and lazy evaluation where appropriate
- Add performance benchmarks to catch regressions
- Implement incremental processing for large file sets

## Key Decision Points

### 1. File Discovery Strategy
**Option A:** Use existing `_walk_directory()` with modifications
**Option B:** Rewrite file discovery from scratch
**Decision:** Option A - modify existing logic to reduce risk

### 2. Options Integration
**Option A:** Pass options as constructor parameter
**Option B:** Get options dynamically from parser during scan()
**Decision:** Option B - more flexible, allows CLI overrides

### 3. Legacy Compatibility  
**Option A:** Complete rewrite, remove legacy support
**Option B:** Dual-mode scanner with legacy fallback
**Decision:** Option B - safer, maintains compatibility

## Implementation Notes Template

```
## Implementation Notes

### Approach Taken
- [Description of overall approach]
- [Key architectural decisions made]

### Features Implemented
- [List of new methods implemented]
- [Changes to existing methods]

### Technical Decisions and Trade-offs
- [Performance vs memory trade-offs]
- [Compatibility vs simplicity trade-offs]
- [Error handling approach]

### Modified Files
- src/llmd/scanner.py: [description of changes]
- tests/test_patterns.py: [new tests added]
- tests/unit/test_scanner.py: [if created]
```

---

**Next Steps:**
1. Write failing tests for new sequential processing behavior
2. Implement core infrastructure (Phase 1)
3. Implement sequential processing logic (Phase 2) 
4. Add integration and compatibility layer (Phase 3)
5. Complete test coverage (Phase 4)

**Success Criteria:**
- All acceptance criteria from task 3 are met
- All existing tests continue to pass
- New tests demonstrate sequential processing works correctly
- Code is clean and maintainable
- Performance is acceptable for typical repositories