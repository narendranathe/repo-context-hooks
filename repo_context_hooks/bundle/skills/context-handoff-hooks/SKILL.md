---
name: context-handoff-hooks
description: Use when setting up an agent-enabled GitHub repository that needs reliable context persistence across session start, pre-compact, post-compact, and session end events.
---

# Context Handoff Hooks

## Overview

This skill installs a context-handoff pipeline so new agent sessions start with project memory, and compaction never drops critical context.

## When to Use

- You use long-running agent sessions and context compaction.
- New agents repeatedly rediscover the same project details.
- You want a durable engineering memory in `specs/README.md`.
- You need "what to do next" context loaded at session start.

## What It Sets Up

- `SessionStart`: refreshes repo memory and injects next-work context.
- `PreCompact`: checkpoints state in `specs/README.md`.
- `PostCompact`: reloads memory and active work context.
- `SessionEnd`: appends a final checkpoint for handoff.
- Local telemetry: emits small JSONL events so `repo-context-hooks measure` can prove hooks actually fired.

## Quick Start

1. Add this skill folder to your repo at `.claude/skills/context-handoff-hooks/`.
2. Run:

```bash
python .claude/skills/context-handoff-hooks/scripts/install_hooks.py --repo-root .
```

3. Start a new session and verify hooks fire.
4. Run `repo-context-hooks measure` to inspect observed hook evidence and estimated continuity uplift.

## Canonical Context Contract

- User-facing narrative: `README.md`
- Engineering memory: `specs/README.md`
- Shared terminology: `UBIQUITOUS_LANGUAGE.md` (if present)
- Work sequencing: `## Open Issues and Next Work` in `specs/README.md`

## Common Mistakes

- Installing hook entries but forgetting script files in `.claude/scripts/`
- Treating `README.md` and `specs/README.md` as duplicate docs instead of different audiences
- Not updating `Open Issues and Next Work`, resulting in weak session-start context
- Assuming hooks work without checking `repo-context-hooks measure`
