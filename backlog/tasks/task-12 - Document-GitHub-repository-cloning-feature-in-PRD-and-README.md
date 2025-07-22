---
id: task-12
title: Document GitHub repository cloning feature in PRD and README
status: To Do
assignee: []
created_date: '2025-07-17'
labels: []
dependencies: []
priority: low
---

## Description

The implementation includes a --github flag that allows cloning and processing remote GitHub repositories directly. This feature is not documented in the PRD or README and should be added to provide complete documentation of the tool's capabilities.

## Acceptance Criteria

- [ ] PRD.md includes --github option in CLI specification section
- [ ] PRD.md includes examples of GitHub URL usage
- [ ] README.md includes --github option in usage documentation
- [ ] README.md includes example commands with GitHub URLs
- [ ] Both documents explain GitHub URL validation (HTTPS and SSH formats)
- [ ] Documentation explains shallow clone behavior for performance
- [ ] Error handling scenarios are documented (network errors invalid URLs etc)

## Technical Details

### Current Implementation (cli.py):
- Line 218: `--github` option definition
- Lines 99-122: `validate_github_url()` function supports both HTTPS and SSH formats
- Lines 124-169: `clone_github_repo()` function with shallow clone (`--depth 1`)
- Lines 171-183: `cleanup_temp_repo()` for automatic cleanup
- Lines 263-278: Main logic for handling GitHub URLs

### Supported URL formats:
```
# HTTPS format
https://github.com/owner/repo
https://github.com/owner/repo.git
https://github.com/owner/repo/

# SSH format  
git@github.com:owner/repo
git@github.com:owner/repo.git
```

### Key behaviors to document:
1. **Shallow clone**: Uses `git clone --depth 1` for performance
2. **Temporary directory**: Clones to temp directory that's automatically cleaned up
3. **Git requirement**: Requires Git to be installed and available in PATH
4. **Error handling**:
   - Repository not found
   - Network/connection errors
   - Git not installed
   - Invalid URL format

### Example commands to include:
```bash
# Process a public GitHub repository
llmd --github https://github.com/user/repo

# With output file
llmd --github https://github.com/user/repo -o output.md

# With whitelist mode
llmd --github https://github.com/user/repo -w "src/" "*.py"

# SSH URL (requires SSH keys configured)
llmd --github git@github.com:user/private-repo.git
```
