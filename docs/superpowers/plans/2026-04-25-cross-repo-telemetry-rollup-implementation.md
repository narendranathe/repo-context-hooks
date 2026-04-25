# Cross-Repo Telemetry Rollup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add context-window threshold telemetry and a cross-repo rollup dashboard for all repositories observed in the local telemetry store.

**Architecture:** Extend the existing telemetry module instead of adding a service. `record-context` writes local JSONL events with context-window details. `rollup` scans existing telemetry directories and renders aggregate text, JSON, Prometheus, and sanitized HTML/JSON snapshots.

**Tech Stack:** Python standard library, argparse, JSONL telemetry, static HTML snapshot output, pytest.

---

### Task 1: Context Window Telemetry Input

**Files:**
- Modify: `repo_context_hooks/telemetry.py`
- Test: `tests/test_telemetry.py`

- [x] **Step 1: Write the failing test**

```python
def test_record_context_window_records_threshold_and_checkpoint_event() -> None:
    event_path = record_context_window(
        repo,
        used_tokens=99_000,
        limit_tokens=100_000,
        threshold_percent=99,
        checkpoint=True,
        telemetry_base=telemetry_base,
        source="vscode-extension",
        agent_platform="codex",
        model_name="gpt-test",
    )
    events = [json.loads(line) for line in event_path.read_text().splitlines()]
    assert [event["event_name"] for event in events] == ["context-window-threshold", "pre-compact"]
```

- [x] **Step 2: Implement `record_context_window`**

Add a helper that computes usage percent, remaining percent, and threshold window. Record `context-window-threshold` when usage reaches the threshold and optional `pre-compact` when `checkpoint=True`.

- [x] **Step 3: Verify**

Run:

```bash
python -m pytest -q tests/test_telemetry.py::test_record_context_window_records_threshold_and_checkpoint_event
```

Expected: PASS.

### Task 2: Cross-Repo Rollup Aggregator

**Files:**
- Modify: `repo_context_hooks/telemetry.py`
- Test: `tests/test_telemetry.py`

- [x] **Step 1: Write the failing rollup tests**

Create two temp repos, emit events into the same telemetry base, and assert that `measure_rollup()` aggregates repo count, total events, sessions, threshold events, checkpoint events, and per-repo max context usage.

- [x] **Step 2: Implement rollup dataclasses and aggregation**

Add `RepoRollupSummary`, `RollupReport`, `measure_rollup`, and `render_rollup_prometheus_metrics`. Include `projects_root` scanning for repo-local fallback telemetry under child project folders.

- [x] **Step 3: Verify**

Run:

```bash
python -m pytest -q tests/test_telemetry.py::test_measure_rollup_aggregates_multiple_repo_event_logs
```

Expected: PASS.

### Task 3: CLI Wiring

**Files:**
- Modify: `repo_context_hooks/cli.py`
- Test: `tests/test_cli.py`

- [x] **Step 1: Add parser tests**

Assert that `rollup`, `rollup --json`, `rollup --prometheus`, and `record-context --used-tokens ... --limit-tokens ...` parse correctly.

- [x] **Step 2: Implement `_rollup` and `_record_context`**

Wire the CLI to telemetry functions and support JSON, Prometheus, and snapshot output.

- [x] **Step 3: Verify**

Run:

```bash
python -m pytest -q tests/test_cli.py::test_rollup_prints_json tests/test_cli.py::test_record_context_prints_threshold_status
```

Expected: PASS.

### Task 4: Docs And Public Snapshot

**Files:**
- Modify: `README.md`
- Modify: `docs/monitoring.md`
- Modify: `docs/observability.md`
- Create: `docs/rollup/index.html`
- Create: `docs/rollup/rollup.json`
- Test: `tests/test_readme_contract.py`
- Test: `tests/test_monitoring_surface.py`

- [x] **Step 1: Document the claim boundary**

Explain that native lifecycle hooks are platform-specific and that generic context-window telemetry requires wrappers/extensions to call `record-context`.

- [x] **Step 2: Generate rollup snapshot**

Run:

```bash
repo-context-hooks rollup --snapshot-dir docs/rollup
```

Expected: `docs/rollup/index.html` and `docs/rollup/rollup.json`.

- [x] **Step 3: Verify docs**

Run:

```bash
python -m pytest -q tests/test_readme_contract.py tests/test_monitoring_surface.py
```

Expected: PASS.
