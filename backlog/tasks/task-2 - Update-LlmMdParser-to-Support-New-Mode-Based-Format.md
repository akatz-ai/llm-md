---
id: task-2
title: Update LlmMdParser to Support New Mode-Based Format
status: To Do
assignee: []
created_date: '2025-07-16'
updated_date: '2025-07-16'
labels: []
dependencies: []
---

## Description

The current LlmMdParser uses the old ONLY/INCLUDE/EXCLUDE pattern format. The PRD specifies a new mode-based format with WHITELIST/BLACKLIST modes, implicit patterns, and OPTIONS sections. This parser is foundational - all other components depend on it understanding the configuration format correctly.

## Acceptance Criteria

- [ ] LlmMdParser correctly parses WHITELIST/BLACKLIST mode declarations
- [ ] Implicit patterns following mode declaration are parsed correctly
- [ ] EXCLUDE/INCLUDE/OPTIONS sections are parsed in order
- [ ] OPTIONS values are converted to appropriate types (boolean int string)
- [ ] get_sections() method returns ordered list of pattern sections
- [ ] get_mode() method returns current mode (WHITELIST/BLACKLIST)
- [ ] get_options() method returns parsed OPTIONS as dictionary
- [ ] Invalid configurations are handled gracefully
- [ ] All existing tests pass or are updated appropriately
- [ ] New tests cover the new functionality

## Implementation Plan

1. Update LlmMdParser class attributes to support new format\n2. Refactor _parse_config() method for mode-based parsing\n3. Add helper methods for mode detection and option value parsing\n4. Remove deprecated methods (has_only_patterns, matches_only)\n5. Update pattern checking methods for sequential processing\n6. Write comprehensive tests for new functionality\n7. Update existing tests to work with new format
