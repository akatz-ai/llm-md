# Task 10 - Fix TOC anchor format bug in markdown generator

**Timestamp:** 2025-07-17  
**Task:** Fix TOC anchor format bug in markdown generator  
**Status:** 0% - ULTRATHINK Planning Phase

## Problem Analysis (ULTRATHINK)

### Current Implementation Analysis

From `src/llmd/generator.py`:

1. **Line 47** in `_generate_toc()`: 
   ```python
   anchor = str(rel_path).replace('/', '-').replace('.', '-').lower()
   ```

2. **Line 55** in `_generate_file_section()`:
   ```python
   anchor = str(rel_path).replace('/', '-').replace('.', '-').lower()
   ```

3. **Line 69** in `_generate_file_section()`:
   ```python
   section = f"""## {rel_path} {{#{anchor}}}"""
   ```

### Problem Statement Deep Dive

The task description states that TOC links are broken for files with dots in their names. However, upon initial analysis, both methods use identical anchor generation logic.

**BUT WAIT** - I need to understand the actual markdown rendering behavior:

For a file `src/main.py`:
- TOC generates: `[src/main.py](#src-main-py)`
- Section generates: `## src/main.py {#src-main-py}`

**Critical Insight**: The `{#anchor}` syntax is valid in some markdown processors but not universally supported. Many markdown processors (including GitHub's) expect section headers to auto-generate anchors based on the header text itself, not custom anchor IDs.

### The Real Problem

Let me think about this more deeply:

1. **Standard Markdown Behavior**: Most markdown processors auto-generate anchors from header text by:
   - Converting to lowercase
   - Replacing spaces with hyphens
   - Removing special characters
   - For `## src/main.py`, the auto-generated anchor would be `#srcmainpy` or `#src-main-py` depending on how slash and dot are handled

2. **Current Implementation Problem**: We're using `{#custom-anchor}` syntax which might not work in all markdown renderers.

3. **Inconsistency Issue**: The TOC is generating links to anchors that might not exist or work as expected.

### Research: Markdown Anchor Standards

**GitHub Flavored Markdown (GFM)**:
- Auto-generates anchors from header text
- Converts to lowercase
- Replaces non-alphanumeric with hyphens
- For `## src/main.py` → anchor becomes `#srcmainpy` (removing slashes and dots)

**CommonMark Standard**:
- Similar behavior
- Header `## src/main.py` → anchor `#srcmainpy`

**Custom Anchor Syntax**:
- `{#custom-id}` is supported by Pandoc and some processors
- Not universally supported

### The Fix Strategy

**Option 1: Remove custom anchors, rely on auto-generation**
- Remove `{#anchor}` from section headers
- Make TOC link generation match the auto-generation algorithm
- PRO: Universal compatibility
- CON: Need to reverse-engineer exact auto-generation algorithm

**Option 2: Fix the dot replacement issue while keeping custom anchors**
- The task suggests that dots should be preserved
- But this might not work with standard markdown processors
- PRO: Simpler fix
- CON: May not solve the actual compatibility issue

**Option 3: Use a well-tested anchor generation algorithm**
- Implement the same algorithm that GitHub/CommonMark uses
- Ensure TOC and sections use identical logic
- PRO: Maximum compatibility
- CON: More complex implementation

### Decision: Option 1 - Rely on Standard Auto-Generation

**Reasoning**:
1. Maximum compatibility with all markdown processors
2. Follows markdown standards
3. The PRD mentions GitHub repository cloning feature, so GFM compatibility is likely important
4. Simpler and more maintainable

**Implementation Plan**:
1. **Research Phase**: Write tests to understand how different markdown processors handle header anchor generation
2. **Implement Algorithm**: Create a function that replicates standard auto-generation
3. **Update TOC**: Use this algorithm in `_generate_toc()`
4. **Update Sections**: Remove custom `{#anchor}` syntax from section headers
5. **Test**: Verify TOC links work in actual markdown renderers

### Detailed Implementation Steps

1. **Create `_generate_anchor()` method**:
   ```python
   def _generate_anchor(self, text: str) -> str:
       """Generate anchor ID following GitHub Flavored Markdown rules."""
       # Convert to lowercase
       # Replace non-alphanumeric with hyphens  
       # Remove leading/trailing hyphens
       # Collapse multiple hyphens
   ```

2. **Update `_generate_toc()`**:
   - Use header text (the file path) to generate anchor
   - Call `_generate_anchor(str(rel_path))`

3. **Update `_generate_file_section()`**:
   - Remove `{#anchor}` syntax
   - Let markdown processor auto-generate anchors

4. **Write comprehensive tests**:
   - Test various file names with dots, slashes, special characters
   - Test that TOC links match actual anchors in rendered markdown

### Test Cases to Write

1. **Simple file**: `main.py` → anchor should be `#mainpy`
2. **File with dots**: `test.file.py` → anchor should be `#testfilepy`  
3. **File with path**: `src/main.py` → anchor should be `#srcmainpy`
4. **Complex file**: `src/test.config.json` → anchor should be `#srctestconfigjson`
5. **Edge cases**: files with numbers, underscores, hyphens

### Expected Outcome

After fix:
- TOC link: `[src/main.py](#srcmainpy)`
- Section header: `## src/main.py` (auto-generates anchor `#srcmainpy`)
- Links work in GitHub, VS Code, and other standard markdown viewers

This approach ensures maximum compatibility and follows established markdown standards.

---

## Implementation Status Update

**Timestamp:** 2025-07-17 14:45  
**Status:** 50% - Implementation Phase Started

### Tests Created and Committed
- Created comprehensive test suite in `tests/test_generator.py`
- Tests cover all edge cases: dots, slashes, complex paths, GitHub standard
- All tests FAIL as expected, confirming the bug exists
- Tests committed successfully to establish TDD baseline

### Next Steps
1. Implement `_generate_anchor()` method following GitHub standard
2. Update `_generate_toc()` to use new anchor generation
3. Update `_generate_file_section()` to remove custom `{#anchor}` syntax
4. Run tests until all pass

### Key Implementation Details Needed
- GitHub anchor generation algorithm: lowercase, remove special chars, no hyphens for dots
- Remove custom anchor syntax from section headers
- Ensure TOC and sections use identical anchor generation logic