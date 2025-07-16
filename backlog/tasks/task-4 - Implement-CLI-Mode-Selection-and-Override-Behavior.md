---
id: task-4
title: Implement CLI Mode Selection and Override Behavior
status: In Progress
assignee: []
created_date: '2025-07-16'
updated_date: '2025-07-16'
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

## Implementation Notes

Implemented CLI Mode Selection and Override Behavior with comprehensive TDD approach.

APPROACH TAKEN:
- Used Click framework to add mutually exclusive mode flags (-w/--whitelist, -b/--blacklist) 
- Added behavior control flags with aliases (--include-gitignore/--no-gitignore, etc.)
- Implemented validation for mutual exclusion and pattern refinement requirements
- Created CLI override logic that completely ignores llm.md when mode flags are used

FEATURES IMPLEMENTED:
- CLI mode selection: -w/--whitelist and -b/--blacklist with multiple patterns  
- Pattern refinement: -e/--exclude and -i/--include (requires mode flags)
- Behavior overrides: --include-gitignore/--no-gitignore, --include-hidden/--with-hidden, --include-binary/--with-binary
- Quiet mode: -q/--quiet flag suppresses non-error output
- Complete llm.md override when CLI mode flags are used

TECHNICAL DECISIONS:
- Used Click's multiple=True with separate flags for each pattern (cleaner UX)
- Added _setup_cli_override method to LlmMdParser for complete config override
- Preserved all existing functionality - no breaking changes
- Implemented comprehensive validation with clear error messages

MODIFIED FILES:
- src/llmd/cli.py - Added all new CLI options and validation logic
- src/llmd/parser.py - Added CLI override support with new constructor parameters
- tests/test_cli_modes.py - Created 12 comprehensive tests covering all acceptance criteria

VERIFICATION:
- All 9 acceptance criteria fully implemented and tested
- 55 total tests passing (12 new + 43 existing) - no regressions
- Code passes ruff linting
- TDD approach followed throughout implementation
