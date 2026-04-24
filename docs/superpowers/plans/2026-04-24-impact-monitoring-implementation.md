# Impact Monitoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build local impact monitoring for repo continuity hooks and skills.

**Architecture:** Add a focused telemetry module, expose it through `repo-context-hooks measure`, and emit JSONL events from bundled hook scripts. Keep storage local, privacy-preserving, and outside the git repo by default.

**Tech Stack:** Python standard library, pytest, existing CLI module, existing bundle scripts.

---

### Task 1: Telemetry Core

**Files:**
- Create: `repo_context_hooks/telemetry.py`
- Test: `tests/test_telemetry.py`

- [x] **Step 1: Write failing tests for event recording and impact reporting**

Expected tests:

```python
from repo_context_hooks.telemetry import measure_impact, record_event, telemetry_dir
```

Expected failure: `ModuleNotFoundError` or missing functions.

- [x] **Step 2: Implement local JSONL telemetry**

Implementation includes:

- repo hash id
- repo name
- branch
- event name
- source
- continuity score
- estimated baseline score
- event details

- [x] **Step 3: Add cache fallback**

Default to OS cache. If unavailable, fall back to `.repo-context-hooks/telemetry/`.

- [x] **Step 4: Verify tests**

Run:

```bash
python -m pytest -q tests/test_telemetry.py --basetemp .pytest-tmp-monitoring
```

Expected: telemetry tests pass.

- [x] **Step 5: Add time-series usability metrics**

Implementation includes:

- score series
- daily event counts
- active days
- resume events
- checkpoint events
- reload events
- session-end events
- lifecycle coverage
- local `monitoring.html` dashboard generation

### Task 2: CLI Command

**Files:**
- Modify: `repo_context_hooks/cli.py`
- Test: `tests/test_cli.py`

- [x] **Step 1: Write failing parser and JSON tests**

Expected behavior:

```bash
repo-context-hooks measure
repo-context-hooks measure --json
```

- [x] **Step 2: Add `_measure()` and parser wiring**

Implementation delegates to `measure_impact()`.

- [x] **Step 3: Verify CLI smoke**

Run:

```bash
python -m repo_context_hooks measure --json
```

Expected: JSON report with `current_score`, `estimated_baseline_score`, and `uplift`.

### Task 3: Hook Script Emission

**Files:**
- Modify: `repo_context_hooks/bundle/scripts/repo_specs_memory.py`
- Modify: `repo_context_hooks/bundle/scripts/session_context.py`
- Modify: `repo_context_hooks/bundle/skills/context-handoff-hooks/scripts/repo_specs_memory.py`
- Modify: `repo_context_hooks/bundle/skills/context-handoff-hooks/scripts/session_context.py`
- Test: `tests/test_repo_memory_contract.py`
- Test: `tests/test_bundle_integrity.py`

- [x] **Step 1: Write failing hook telemetry test**

Run a bundled script in a temp repo and assert an `events.jsonl` file is created.

- [x] **Step 2: Add safe `record_event()` calls**

Hook script telemetry must never fail the hook. Wrap telemetry imports and writes in `try/except`.

- [x] **Step 3: Keep duplicate skill scripts synchronized**

Both top-level runtime scripts and skill-bundled scripts include telemetry emission.

### Task 4: Docs And Repo Hygiene

**Files:**
- Modify: `README.md`
- Create: `docs/monitoring.md`
- Modify: `specs/README.md`
- Modify: `.gitignore`
- Modify: `repo_context_hooks/repo_contract.py`
- Modify: `repo_context_hooks/bundle/skills/context-handoff-hooks/SKILL.md`
- Modify: `repo_context_hooks/bundle/skills/context-handoff-hooks/README.md`

- [x] **Step 1: Add README proof section**

Document:

```bash
repo-context-hooks measure
repo-context-hooks measure --json
```

- [x] **Step 2: Add monitoring guide**

Explain metric definitions, privacy boundary, evidence storage, and before/after workflow.

- [x] **Step 3: Ignore repo-local telemetry fallback**

Add `.repo-context-hooks/` to `.gitignore` and ensure `init` appends it for target repos.

- [x] **Step 4: Add public monitoring and brand visuals**

Create:

- `assets/diagrams/context-continuity-engine.svg`
- `docs/monitoring/index.html`
- `docs/monitoring/history.json`

Update README with the hero visual, current score, uplift, lifecycle coverage, and dashboard link.

### Task 5: Verification

**Files:**
- Test suite

- [x] **Step 1: Run targeted tests**

```bash
python -m pytest -q tests/test_telemetry.py tests/test_cli.py tests/test_repo_memory_contract.py tests/test_bundle_integrity.py --basetemp .pytest-tmp-monitoring-targeted
```

- [x] **Step 2: Run full suite**

```bash
python -m pytest -q --basetemp .pytest-tmp-monitoring-full
```

Expected: full suite passes.
