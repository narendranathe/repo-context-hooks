# Architecture

## Core Flow

1. `SessionStart` loads project memory and next-work context
2. `PreCompact` checkpoints the latest tactical state into `specs/README.md`
3. `PostCompact` reloads the condensed project context
4. `SessionEnd` captures a final continuity note

## Source Of Truth

The repo owns the context:

- user-facing intent lives in `README.md`
- engineering memory lives in `specs/README.md`
- hook automation keeps those files current enough for the next agent

## Why This Works

The system avoids hidden state. A new agent can inspect the repo and understand:

- what the product is
- what constraints matter
- what changed recently
- what should happen next
