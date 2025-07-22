Read relevant files in the codebase to get a general map of where important files are and what they do, then output a tree map like so:

```
.
├── CLAUDE.md                           # Project instructions and environment setup
├── LICENSE
├── README.md
├── backlog/
│   ├── archive/                        # Archived tasks and drafts
│   │   ├── drafts/
│   │   └── tasks/
│   ├── config.yml                      # Backlog configuration
│   ├── decisions/                      # Architectural decisions
│   ├── docs/                           # 📁 Project documentation hub
│   │   ├── PRD.md                      # Product Requirements Document
│   │   ├── UV-docs.md                  # UV package manager documentation
│   │   ├── backlog-usage.md            # Instructions for task management
│   │   ├── claude-hooks.md             # Claude Code hooks documentation
│   │   └── codebase-map.md             # This file
│   ├── drafts/                         # Work in progress documents
│   └── tasks/                          # 📋 Active development tasks
│       ├── task-1 - Implement-Claude-Code-hooks-system.md
│       ├── task-2 - Set-up-basic-CLI-tool-structure-with-core-commands.md
│       ├── task-3 - Implement-local-webhook-server-to-receive-Claude-Code-events.md
│       ├── task-4 - Create-Discord-bot-client-foundation-with-DM-handling.md
│       ├── task-5 - Implement-PIN-based-authentication-system.md
│       ├── task-6 - Connect-webhook-server-to-Discord-bot-for-task-notifications.md
│       ├── task-7 - Implement-init-command-and-hook-subcommand-for-Claude-Code-integration.md
│       └── task-8 - Improve-init-command-to-intelligently-merge-hooks-with-existing-settings.md
├── docs/
│   └── setup.md                        # Installation and setup guide
├── pyproject.toml                      # Python project configuration
├── scratchpad/                         # 📝 Development planning documents
│   ├── task-2-implementation-plan.md
│   ├── task-3-implementation-plan.md
│   └── task-7-implementation-plan-2025-07-15.md
├── src/
│   └── claude_discord_bot/             # 🔧 Main application code
│       ├── __init__.py                 # Package initialization
│       ├── cli/
│       │   └── main.py                 # 🎯 CLI entry point with all commands
│       ├── discord/
│       │   └── bot.py                  # 🤖 Discord bot implementation
│       ├── hooks/
│       │   ├── __init__.py
│       │   ├── manager.py              # 🔗 Hook management and execution
│       │   └── matcher.py              # 🎯 Pattern matching for hooks
│       ├── server/
│       │   └── webhook.py              # 🌐 FastAPI webhook server for Claude Code events
│       └── settings/
│           ├── __init__.py
│           ├── loader.py               # ⚙️ Settings file loading and management
│           ├── models.py               # 📝 Pydantic models for configurations
│           └── validator.py            # ✅ Settings validation logic
├── tests/
│   ├── test_cli.py                     # CLI integration tests
│   ├── test_webhook.py                 # Webhook server tests
│   └── unit/                           # 🧪 Unit tests directory
│       ├── test_cli.py                 # CLI unit tests
│       └── test_init_hook_commands.py  # Init and hook command tests
└── uv.lock                             # UV dependency lock file
```

Add annotations next to important code files for reference later on to more easily navigate the codebase.

Put the codebase-map.md file in backlog/docs (if already exists) otherwise in a docs/ directory. 