# Task 13 Sequential Processing Ultrathink Plan

**Created:** 2025-07-17
**Task:** Implement sequential pattern processing for CLI flags
**Mode:** Ultrathink Analysis

## Problem Analysis

### Current Issue from Task 11
The task 11 implementation notes reveal the core problem:
- Click CLI groups `-e` and `-i` flags separately, losing order information
- Current implementation treats INCLUDE/EXCLUDE as global precedence rules 
- PRD specifies **sequential processing** where order matters
- Examples show complex chaining: `-w src/ -e src/*.pyc` should process sequentially

### Sequential Processing Requirements
From the PRD and task 13, sequential processing means:
1. `llmd -w src/ -e src/*.pyc` → Start with src/, then remove .pyc files
2. `llmd -w src/ -e src/random/ -i src/random/important-file.txt` → Start with src/, remove src/random/, then rescue important file
3. `llmd -b tests/ -i tests/integration/ -e tests/integration/*.pyc` → Start with everything except tests/, rescue tests/integration/, then remove .pyc files

### Technical Challenge
Click framework by default collects multiple occurrences of the same option into tuples:
```python
@click.option('-e', '--exclude', multiple=True)
@click.option('-i', '--include', multiple=True)
```
This results in: `excludes = ('-e', 'src/*.pyc'), includes = ('-i', 'src/random/important-file.txt')`
But we lose the order: was it `-e` then `-i`, or `-i` then `-e`?

## Solution Design

### Option 1: Custom Click Callback (CHOSEN APPROACH)
Use a custom callback that captures flags in the order they appear:

```python
def add_pattern(ctx, param, value):
    if not hasattr(ctx, 'pattern_sequence'):
        ctx.pattern_sequence = []
    if value:
        pattern_type = 'exclude' if param.name == 'exclude' else 'include'
        for pattern in value if isinstance(value, tuple) else [value]:
            ctx.pattern_sequence.append((pattern_type, pattern))
    return value

@click.option('-e', '--exclude', multiple=True, callback=add_pattern)
@click.option('-i', '--include', multiple=True, callback=add_pattern)
```

### Option 2: Single Combined Flag
Replace with: `--pattern exclude:*.pyc --pattern include:important.txt`
- Pros: Natural ordering, clear syntax
- Cons: Breaking change, less intuitive than separate flags

### Option 3: Parse sys.argv Manually
Bypass Click for `-e`/`-i` parsing
- Pros: Full control over order
- Cons: Reimplements Click functionality, error-prone

**Decision: Use Option 1 (Custom Callback)** - Preserves backward compatibility while solving ordering issue

## Implementation Architecture

### Data Structure for Sequential Patterns
```python
@dataclass
class SequentialPattern:
    pattern_type: str  # 'exclude' or 'include'
    pattern: str
    
class PatternSequence:
    def __init__(self):
        self.patterns: List[SequentialPattern] = []
        
    def add_pattern(self, pattern_type: str, pattern: str):
        self.patterns.append(SequentialPattern(pattern_type, pattern))
        
    def apply_to_fileset(self, files: Set[str], base_patterns: List[str]) -> Set[str]:
        # Apply base patterns first (whitelist/blacklist)
        # Then apply sequential patterns in order
```

### CLI Integration Points

#### 1. CLI Argument Parsing (cli.py)
- Modify `@click.option` decorators to use custom callbacks
- Store sequential pattern information in Click context
- Pass pattern sequence to scanner

#### 2. Scanner Processing (scanner.py)
- Add `apply_sequential_patterns()` method
- Integrate with existing `scan()` workflow
- Handle both legacy (precedence-based) and new (sequential) processing

#### 3. Parser Integration (parser.py)
- LlmMdParser should continue to work with legacy INCLUDE/EXCLUDE sections
- CLI mode should use sequential processing
- Clear separation between file-based and CLI-based pattern handling

### Processing Flow

```
1. Parse CLI arguments with custom callbacks → PatternSequence
2. Initialize file set based on mode:
   - Whitelist: Start empty, add base patterns
   - Blacklist: Start with all files, remove base patterns
3. Apply default exclusions (gitignore, hidden, binary)
4. Apply sequential patterns in order:
   - For each pattern in sequence:
     - If 'exclude': remove matching files
     - If 'include': add matching files (rescue)
5. Return final file set
```

## Backward Compatibility Strategy

### Legacy llm.md Files
- Continue using existing precedence rules (INCLUDE overrides EXCLUDE globally)
- No changes to `LlmMdParser` pattern processing
- Only CLI mode gets sequential processing

### CLI Behavior
- Existing commands work identically if they don't mix `-e` and `-i` flags
- New sequential behavior only applies when both `-e` and `-i` are used
- Single flag usage (`-e` only or `-i` only) works as before

## Implementation Steps

### Phase 1: CLI Argument Preservation
1. Add `PatternSequence` class to `parser.py`
2. Implement custom Click callbacks in `cli.py`
3. Modify CLI command to store pattern sequence in context
4. Pass pattern sequence to scanner

### Phase 2: Sequential Processing Engine
1. Add `apply_sequential_patterns()` to `RepoScanner`
2. Integrate sequential processing with existing `scan()` method
3. Ensure proper file set initialization based on mode
4. Handle edge cases (empty patterns, invalid patterns)

### Phase 3: Testing & Validation
1. Add comprehensive tests for sequential processing
2. Test all examples from task 13 acceptance criteria
3. Ensure backward compatibility with existing usage
4. Test edge cases and error conditions

## Test Cases to Implement

### Sequential Processing Tests
```python
def test_sequential_whitelist_exclude():
    # llmd -w src/ -e src/*.pyc
    # Should include src/ then remove .pyc files
    
def test_sequential_exclude_include():
    # llmd -w src/ -e src/random/ -i src/random/important-file.txt
    # Should include src/, remove random/, then rescue important file
    
def test_sequential_complex_chain():
    # llmd -b tests/ -i tests/integration/ -e tests/integration/*.pyc
    # Complex multi-step processing
    
def test_sequential_ad_infinitum():
    # Test long chains of -e and -i flags
```

### Backward Compatibility Tests
```python
def test_legacy_llmd_files_unchanged():
    # Existing llm.md files should work identically
    
def test_single_flag_usage_unchanged():
    # -e only or -i only should work as before
```

## Risk Analysis

### High Risk Areas
1. **Click callback execution order**: Callbacks might not execute in expected order
2. **Pattern matching logic**: Complex interactions between sequential patterns
3. **Backward compatibility**: Accidental changes to existing behavior

### Mitigation Strategies
1. **Extensive testing**: Cover all interaction patterns and edge cases
2. **Incremental implementation**: Test each component in isolation first
3. **Rollback plan**: Keep legacy processing as fallback if needed

## Performance Considerations

### Potential Impact
- Sequential processing requires multiple passes over file sets
- Pattern matching might be repeated for each sequential pattern

### Optimization Strategies
- Cache compiled regex patterns
- Use set operations for efficient file filtering
- Consider lazy evaluation for large repositories

## Success Criteria

### Functional Requirements
- [ ] All task 13 acceptance criteria pass
- [ ] Sequential processing examples work correctly
- [ ] Legacy llm.md files continue working
- [ ] CLI backward compatibility maintained

### Quality Requirements
- [ ] All existing tests continue passing
- [ ] New tests achieve >95% coverage of new code
- [ ] Performance regression <10% for typical use cases
- [ ] Error handling for invalid pattern sequences

## Next Steps for Implementation

1. **Start with TDD**: Write failing tests for sequential processing examples
2. **Implement CLI changes**: Add custom callbacks and pattern sequence storage
3. **Add sequential engine**: Implement pattern processing logic
4. **Iterative testing**: Run tests after each change
5. **Validation**: Test with real repositories and edge cases

---

## Implementation Status Update - 2025-07-17

**Status:** COMPLETED - Sequential pattern processing successfully implemented
**Completion:** 100%

### What Was Implemented

#### 1. Data Structures
- ✅ Added `SequentialPattern` dataclass to represent individual patterns
- ✅ Added `PatternSequence` class to manage ordered pattern lists
- ✅ Integrated with existing `LlmMdParser` architecture

#### 2. CLI Argument Preservation
- ✅ Implemented `build_pattern_sequence_from_raw_args()` to parse `sys.argv` and preserve flag order
- ✅ Added test support functions `set_test_args()` and `clear_test_args()` for Click testing compatibility
- ✅ Modified CLI to extract pattern sequence and pass to parser

#### 3. Sequential Processing Engine
- ✅ Leveraged existing sequential section processing in `RepoScanner`
- ✅ Modified `LlmMdParser._setup_cli_override()` to create sequential sections
- ✅ Each `-e` and `-i` flag creates its own section, processed in order

#### 4. Testing & Validation
- ✅ All task 13 acceptance criteria tests pass:
  - Sequential whitelist with exclude
  - Complex exclude/include/rescue chains
  - Blacklist with include/exclude combinations
  - Order-dependent processing
  - Ad-infinitum chaining
- ✅ Backward compatibility maintained for existing CLI usage
- ✅ Legacy llm.md file processing unchanged

### Technical Solution

The final implementation uses a hybrid approach:

1. **Real CLI Usage**: Parses `sys.argv` directly to preserve exact flag order
2. **Test Environment**: Uses global variable override for Click testing compatibility
3. **Sequential Processing**: Creates individual sections for each pattern, leveraging existing scanner architecture

### Key Files Modified

- `src/llmd/parser.py` - Added SequentialPattern classes and sequential processing support
- `src/llmd/cli.py` - Added argument parsing and test support functions
- `tests/test_cli_modes.py` - Added comprehensive sequential processing tests

### Backward Compatibility

- ✅ Existing CLI commands work identically when not mixing `-e` and `-i`
- ✅ Legacy llm.md files continue using precedence-based processing
- ✅ Only CLI mode with mixed `-e`/`-i` flags uses sequential processing

### Examples Working

All examples from task acceptance criteria work correctly:

```bash
# Sequential whitelist with exclude
llmd -w src/ -e src/*.pyc

# Complex rescue chain
llmd -w src/ -e src/random/ -i src/random/important-file.txt

# Multi-step blacklist processing
llmd -b tests/ -i tests/integration/ -e tests/integration/*.pyc
```

---

**Previous Status:** Planning complete, ready for implementation
**Estimated Complexity:** High - Involves CLI parsing, pattern matching, and backward compatibility
**Key Dependencies:** Task 11 completion (ONLY pattern removal)