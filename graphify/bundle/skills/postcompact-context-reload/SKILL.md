---
name: postcompact-context-reload
description: Use when a session has just compacted and the agent needs to restore active project memory, priorities, and issue context before continuing.
---

# Post-Compact Context Reload

## Overview

Rehydrates high-signal context immediately after compaction to prevent drift and repeated rediscovery.

## Use With

- `context-handoff-hooks` skill package
- `.claude/scripts/repo_specs_memory.py post-compact`
- `.claude/scripts/session_context.py post-compact`

## Required Behavior

- Refresh repo context index in `specs/README.md`
- Reprint active next-work bullets and workflow bullets
- Restore issue references for immediate task resumption
- Continue implementation only after context is reloaded
