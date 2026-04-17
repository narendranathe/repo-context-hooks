---
name: session-start-context-loader
description: Use when an agent starts work in a repository and needs immediate context on docs, priorities, issue references, and workflow expectations.
---

# Session Start Context Loader

## Overview

Loads canonical project context at session start so a new agent can execute without rediscovery.

## Use With

- `context-handoff-hooks` skill package
- `.claude/scripts/session_context.py`
- `.claude/scripts/repo_specs_memory.py`

## Expected Output

- Canonical doc list (`README.md`, `specs/README.md`, `CLAUDE.md`)
- Current priority bullets from `Open Issues and Next Work`
- Workflow bullets from `How To Work in This Repo`
- Open issue references (`gh issue list` when available, fallback to `#123` refs in specs)
