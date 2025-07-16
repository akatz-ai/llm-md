---
id: task-4
title: Implement CLI Mode Selection and Override Behavior
status: To Do
assignee: []
created_date: '2025-07-16'
labels: []
dependencies: []
priority: high
---

## Description

Add missing CLI mode flags (-w, --whitelist and -b, --blacklist) and behavior control flags to fully support PRD-specified CLI interface. CLI mode flags must completely override any llm.md configuration rather than being additive.

## Acceptance Criteria

- [ ] CLI accepts -w/--whitelist PATTERN... for whitelist mode
- [ ] CLI accepts -b/--blacklist PATTERN... for blacklist mode
- [ ] CLI mode flags completely override llm.md configuration
- [ ] Add --include-gitignore/--no-gitignore flags
- [ ] Add --include-hidden/--with-hidden flags
- [ ] Add --include-binary/--with-binary flags
- [ ] Add --quiet/-q flag for suppressing non-error output
- [ ] MODE flags and PATTERN refinement flags (-e/-i) work together correctly
- [ ] All new CLI options properly integrated with existing RepoScanner logic
