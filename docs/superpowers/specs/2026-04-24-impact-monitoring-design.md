# Impact Monitoring Design

## Goal

Add a local evidence loop that proves `repo-context-hooks` is doing useful continuity work before users promote it to teams or the public.

The feature should answer four questions:

- Does this repo have a meaningful continuity contract?
- Did hooks or skills actually run?
- How much better is this repo's current continuity state than a bare README-only baseline?
- Is usability improving over time across real lifecycle events?

## Product Positioning

This is operational evidence, not a scientific productivity benchmark.

Good public language:

- "Measure continuity readiness and observed hook events."
- "Compare current repo continuity against an estimated no-continuity baseline."
- "Generate local JSON evidence you can inspect or feed into scripts."

Avoid:

- "Proves agents are X% more productive."
- "Hosted analytics."
- "Captures prompts or code."

## Architecture

The feature adds one module, `repo_context_hooks.telemetry`, and one CLI command, `repo-context-hooks measure`.

Hook scripts call `record_event()` after useful lifecycle work:

- `repo_specs_memory.py` records session-start, pre-compact, post-compact, and session-end events.
- `session_context.py` records session-context events and counts next-work, workflow, and issue signals.

`measure_impact()` reads local JSONL events and current repo-contract signals, then renders a human or JSON report. It also writes a local `monitoring.html` dashboard beside the JSONL event log so hook activity creates a living time-series view without dirtying the git repo.

The public repo can include a checked-in dashboard snapshot under `docs/monitoring/index.html`. That snapshot is marketing and documentation; the automatically updated monitor remains local unless the maintainer intentionally publishes a new snapshot.

## Storage

Telemetry is local-only by default.

Preferred storage:

- Windows: `%LOCALAPPDATA%\repo-context-hooks\telemetry\`
- macOS/Linux: `$XDG_CACHE_HOME/repo-context-hooks/telemetry/` or `~/.cache/repo-context-hooks/telemetry/`

Fallback storage:

- `.repo-context-hooks/telemetry/` inside the repo when OS cache access is blocked

`repo-context-hooks init` and the bundled skill installer add `.repo-context-hooks/` to `.gitignore`.

## Scoring

The current continuity score is intentionally transparent and deterministic:

- `README.md`
- `specs/README.md`
- required engineering-memory sections
- `UBIQUITOUS_LANGUAGE.md`
- `AGENTS.md`
- `CLAUDE.md`
- Claude lifecycle hook registration

The estimated baseline is the README-only state. This keeps the comparison honest: the report says "this repo now has more continuity infrastructure than a bare README," not "developer productivity improved by a controlled experimental amount."

## Usability Time Series

The report tracks:

- score series by day
- daily hook event counts
- active days
- resume events
- checkpoint events
- reload events
- session-end events
- lifecycle coverage
- minutes since the last observed hook event

These metrics are designed to answer whether the workflow is being used and whether it is staying healthy over time. They do not read source code or prompts.

## Visual Surface

The README should include a strong hero visual that explains the core mechanism:

- `README.md` carries the public story
- `specs/README.md` carries engineering memory
- `AGENTS.md` carries cross-agent re-entry
- hooks emit telemetry
- the impact monitor shows score, uplift, and event history

This visual is part of the product, not decoration. It helps developers understand why the repo exists before they read the implementation details.

## Self-Critique

The first version is deliberately simple. It does not track wall-clock task completion, model token usage, or interview-quality outcomes. That is the correct boundary for now because those measurements can become invasive, noisy, or misleading.

The most important next improvement is an explicit experiment runner that can generate `before.json` and `after.json` files in one guided flow. That should remain opt-in and should redact paths if users want to share public evidence.
