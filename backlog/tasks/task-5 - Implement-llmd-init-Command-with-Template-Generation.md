---
id: task-5
title: Implement llmd init Command with Template Generation
status: To Do
assignee: []
created_date: '2025-07-16'
labels: []
dependencies: []
priority: high
---

## Description

Add the missing llmd init subcommand that creates llm.md template files in the current directory. This is a core feature specified in the PRD for helping users get started with configuration.

## Acceptance Criteria

- [ ] CLI accepts 'llmd init' subcommand
- [ ] Support -w/--whitelist option to create whitelist template
- [ ] Support -b/--blacklist option to create blacklist template
- [ ] Support --minimal option for minimal template
- [ ] Generated templates use new mode-based format from PRD
- [ ] Templates include proper OPTIONS section examples
- [ ] Command fails gracefully if llm.md already exists
- [ ] Templates match exact format specified in PRD examples
- [ ] CLI help shows init command and its options
