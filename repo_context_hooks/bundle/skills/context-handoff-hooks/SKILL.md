---
name: context-handoff-hooks
description: >
  Agent-level continuity skill. Maintains project context across session boundaries, compaction,
  and agent handoffs by reading/writing workspace contracts in the repo. Activates on SessionStart,
  PreCompact, PostCompact, and SessionEnd. Install once to agent home - works in every workspace.
  Use when starting any new session in a repo that has specs/README.md, or when setting up
  context continuity for a new workspace.
---

# Context Handoff Hooks

Agent-level continuity skill. Runs at the agent runtime level - not per-repo setup.

## Behavior

**On SessionStart:** Read `specs/README.md` and inject active work context. If no workspace contract exists, offer to scaffold it.

**On PreCompact:** Checkpoint current work state, open decisions, and next step into `specs/README.md`.

**On PostCompact:** Reload from `specs/README.md`. Reconstruct working context from repo state, not session memory.

**On SessionEnd:** Write final handoff summary to `specs/README.md` for the next session.

## Workspace Contract (what to read and write)

- `specs/README.md` - engineering memory: current work, constraints, next step, open decisions
- `README.md` - product intent: public narrative, what the project does and why
- `UBIQUITOUS_LANGUAGE.md` - shared terms: canonical names, aliases to avoid

## Setup This Skill in a New Workspace

If `specs/README.md` is missing, run:

```bash
repo-context-hooks init
repo-context-hooks doctor
```

To install this skill to agent home (so every session picks it up):

```bash
repo-context-hooks install --platform claude
```

## Verify It Is Working

```bash
repo-context-hooks measure
```

Shows hook events observed and estimated continuity uplift.

## Common Mistakes

- Treating `README.md` and `specs/README.md` as duplicates - they serve different audiences
- Not updating `## Open Issues and Next Work` in `specs/README.md` - session start context becomes stale
- Installing per-repo hook entries without the agent-home skill - hooks fire but the skill is not loaded
