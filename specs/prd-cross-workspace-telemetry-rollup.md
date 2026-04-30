# PRD: Cross-Workspace Telemetry Rollup (`measure --all-repos`)

> **Parent PRD:** [#68 v1.0 production-readiness hardening](https://github.com/narendranathe/repo-context-hooks/issues/68)
> **Sibling milestones:** #73 self-observability, #74 install/uninstall UX
> **Status:** DRAFT — pending owner approval, then `/prd-to-issues`

## Overview

Today the `repo-context-hooks measure` command computes continuity score and tokens-saved for **one** repo at a time. Users who install the skill globally (per `repo-context-hooks install --platform claude`) accumulate telemetry across hundreds of workspaces, but have no way to roll up the fleet-level value the skill has delivered. This PRD adds `measure --all-repos`: a read-only aggregator that walks every workspace under the local telemetry root and produces a single fleet summary.

## Problem Statement

**Real local evidence (measured 2026-04-29):**

- `%LOCALAPPDATA%\repo-context-hooks\telemetry\` contains **510 workspace directories**, **676 distinct agent sessions**, and **624 `session-start` events** spread across `events.jsonl` files.
- `repo-context-hooks measure --repo-root .` only sees the *current* repo's slice. To answer *"how many tokens has the skill saved across every agent and every repo on this machine?"*, the user wrote a one-off Python script (`C:\Users\naren\AppData\Local\Temp\rch_telemetry_rollup.py`).
- That script computed: **374,400 tokens saved**, **$1.12 cost saved (Claude input @ $3/Mtok)**, top-15 workspaces table dominated by `repohandoff (107 starts)`, `repo-context-hooks (38+29 starts across two worktrees)`, `feat-sampling-roi (28 starts)`.

**Cost of not doing it.** The most compelling evidence that this skill *works* is invisible to the person who installed it. Without a built-in rollup:

1. Users can't articulate "what has this saved me" without bespoke shell scripts.
2. The repo-level dashboard underrepresents fleet value by 10-50x.
3. Adoption demos and case studies require manual Python plumbing every time.
4. There is no standard schema for fleet rollup, so any third-party reporting tool would have to invent one.

## Detailed Description

`measure --all-repos` walks every workspace directory under the resolved telemetry base (cross-platform: `LOCALAPPDATA` on Windows, `XDG_CACHE_HOME` or `~/.cache` on Linux/macOS, or `REPO_CONTEXT_HOOKS_TELEMETRY_DIR` if set), reads each `events.jsonl`, applies the same `_build_usability` substring-match formula already in `repo_context_hooks/telemetry.py`, and produces:

### Summary block

| Field | Definition | Source |
|---|---|---|
| `workspaces_total` | All workspace dirs read | filesystem walk |
| `workspaces_real` | After ghost filter | reuse `purge_ghost_repos` classifier |
| `workspaces_ghost` | Filtered out | difference |
| `sessions_distinct` | `len({session_id})` across all events | events |
| `events_total` | Sum of all JSONL lines parsed | events |
| `event_counts` | Dict `{event_name -> count}` | events |
| `session_starts` | Substring match `"session-start" in event_name` | events |
| `tokens_injected` | `session_starts * 4500` | formula at [telemetry.py:783](../repo_context_hooks/telemetry.py#L783) |
| `tokens_saved` | `round(session_starts * 0.30 * 2000)` | formula at [telemetry.py:785](../repo_context_hooks/telemetry.py#L785) |
| `cost_saved_usd` | `round(tokens_saved / 1_000_000 * 3.0, 3)` | formula at [telemetry.py:786](../repo_context_hooks/telemetry.py#L786) |
| `telemetry_base` | Resolved root path (string) | `_default_telemetry_base()` |

### Per-workspace block (sorted desc by `tokens_saved`, truncated to `--top N`)

`repo_id`, `repo_name` (or hashed if `--redact`), `branches[:3]`, `events_total`, `sessions`, `session_starts`, `pre_compact`, `post_compact`, `session_end`, `score` (latest `repo_contract_score`), `baseline` (latest `estimated_baseline_score`), `tokens_saved`, `is_ghost` (bool).

### Default text rendering

```
==============================================================================
repo-context-hooks  Fleet Rollup
==============================================================================
Telemetry root          : C:\Users\naren\AppData\Local\repo-context-hooks\telemetry
Workspaces (real)       : 25  (485 ghosts excluded; --include-ghosts to show)
Distinct sessions       : 676
Total events            : 754
session-start           : 624
Tokens injected (ctx)   : 2,808,000
Tokens SAVED (vs cold)  : 374,400      (30% × 2,000 tok re-orient avoided)
Cost saved (Claude in)  : $1.12

Top 15 workspaces by tokens saved
------------------------------------------------------------------------------
repo_id           name                        sess  starts     saved  score
abf293c549492716  repohandoff                   82     107    64,200  90/20
db9f15a890d32e9c  repo-context-hooks            38      38    22,800  90/20
...
```

### `--json` schema (stable contract)

```json
{
  "schema_version": 1,
  "summary": {
    "telemetry_base": "...",
    "workspaces_total": 510,
    "workspaces_real": 25,
    "workspaces_ghost": 485,
    "sessions_distinct": 676,
    "events_total": 754,
    "event_counts": {"session-start": 509, "session-context-session-start": 115, "decision": 66, "pre-compact": 64},
    "session_starts": 624,
    "tokens_injected": 2808000,
    "tokens_saved": 374400,
    "cost_saved_usd": 1.123
  },
  "repos": [
    {"repo_id": "abf293c549492716", "repo_name": "repohandoff", "sessions": 82, "session_starts": 107,
     "tokens_saved": 64200, "score": 90, "baseline": 20, "is_ghost": false, ...}
  ]
}
```

## User Stories

- As a **solo developer** who installed `repo-context-hooks` globally, I want one command that tells me how much continuity value the skill has delivered across every repo I've worked in, so I can verify the install was worth it.
- As a **maintainer** showing the project to a stranger, I want to paste a summary that says "374k tokens saved across 25 real workspaces" without writing a custom script.
- As a **CI / scripting consumer**, I want `--all-repos --json` with a stable, versioned schema so I can build dashboards or weekly digests on top of it.
- As a **privacy-conscious user**, I want `--redact` to hash workspace names before they appear in my export, mirroring `measure export --redact`.
- As a **noise-conscious user**, I want ghost dirs (test runs, ephemeral worktrees) excluded by default but accessible via `--include-ghosts`.

## Acceptance Criteria

- [ ] `repo-context-hooks measure --all-repos` runs cleanly on a populated telemetry base and prints the text summary above.
- [ ] `repo-context-hooks measure --all-repos --json` emits the JSON schema above. `schema_version: 1` is set.
- [ ] `--top N` controls the table size. Default is 15. `--top 0` means show all.
- [ ] `--include-ghosts` flips the ghost filter off; without it, the existing `purge_ghost_repos` ghost classifier is applied (read-only, no deletion).
- [ ] `--redact` replaces `repo_name` with `sha256(repo_name)[:12]` in both text and JSON output.
- [ ] `tokens_saved` formula is identical to `_build_usability`'s `resume_events * 0.30 * 2000` — same substring match (`"session-start" in event_name`).
- [ ] `REPO_CONTEXT_HOOKS_TELEMETRY=0` causes the rollup to print a single line ("Telemetry disabled; rollup is opt-out.") and exit 0 without reading any files.
- [ ] `REPO_CONTEXT_HOOKS_TELEMETRY_DIR` override is honored.
- [ ] Empty telemetry base prints a friendly "no events found" message (not a crash).
- [ ] Corrupt JSONL lines are skipped silently (matches existing tolerance) — does not crash on a malformed line.
- [ ] Public-surface contract `tests/contract/public_surface.json` is updated to include `--all-repos`, `--include-ghosts`, `--top` flags under `measure`. Existing `--redact` and `--json` are reused.
- [ ] Unit tests cover: empty base, single-repo base, multi-repo with ghosts, redaction, top-N truncation, top-N=0, JSON schema shape, env opt-out, telemetry-dir override, corrupt JSONL.
- [ ] Integration test: build a synthetic telemetry tree with 3 fixture workspaces, run rollup, assert tokens_saved math matches the formula by hand.
- [ ] Coverage gate stays ≥ 85% (set by [#92](https://github.com/narendranathe/repo-context-hooks/issues/92)).
- [ ] `TELEMETRY.md` gets a "Fleet rollup" section pointing to the new flag.
- [ ] `docs/monitoring.md` cross-links the new command from the impact-monitor section.
- [ ] `CHANGELOG.md` Unreleased section gets a `Added: measure --all-repos cross-workspace rollup` line.

## Non-Functional Requirements

- **Performance:** Rollup over 1,000 workspaces with 100 events each (~100k JSONL lines) completes in under 2 seconds on a modern laptop. Streaming line-by-line read; no full-file slurp where avoidable.
- **Security / privacy:** Read-only. Never writes to telemetry dirs. `--redact` produces a path-free, name-hashed export. `REPO_CONTEXT_HOOKS_TELEMETRY=0` is a hard kill switch.
- **Cross-platform:** Verified on Windows (`LOCALAPPDATA`), Linux (`~/.cache`), macOS (`~/Library/Caches` is not used; we rely on `~/.cache` per existing `_default_telemetry_base`).
- **Stability contract:** New flags listed in `public_surface.json`. JSON schema is `schema_version: 1`; future-additive fields don't bump version.
- **Accessibility:** Table uses ASCII-only characters (no box-drawing) so it's safe for `>` redirection and `gh issue comment --body-file`.

## Technical Context (verified from repo)

### Existing code reused

| File | Function | Why |
|---|---|---|
| `repo_context_hooks/telemetry.py:41` | `_default_telemetry_base()` | Cross-platform path resolution + env override — already correct, no changes needed |
| `repo_context_hooks/telemetry.py:564` | `_build_usability()` formula | `tokens_saved = resume_events * 0.30 * 2000`; substring match on `"session-start" in name` |
| `repo_context_hooks/telemetry.py` | `purge_ghost_repos()` | Ghost-repo classifier; use its `is_ghost(repo_dir)` predicate (extract if private) |
| `repo_context_hooks/cli.py:170-263` | `measure` subparser | Add new flags; route in `_measure()` before `measure_impact()` call |
| `repo_context_hooks/cli.py:528` | `_measure()` | Add early-return branch for `args.all_repos` |
| `tests/contract/public_surface.json:30-32` | `measure` cli_commands entry | Extend `flags` array |

### Established patterns followed

- **`--json` early-return + `to_dict()`** ([cli.py:646](../repo_context_hooks/cli.py#L646)): existing `measure --json` calls `report.to_dict()`. Mirror this for `RollupReport`.
- **Subcommand-style flags on measure** ([cli.py:528-611](../repo_context_hooks/cli.py#L528-L611)): `--clean-ghosts`, `--branches`, `--forecast`, `--badge` all branch early in `_measure()`. `--all-repos` is a 5th branch with the same shape.
- **Dataclass-style reports** ([telemetry.py:377](../repo_context_hooks/telemetry.py#L377) `UsabilityMetrics`): `RollupReport` follows the same `@dataclass` + `to_dict()` + `render()` pattern.
- **Redaction**: `measure export --redact` already exists. Reuse the same flag and the same hashing helper.
- **Ghost classification**: `purge_ghost_repos(dry_run=True)` exists. Refactor to expose a side-effect-free predicate.

### Dependencies

- **Existing only.** No new pip deps. `hashlib`, `json`, `pathlib`, `dataclasses`, `os` — all stdlib, all already imported in `telemetry.py`.

## Module Breakdown

### Module 1: `RollupReport` dataclass

- **Responsibility:** Carry rollup data; render to text and JSON.
- **Interface:**
  - `RollupReport(summary: RollupSummary, repos: list[RollupRepo], schema_version: int = 1)`
  - `to_dict() -> dict[str, Any]`
  - `render(top_n: int = 15) -> str`
- **Dependencies:** none (pure data)
- **Files:** `repo_context_hooks/telemetry.py` (extend; do not new-file)
- **Complexity:** S

### Module 2: Ghost-classifier extraction

- **Responsibility:** Expose the existing ghost-detection logic from `purge_ghost_repos` as a side-effect-free predicate `is_ghost_repo(repo_dir: Path) -> bool`.
- **Interface:** `def is_ghost_repo(repo_dir: Path) -> bool`
- **Dependencies:** none
- **Files:** `repo_context_hooks/telemetry.py` (refactor — no behavior change to `purge_ghost_repos`)
- **Complexity:** S

### Module 3: `rollup_telemetry()` aggregator

- **Responsibility:** Walk telemetry base, parse every `events.jsonl`, apply ghost filter, compute summary + per-repo records, sort by `tokens_saved` desc, return `RollupReport`.
- **Interface:** `def rollup_telemetry(*, base: Path | None = None, include_ghosts: bool = False) -> RollupReport`
- **Dependencies:** Module 1, Module 2, `_default_telemetry_base`
- **Files:** `repo_context_hooks/telemetry.py`
- **Complexity:** M

### Module 4: Redaction helper

- **Responsibility:** Hash `repo_name` to a 12-char SHA-256 prefix when redaction is requested.
- **Interface:** `def redact_repo_name(name: str) -> str`
- **Dependencies:** `hashlib` (already imported)
- **Files:** `repo_context_hooks/telemetry.py`
- **Complexity:** S

### Module 5: CLI wiring

- **Responsibility:** Add `--all-repos`, `--include-ghosts`, `--top` to the `measure` argparse subparser. Add an early-return branch in `_measure()` that calls `rollup_telemetry()`, applies redaction if `--redact`, and emits text or JSON.
- **Interface:** argparse + handler branch
- **Dependencies:** Modules 1, 3, 4
- **Files:** `repo_context_hooks/cli.py`
- **Complexity:** S

### Module 6: Public-surface contract update

- **Responsibility:** Extend `tests/contract/public_surface.json` `measure.flags` array with `--all-repos`, `--include-ghosts`, `--top`. Existing `--redact` and `--json` need no change.
- **Interface:** JSON edit
- **Dependencies:** Module 5
- **Files:** `tests/contract/public_surface.json`
- **Complexity:** S

### Module 7: Tests

- **Responsibility:** Cover all acceptance criteria. Use `tmp_path` fixture to build synthetic telemetry trees.
- **Interface:** pytest test cases
- **Dependencies:** Modules 1-6
- **Files:**
  - `tests/test_telemetry_rollup.py` (new — unit tests for `rollup_telemetry`, `is_ghost_repo`, `RollupReport.to_dict/render`, `redact_repo_name`)
  - `tests/test_cli_measure_all_repos.py` (new — CLI plumbing, JSON schema, env opt-out)
  - existing contract test picks up the contract change automatically
- **Complexity:** M

### Module 8: Docs

- **Responsibility:** User-facing docs.
- **Interface:** Markdown edits.
- **Dependencies:** Module 5 (must reflect shipped CLI)
- **Files:** `TELEMETRY.md`, `docs/monitoring.md`, `CHANGELOG.md`, `specs/README.md` (Built So Far entry on PR merge)
- **Complexity:** S

## Dependency Graph

```
                    ┌──────────────────────┐
                    │ M2: is_ghost_repo    │  ◄── refactor, no behavior change
                    └──────────────────────┘
                                │
                                ▼
┌──────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│ M4: redact   │     │ M3: rollup_telemetry │     │ M1: RollupReport │
└──────────────┘     └──────────────────────┘     └──────────────────┘
        │                       │                          │
        └───────────┬───────────┴──────────────────────────┘
                    ▼
            ┌──────────────────┐
            │ M5: CLI wiring   │ ─────► M6: public_surface.json contract
            └──────────────────┘
                    │
                    ▼
            ┌──────────────────┐
            │ M7: Tests        │
            └──────────────────┘
                    │
                    ▼
            ┌──────────────────┐
            │ M8: Docs         │
            └──────────────────┘
```

**Suggested implementation order (and child-issue split for `/prd-to-issues`):**

1. M2 ghost-classifier extraction (refactor; no behavior change; merges first)
2. M1 + M3 + M4 (telemetry-core slice — `RollupReport`, `rollup_telemetry`, `redact_repo_name` + their unit tests)
3. M5 + M6 (CLI surface + contract update + CLI tests)
4. M7 integration test against a synthetic 3-workspace tree
5. M8 docs (TELEMETRY.md, monitoring.md, CHANGELOG)

Each is a vertical slice that can ship a green PR independently.

## Out of Scope

- **Date filtering** (`--since`, `--last Nd`) — deferred to a follow-up issue.
- **HTML "fleet" view** in the existing `measure --open` dashboard — deferred.
- **Remote / multi-machine aggregation** — covered by [#26](https://github.com/narendranathe/repo-context-hooks/issues/26) "Build consented remote telemetry and MCP reporting"; explicitly NOT this PRD.
- **Team-scope multi-developer rollup** — single-developer only.
- **Editing or pruning telemetry** — read-only. `--clean-ghosts` already covers pruning.
- **New tokens-saved formula** — uses existing `_build_usability` math verbatim. Tuning that formula is its own PRD.
- **Per-source breakdown UI** (`repo_specs_memory` vs `session_context`) — included in JSON `event_counts` but not surfaced in the text table.

## Open Questions

- *Resolved during grilling:* CLI shape (B), ghost default (A), date window (A — deferred), redaction (A), top-N default (B — 15), HTML (A — deferred).
- **Q (implementation):** Should `is_ghost_repo` live in `telemetry.py` or migrate to a tiny `repo_context_hooks/_ghosts.py` for testability? Defer to implementer.
- **Q (test fixtures):** Should the synthetic-telemetry helper become a shared `tests/conftest.py` fixture so future tests reuse it? Likely yes; flag during M7.

## Definition of Done

- [ ] All 14 acceptance criteria above checked.
- [ ] `pytest tests/ -v` green; coverage ≥ 85% (CI gate from #92).
- [ ] `python scripts/check_public_surface.py` green (contract gate).
- [ ] `ruff check` and `black --check` clean.
- [ ] `mypy` clean (matches existing project bar).
- [ ] PR opened, reviewed, and merged into `main`.
- [ ] CHANGELOG entry under `Unreleased` → `Added`.
- [ ] PRD parent issue (this one) closed by merge of the docs PR.
- [ ] Manual smoke: run `repo-context-hooks measure --all-repos` on the maintainer's local machine, paste output into a closing comment as evidence.

---

**Approved by:** _pending_
**Approved on:** _pending_
**Implementation tracking:** child issues from `/prd-to-issues` will reference this PRD as parent.
