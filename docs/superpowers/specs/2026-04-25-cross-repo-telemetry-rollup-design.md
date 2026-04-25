# Cross-Repo Telemetry Rollup Design

## Problem

The first monitoring slice proved a single repo could show local hook evidence, but the product goal is broader: measure whether context-handoff hooks help across the developer's actual project ecosystem.

The user also wants the system to catch context-window pressure before auto-compact. That cannot be universal by default because not every editor, agent, or model runner exposes context-window fullness or a pre-compact lifecycle event. Claude can expose native lifecycle hooks. VS Code extensions, local runners, and wrappers need a generic command they can call when they know token usage.

## Product Direction

Build two complementary surfaces:

- `record-context`: a generic telemetry input for any extension or wrapper that can report used tokens and context limit.
- `rollup`: a cross-repo aggregation command that scans the shared local telemetry store and shows hook evidence across all observed repositories.

This keeps the product honest. It records the "1% before auto-compact" behavior when a platform or wrapper can supply the signal, but it does not claim to inspect every model's private context window automatically.

## Design

### Context Window Telemetry

`repo-context-hooks record-context` accepts:

- `--used-tokens`
- `--limit-tokens`
- `--threshold-percent`, default `99`
- `--checkpoint`
- `--source`
- `--agent-platform`
- `--model-name`
- `--session-id`

When usage is below threshold, it records `context-window-sample`. When usage reaches the threshold, it records `context-window-threshold`. With `--checkpoint`, it also records `pre-compact` so the rollup can show that the context-pressure signal triggered a checkpoint event.

### Cross-Repo Rollup

`repo-context-hooks rollup` scans the telemetry root for every `events.jsonl` file and aggregates:

- repositories observed
- total events
- agent sessions
- context-window threshold events
- checkpoint events
- per-repo score, uplift, lifecycle coverage, event mix, and max context usage

The rollup supports text, JSON, Prometheus/OpenMetrics, and sanitized snapshot output.

`--projects-root` also scans repo-local fallback telemetry under child project folders. This matters when sandboxing prevents writes to the shared OS cache and telemetry falls back to `.repo-context-hooks/telemetry/` inside each repo.

### Public Snapshot

`repo-context-hooks rollup --snapshot-dir docs/rollup` writes:

- `docs/rollup/index.html`
- `docs/rollup/rollup.json`

The snapshot excludes raw telemetry paths, prompts, source code, compact summaries, resumes, issue bodies, and secrets.

## Claim Boundary

This phase makes context-pressure telemetry operational, but it does not create a VS Code extension. VS Code, Cursor, Codex wrappers, Ollama wrappers, or other model runners must call `record-context` when they can observe token usage.

Native lifecycle hooks remain platform-specific. Claude is the strongest current path for automatic session and compact lifecycle events.
