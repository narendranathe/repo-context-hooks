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

## On SessionStart

1. Read `specs/README.md` — load current work, constraints, open decisions, and next step.
2. Read `README.md` — load user-facing product intent.
3. If no `specs/README.md` exists, offer to run `repo-context-hooks init`.
4. Do not write anything on session start — only read and inject context.

## On PreCompact

Before the context compaction fires, write a checkpoint:

1. Summarize in 3-7 bullets: what was built this session, key decisions made, open blockers, next step.
2. Run:
   ```
   repo-context-hooks checkpoint --message "SUMMARY"
   ```
   where SUMMARY covers: what was built, why each major decision was made, what remains.
3. Update `## Open Issues and Next Work` in `specs/README.md` to reflect current state — the next agent will load this section first.

## On PostCompact

1. Re-read `specs/README.md` — reconstruct working context from repo state, not session memory.
2. Resume from `## Open Issues and Next Work`.

## On SessionEnd

Write a full handoff so the next session starts with zero rediscovery cost:

1. Write a handoff summary covering:
   - What was shipped or changed
   - Key design/product decisions and the rationale behind each
   - Any constraints, dead ends, or reversals discovered
   - Exact next step (specific, not vague)
2. Run:
   ```
   repo-context-hooks checkpoint --message "HANDOFF"
   ```
3. Update `## Open Issues and Next Work` in `specs/README.md` — this is the first thing the next session reads.

## Checkpoint Message Format

Write the message as a dense, scannable block — not prose. Example:

```
Built: JWT refresh endpoint + migration 0014. Decided to store refresh tokens in Redis (not DB) to avoid write contention under load. Tried storing in DB first — reverted after load test showed 3x latency spike. Next: wire refresh token validation into auth middleware.
```

Fields to include (as applicable):
- **Built:** what was actually shipped/committed
- **Decided:** key choices made and why
- **Reverted/failed:** dead ends so the next agent doesn't repeat them
- **Next:** the exact next task, specific enough to start without rereading the full thread

## Workspace Contract (what to read and write)

- `specs/README.md` - engineering memory: current work, constraints, next step, open decisions, session log
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
- Writing vague checkpoints ("worked on auth") - write specific decisions and rationale
- Not updating `## Open Issues and Next Work` - session start context becomes stale
- Forgetting to run `repo-context-hooks checkpoint` before compaction or session end
- Installing per-repo hook entries without the agent-home skill - hooks fire but the skill is not loaded
