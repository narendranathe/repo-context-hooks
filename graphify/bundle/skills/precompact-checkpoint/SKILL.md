---
name: precompact-checkpoint
description: Use when an agent is about to compact context and must preserve current decisions, progress, and next-work state in project memory.
---

# Pre-Compact Checkpoint

## Overview

Creates a durable checkpoint before compaction so important session context survives token compression.

## Use With

- `context-handoff-hooks` skill package
- `.claude/scripts/repo_specs_memory.py pre-compact`

## Required Behavior

- Ensure `specs/README.md` has current sections for:
  - constraints
  - built so far
  - decisions
  - failures/reverts
  - next work
- Append a timestamped checkpoint entry under `## Session Checkpoints`
- Keep checkpoint concise and operational
