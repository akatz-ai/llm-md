---
id: task-1
title: Implement default behavior when no llm.md exists
status: To Do
assignee: []
created_date: '2025-07-16'
labels: []
dependencies: []
---

## Description

The tool currently requires an llm.md configuration file to work properly. To improve usability, the tool should work out-of-the-box without requiring configuration. When no llm.md file exists, the tool should default to blacklist mode with no explicit exclusions, while still applying the standard default exclusions (gitignore, hidden files, binary files).

## Acceptance Criteria

- [ ] CLI runs successfully when no llm.md file exists
- [ ] Default behavior includes all files except gitignore hidden and binary files
- [ ] Default output filename is llm-context.md in current directory
- [ ] Scanner operates in blacklist mode with empty exclusion patterns
- [ ] Default exclusions (gitignore hidden binary) are still applied
- [ ] LlmMdParser constructor accepts default_mode parameter
- [ ] Existing functionality with llm.md files remains unchanged
- [ ] All existing tests pass
- [ ] New tests cover default behavior scenarios

## Implementation Plan

1. Update LlmMdParser constructor to accept default_mode parameter\n2. Modify CLI to handle missing llm.md gracefully\n3. Update scanner to handle blacklist mode with no patterns\n4. Ensure default exclusions are preserved\n5. Add tests for default behavior\n6. Update documentation if needed
