# Task 7: GitHub Remote Repository Context Extraction - Ultrathink Planning

## Timestamp: 2025-07-17
## Task: task-7 - Add GitHub remote repository context extraction
## Status: 0% - Ultrathink planning phase

## Problem Analysis

The user wants to be able to run something like:
```bash
llmd --github https://github.com/user/repo -o github-repo-context.md
```

This should:
1. Clone the GitHub repository to a temporary location
2. Run llmd with the provided args (if any) on that temporary location
3. Output the context file to the location specified by -o or current directory
4. Clean up the temporary clone

## Current Architecture Understanding

From the codebase map and PRD, the current CLI structure is in `src/llmd/cli.py` using Click framework. The main entry point orchestrates:
- Configuration loading
- File scanning via `scanner.py`
- Output generation via `generator.py`

The CLI already supports various flags like `-o`, `-w`/`--whitelist`, `-b`/`--blacklist`, etc.

## Design Considerations

### 1. CLI Integration
- Add `--github` option to existing CLI
- Should work with all existing flags (whitelist/blacklist patterns, -o output, etc.)
- The --github flag should be mutually exclusive with providing a PATH argument, OR it should override the PATH

### 2. Git Operations
- Need to clone repositories temporarily
- Need to handle authentication (public repos first, may need to consider private repos later)
- Need robust cleanup even if something goes wrong
- Should validate that the URL is a valid GitHub URL

### 3. Temporary Directory Management
- Use Python's tempfile.TemporaryDirectory for automatic cleanup
- Should be cleaned up even if process is interrupted (context manager)
- Clone should be shallow (--depth 1) for performance

### 4. Error Handling
- Invalid GitHub URLs
- Network connectivity issues
- Git not available
- Clone failures (private repos, non-existent repos)
- File system issues

## Implementation Plan

### Phase 1: CLI Flag Addition
1. Add `--github` option to Click CLI in `cli.py`
2. Add validation for GitHub URL format
3. Make it mutually exclusive with PATH or handle precedence

### Phase 2: Git Operations Module
1. Create git operations utilities (could be in cli.py or separate module)
2. Implement GitHub URL validation
3. Implement git clone functionality with temporary directory
4. Add proper error handling and cleanup

### Phase 3: Integration with Existing Flow
1. Modify main flow to handle GitHub repos
2. Ensure all existing CLI options work with --github
3. Update output path handling to work with temporary repos

### Phase 4: Testing
1. Unit tests for GitHub URL validation
2. Integration tests for git operations (may need mocking)
3. End-to-end tests with actual GitHub repositories

## Technical Details

### URL Validation
GitHub URLs can be in formats:
- https://github.com/user/repo
- https://github.com/user/repo.git
- git@github.com:user/repo.git (SSH)

### Git Dependencies
- Need to check if git is available on system
- Use subprocess to run git commands
- Consider using pygit2 or GitPython libraries (but prefer subprocess for simplicity)

### CLI Changes Needed
In `cli.py`, need to:
1. Add `@click.option('--github', help='Clone and process GitHub repository')`
2. Modify main function to handle github_url parameter
3. Add GitHub URL validation
4. Add temporary cloning logic
5. Ensure cleanup happens in finally block or context manager

### Flow Modification
Current flow: PATH -> scan -> generate
New flow: --github URL -> clone to temp -> scan temp -> generate -> cleanup temp

## Risk Analysis

### Low Risk
- Adding CLI option (well-established pattern)
- URL validation (straightforward regex)
- Temporary directory management (Python stdlib)

### Medium Risk
- Git subprocess calls (need proper error handling)
- Integration with existing CLI options (need thorough testing)

### High Risk
- Network dependencies (GitHub availability)
- Authentication for private repos (out of scope for now)
- Edge cases in GitHub URL formats

## Success Criteria Mapping

1. "User can run llmd --github <url> to clone and extract context"
   - Implement --github CLI option
   - Implement git clone functionality
   - Integration with existing scanning logic

2. "Output file location can be specified with -o flag"
   - Ensure -o flag works with --github
   - Should work exactly like current -o behavior

3. "Temporary clone is cleaned up after processing"
   - Use context managers for cleanup
   - Cleanup even on errors

4. "Command integrates with existing llmd arguments"
   - All existing flags should work: -w, -b, -e, -i, --include-hidden, etc.
   - No breaking changes to existing functionality

5. "Error handling for invalid URLs and clone failures"
   - Validate GitHub URLs
   - Handle git command failures
   - Proper error messages for user

## Implementation Notes for Later

Will need to:
- Check git availability early
- Use shallow clones for performance
- Handle both HTTPS and SSH GitHub URLs
- Provide clear error messages
- Ensure no leftover temporary directories

## Next Steps

1. Start with TDD - write tests first
2. Begin with CLI option addition
3. Implement git operations
4. Integration testing
5. Error handling refinement

---

## Timestamp: 2025-07-17 - 15:30
## Status: 25% - TDD Tests Written and Confirmed Failing

### Progress Update

✅ **TDD Tests Written**: Created comprehensive test suite in `tests/test_github_remote.py` covering:
- GitHub URL validation (HTTPS, SSH, invalid URLs)
- Integration with existing CLI options (-w, -b, -e, -i, -o)
- Git operations (clone, cleanup, error handling)
- Complete workflow testing
- Error scenarios (git not available, network issues, cleanup on errors)

✅ **Tests Confirmed Failing**: Ran tests and confirmed they fail as expected:
- 14 failed, 1 passed
- Main failures: `--github` option doesn't exist, `clone_github_repo`/`cleanup_temp_repo` functions don't exist
- This confirms TDD approach is working correctly

### Next Implementation Steps

1. **Add CLI Option**: Add `--github` parameter to main function in `cli.py`
2. **Add Helper Functions**: Implement `clone_github_repo` and `cleanup_temp_repo` functions
3. **Add URL Validation**: Implement GitHub URL validation logic
4. **Integration Logic**: Modify main flow to handle GitHub repositories
5. **Error Handling**: Add comprehensive error handling for git operations

Starting implementation phase now...

---

## Timestamp: 2025-07-17 - 16:45
## Status: 80% - Core GitHub Functionality Complete, Testing Regressions

### Major Progress Update

✅ **Core GitHub Functionality Implemented**:
- Added `--github` CLI option with proper Click integration
- Implemented `validate_github_url()` function supporting HTTPS and SSH GitHub URLs
- Implemented `clone_github_repo()` with shallow cloning and comprehensive error handling
- Implemented `cleanup_temp_repo()` with safe cleanup
- Added try-finally block to ensure cleanup happens even on errors
- Integrated GitHub workflow with all existing CLI options (-w, -b, -e, -i, -o, etc.)

✅ **All GitHub Tests Passing**: 
- 15/15 GitHub-specific tests now pass
- URL validation working for both valid and invalid URLs
- Git operations properly mocked and tested
- Integration with existing CLI patterns working
- Error handling comprehensive and tested
- Complete end-to-end workflow tested

⚠️ **Discovered Regression Issues**:
- Existing CLI tests failing (18 failed, 77 passed)
- Issue appears to be with path argument parsing
- Repository paths being interpreted as commands instead of arguments
- Current directory mode works fine, but explicit path arguments broken
- The `FlexibleGroup` Click behavior appears disrupted

### Current Status: Debugging Regressions

The GitHub functionality is fully working and tested, but I introduced regressions in the existing CLI behavior. The issue seems to be:

1. **Path Argument Parsing**: Repository paths like `/tmp/repo` are being treated as commands
2. **FlexibleGroup Behavior**: The custom Click group logic is not working as expected
3. **Function Signature**: Adding `github_url` parameter may have disrupted Click's parsing

### Next Steps - Regression Fixes

1. **Investigate Click Function Signature**: Ensure adding `github_url` didn't break path handling
2. **Test FlexibleGroup Logic**: Verify the custom Click group still works correctly
3. **Fix Path Argument Processing**: Restore the original `ctx.args` handling behavior
4. **Validate No Breaking Changes**: Ensure all existing tests pass
5. **Final Integration**: Complete the TDD cycle

### Success Criteria Status

- ✅ User can run llmd --github <url> to clone and extract context
- ✅ Output file location can be specified with -o flag  
- ✅ Temporary clone is cleaned up after processing
- ✅ Command integrates with existing llmd arguments (for GitHub mode)
- ✅ Error handling for invalid URLs and clone failures
- ⚠️ Need to fix regressions in existing CLI behavior

### Implementation Completed

**Files Modified:**
- `src/llmd/cli.py`: Added GitHub functionality, helper functions, CLI option, error handling
- `tests/test_github_remote.py`: Comprehensive test suite (15 tests, all passing)

**Functions Added:**
- `validate_github_url()`: URL validation for GitHub repositories
- `clone_github_repo()`: Git cloning with temporary directory management  
- `cleanup_temp_repo()`: Safe cleanup of temporary directories

**CLI Integration:**
- `--github` option added and fully functional
- Integration with all existing options (-w, -b, -e, -i, -o, --dry-run, etc.)
- Proper error handling and user feedback