# RepoHandoff Positioning

## One-Line Pitch

RepoHandoff is the reliability layer for coding-agent sessions: it preserves operational context before, during, and after compaction.

## Problem

Agent sessions degrade over time:

- compaction drops tactical context
- new sessions repeat discovery
- next-work state gets stale or lost
- teams over-invest in memory infrastructure when they need deterministic workflow continuity

## Product Thesis

Execution continuity should be deterministic and repository-local.

## Differentiation

- Memory platforms optimize retrieval.
- RepoHandoff optimizes lifecycle reliability.

## Core Value

- deterministic lifecycle hooks (`SessionStart`, `PreCompact`, `PostCompact`, `SessionEnd`)
- dual-document operating contract (`README.md` + `specs/README.md`)
- issue-aware startup context
- zero external infrastructure dependency

## Messaging for Community

- "Not another memory DB. A handoff protocol for real repositories."
- "Compaction-safe continuity for Codex and Claude."
- "Ship context as code: hooks + docs + deterministic checkpoints."
