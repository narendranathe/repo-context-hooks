# PRD: Session-Level Metrics Sampling

## Overview

The existing telemetry records every lifecycle event individually to a local OS-cache JSONL file with no session grouping, no sampling gate, and no automatic repo snapshot. This PRD adds session-level grouping (events share a session ID), probabilistic sampling (record only N% of sessions to avoid overhead), and automatic repo snapshot commits at SessionEnd so `docs/monitoring/history.json` stays current without manual CLI invocations.

## Problem Statement

1. **No session identity** - there is no way to tell which events belong to the same agent invocation. `session-start`, `pre-compact`, `post-compact`, and `session-end` appear as unrelated rows in the JSONL log.
2. **100% event recording** - every lifecycle event in every session is written, which will cause the local JSONL to grow unboundedly as usage scales. There is no sampling gate.
3. **Manual snapshot only** - `docs/monitoring/history.json` only updates when the developer manually runs `repo-context-hooks measure --snapshot-dir docs/monitoring`. There is no automatic update at session end.

Without session IDs and sampling, impact analytics cannot be trusted as real behavioral signals, and the repo-embedded snapshot becomes stale.

## Detailed Description

### Session ID

Each agent invocation is a session. All events within one invocation must share a common `session_id` so that analytics can compute per-session duration, lifecycle coverage, and compact frequency.

A session ID is a UUID4 generated once at the first lifecycle event of a session. It is persisted to a temp file (`.repo-context-hooks/current-session-id`) for the duration of the session. Subsequent events in the same invocation read the same ID. At `session-end`, the temp file is deleted.

The `REPO_CONTEXT_HOOKS_SESSION_ID` env var can override the generated ID (for testing).

### Probabilistic Sampling

Recording every session in a busy development environment adds friction and inflates the event log with low-signal data. The sampling gate decides: for each new session (first lifecycle event), flip a weighted coin. If sampled=True, record all events for that session. If sampled=False, skip all events for that session silently.

Default sample rate: **30%**. Configurable via `REPO_CONTEXT_HOOKS_SAMPLE_RATE` env var (float 0.0-1.0). The sampling decision is persisted alongside the session ID so it stays consistent across all lifecycle events in one session.

### Session Summary Record

At `session-end`, emit a special `session_summary` event (in addition to the regular `session-end` event) containing:
- `session_id`
- `session_start` (ISO timestamp of first event in this session)
- `session_end` (ISO timestamp of SessionEnd)
- `duration_seconds` (float)
- `lifecycle_events` (list of event names in order)
- `compact_count` (number of pre-compact + post-compact pairs)
- `workspace` (repo_name + branch)

### Auto-Snapshot at SessionEnd

At `session-end`, after recording events, call `write_public_monitoring_snapshot(report, output_dir)` with `output_dir = repo_root / "docs" / "monitoring"`. If the resulting `history.json` differs from what is already committed, stage and commit it automatically using `git add docs/monitoring/ && git commit -m "chore: update monitoring snapshot [skip ci]"`.

The commit is skipped if: no `.git` directory exists, git exits non-zero, or `docs/monitoring/` is listed in `.gitignore`.

## User Stories

- As a developer, I want all events from one agent session to share a session ID so I can trace the full lifecycle arc of a session in analytics.
- As a tool maintainer, I want only 30% of sessions sampled by default so the event log stays manageable without manual pruning.
- As a team lead, I want `docs/monitoring/history.json` to update automatically at session end so the repo always reflects real usage data.
- As a data analyst, I want session summary records with duration and compact count so I can benchmark continuity health over time.

## Acceptance Criteria

- [ ] `record_event()` includes `session_id` field in every JSONL record
- [ ] `session_id()` generates a UUID4 at first call and persists it to `.repo-context-hooks/current-session-id`; subsequent calls in the same session return the same ID
- [ ] `is_sampled()` returns True with probability equal to `REPO_CONTEXT_HOOKS_SAMPLE_RATE` (default 0.3)
- [ ] Hook scripts gate all `record_telemetry()` calls on `is_sampled()`, with sampling decision persisted for the session
- [ ] At `session-end`, a `session_summary` record is emitted with duration, lifecycle_events, and compact_count
- [ ] At `session-end`, `docs/monitoring/history.json` is updated and git-committed if changed (skipped silently when not in a git repo)
- [ ] `REPO_CONTEXT_HOOKS_SAMPLE_RATE=1.0` forces all sessions to be recorded (useful for tests and explicit `install` runs)
- [ ] All new behavior is covered by tests
- [ ] 142 existing tests continue to pass

## Non-Functional Requirements

- **Performance**: `session_id()` and `is_sampled()` must exit in <5ms; no blocking I/O in the hot path
- **Safety**: Auto-commit must never fail loudly - catch all exceptions, log to stderr, exit 0
- **Privacy**: Session summary records must not include file contents, prompts, or compact summaries - only counts and timestamps

## Technical Context (verified from repo)

### Existing Code Affected

- `repo_context_hooks/telemetry.py:163-191` - `record_event()` adds `session_id` field; no other signature change
- `repo_context_hooks/bundle/skills/context-handoff-hooks/scripts/repo_specs_memory.py:201-218` - `record_telemetry()` gates on `is_sampled()`
- `repo_context_hooks/bundle/skills/context-handoff-hooks/scripts/session_context.py:107-132` - `record_telemetry()` gates on `is_sampled()`

### Established Patterns to Follow

- Env var overrides: `REPO_CONTEXT_HOOKS_TELEMETRY_DIR` pattern from `_default_telemetry_base()` in `telemetry.py:32-46`
- Fallback cascade: `telemetry_dir()` tries OS cache first, falls back to `.repo-context-hooks/` - same pattern for `current-session-id` temp file
- Silent failure: `record_telemetry()` helpers wrap everything in `try/except pass` - same pattern for auto-commit

### Dependencies

- Existing: `json`, `hashlib`, `datetime`, `subprocess`, `pathlib`, `uuid` (all stdlib, no new deps)

## Module Breakdown

### Module A: `telemetry.session_id()` and `telemetry.is_sampled()`
- **Responsibility:** Generate and persist a session ID; gate recording with probabilistic sampling
- **Interface:** `session_id(repo_root: Path) -> str` | `is_sampled(repo_root: Path, rate: float = 0.3) -> bool`
- **Dependencies:** nothing new
- **Complexity:** S
- **Key files:** `repo_context_hooks/telemetry.py` (modify)

### Module B: `record_event()` session_id injection
- **Responsibility:** Include `session_id` field in every JSONL record
- **Interface:** `record_event(..., session_id: str | None = None)` - auto-calls `session_id(repo_root)` if not provided
- **Dependencies:** Module A
- **Complexity:** S
- **Key files:** `repo_context_hooks/telemetry.py` (modify)

### Module C: Hook script sampling gate
- **Responsibility:** Gate `record_telemetry()` on `is_sampled()`; persist sampling decision for session; emit `session_summary` at `session-end`
- **Interface:** internal to hook scripts
- **Dependencies:** Module A + B
- **Complexity:** M
- **Key files:** `repo_context_hooks/bundle/skills/context-handoff-hooks/scripts/repo_specs_memory.py`, `session_context.py` (modify)

### Module D: Auto-snapshot at SessionEnd
- **Responsibility:** At session-end, write `docs/monitoring/history.json` and git-commit if changed
- **Interface:** `auto_commit_snapshot(repo_root: Path) -> bool` in `telemetry.py`
- **Dependencies:** Module A + B + C (needs session_id context and events to exist)
- **Complexity:** M
- **Key files:** `repo_context_hooks/telemetry.py` (modify), hook script `repo_specs_memory.py` (call at session-end)

### Module E: Tests
- **Responsibility:** TDD tests for session_id, is_sampled, session_summary record, auto-commit behavior
- **Interface:** `tests/test_session_metrics.py` (new)
- **Dependencies:** Modules A-D
- **Complexity:** M
- **Key files:** `tests/test_session_metrics.py` (new)

## Dependency Graph

```
A (session_id + is_sampled)
├── B (record_event session_id injection) - blocked by A
├── C (hook script sampling gate + session_summary) - blocked by A + B
│   └── D (auto-snapshot at SessionEnd) - blocked by A + B + C
└── E (tests) - blocked by A + B + C + D
```

## Out of Scope

- Remote telemetry / opt-in community metrics (tracked in Issue #26)
- Sampling rate persistence in `settings.json` (env var is sufficient for MVP)
- MCP cold-memory layer (v0.5.0 backlog)
- Codex/non-Claude auto-commit (Codex has no SessionEnd hook today)

## Open Questions

- Should `REPO_CONTEXT_HOOKS_SAMPLE_RATE=1.0` be the default during `install` runs so the first real session is always recorded? (Proposed: yes.)
- Should the auto-commit be skipped if the repo has uncommitted staged changes? (Proposed: yes, skip and log warning.)

## Definition of Done

- [ ] All acceptance criteria met
- [ ] `tests/test_session_metrics.py` passes (RED->GREEN TDD cycle strictly followed)
- [ ] 142 existing tests still pass (no regressions)
- [ ] `docs/monitoring/history.json` updated with at least one session_summary record
- [ ] Code reviewed and committed to `feat/agent-level-skill-runtime`
