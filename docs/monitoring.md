# Monitoring And Impact Evidence

`repo-context-hooks` includes local monitoring so maintainers can prove the continuity loop is active and compare a repo's current readiness against a no-continuity baseline.

This is not a hosted analytics product. It is a local evidence layer for agent-enabled repositories.

Remote telemetry is not enabled in the MVP. If remote community metrics are added later, they must be explicit opt-in and follow [Telemetry Policy](telemetry-policy.md).

## Quick Start

Run a measurement before installing any platform adapter:

```bash
repo-context-hooks measure
```

Install the strongest available adapter for lifecycle evidence:

```bash
repo-context-hooks install --platform claude
```

Start a new agent session, run a compact flow, or end a session so the hooks have a chance to fire. Then measure again:

```bash
repo-context-hooks measure
```

For scripts, dashboards, and CI experiments:

```bash
repo-context-hooks measure --json
repo-context-hooks measure --prometheus
```

To intentionally refresh a checked-in public dashboard from local evidence:

```bash
repo-context-hooks measure --snapshot-dir docs/monitoring
```

The public snapshot for this repo lives at [docs/monitoring/index.html](monitoring/index.html). It is a checked-in snapshot, while the local hook-generated dashboard keeps updating in the telemetry directory. The public snapshot writer sanitizes local paths and publishes aggregate scores, event counts, lifecycle coverage, and time-series usability only.

The README-facing graph lives at [docs/monitoring/timeseries.svg](monitoring/timeseries.svg). It is generated from the same `history.json` snapshot, so the public graphic is evidence-backed instead of a hand-authored metric claim.

The graph intentionally compares the model/session-only baseline against repo continuity. It also shows previous-vs-latest telemetry days, score trend, hook-event volume, agent/model comparison, event mix, lifecycle coverage, and the source fields used by the renderer.

For Prometheus/OpenMetrics, Grafana, and Datadog usage paths, see [Observability Integrations](observability.md).

## Visualization Tools

The MVP intentionally keeps visualization boring in the best way: one generated README SVG, one static HTML dashboard, and one portable JSON file. That makes the data easy to inspect without introducing a hosted telemetry service.

Good next visualization surfaces:

- GitHub README: embed `docs/monitoring/timeseries.svg` so the repo landing page shows an actual time-series graph.
- GitHub Pages: publish the static monitor as a shareable dashboard.
- Observable Plot: import `docs/monitoring/history.json` and chart score, event volume, and lifecycle coverage.
- Vega-Lite: embed a declarative time-series chart in docs or a portfolio case study.
- Evidence, DuckDB, or SQLite: analyze longer local telemetry history across many repos or sessions.

Suggested README-facing metrics:

- continuity score
- uplift over the README-only baseline
- observed hook events
- active days
- lifecycle coverage
- resume, checkpoint, reload, and session-end counts

## What Gets Measured

The report includes:

- current continuity score
- estimated baseline score without repo continuity
- estimated uplift
- agent platform and model-name comparison
- observed hook and skill events
- event counts by lifecycle stage
- score time series
- daily event counts
- active days
- resume events
- checkpoint events
- reload events
- session-end events
- lifecycle coverage
- local evidence-log path
- recommendations for missing setup

The score is intentionally simple. It rewards the repo contract files that help a fresh agent resume work:

- `README.md`
- `specs/README.md`
- required engineering-memory sections
- `UBIQUITOUS_LANGUAGE.md`
- `AGENTS.md`
- `CLAUDE.md`
- Claude lifecycle hook registration when available

The baseline is intentionally conservative: it estimates what a repo has if an agent can only rely on the user-facing README and no continuity contract.

## Evidence Storage

Hook scripts append small JSONL events to a local cache directory by default, not to the repository.

Default locations:

- Windows: `%LOCALAPPDATA%\repo-context-hooks\telemetry\`
- macOS/Linux: `$XDG_CACHE_HOME/repo-context-hooks/telemetry/` or `~/.cache/repo-context-hooks/telemetry/`

Override the location when testing or collecting a shareable experiment:

```bash
set REPO_CONTEXT_HOOKS_TELEMETRY_DIR=C:\tmp\repo-context-hooks-telemetry
repo-context-hooks measure
```

If the OS cache path is unavailable in a sandboxed environment, the CLI falls back to `.repo-context-hooks/telemetry/` inside the repo. `repo-context-hooks init` adds `.repo-context-hooks/` to `.gitignore` so fallback telemetry does not become commit noise.

PowerShell users can set it for the current shell:

```powershell
$env:REPO_CONTEXT_HOOKS_TELEMETRY_DIR = "C:\tmp\repo-context-hooks-telemetry"
repo-context-hooks measure
```

## Privacy Boundary

Telemetry is local-only by default.

Events include:

- timestamp
- event name
- event source
- agent platform
- model name when provided
- hashed repo id
- repo folder name
- git branch name
- repo continuity score
- estimated baseline score
- small event details such as counts and local file paths

Events do not upload code, prompts, compact summaries, issue bodies, or file contents.

Set these environment variables when you want explicit platform/model labels in new telemetry events:

```bash
REPO_CONTEXT_HOOKS_AGENT_PLATFORM=codex
REPO_CONTEXT_HOOKS_MODEL_NAME=gpt-5.5
repo-context-hooks measure
```

If they are not set, hook sources such as Claude lifecycle scripts are inferred when possible and the model is shown as `unknown model` in public graphs.

No cookies are used by the CLI. Cookies are only appropriate for a future optional web dashboard, not for hook or MCP telemetry.

## Before And After Workflow

Use this sequence when you want evidence for a README, blog post, internal adoption note, or recruiter-facing demo:

1. Run `repo-context-hooks measure` before setup and save the output.
2. Run `repo-context-hooks init`.
3. Run `repo-context-hooks doctor`.
4. Run `repo-context-hooks install --platform claude` for native hook evidence, or install the best partial adapter for your platform.
5. Start a new agent session and do real work.
6. Trigger a compact or session-end flow when available.
7. Run `repo-context-hooks measure` again.
8. Compare the uplift, observed events, and recommendations.
9. If the evidence is shareable, run `repo-context-hooks measure --snapshot-dir docs/monitoring` and review the generated files before committing them.

The snapshot command writes:

- `docs/monitoring/index.html`
- `docs/monitoring/history.json`
- `docs/monitoring/timeseries.svg`

For reproducible comparisons:

```bash
repo-context-hooks measure --json > before.json
repo-context-hooks init
repo-context-hooks install --platform claude
repo-context-hooks measure --json > after.json
repo-context-hooks measure --snapshot-dir docs/monitoring
```

## How To Interpret It

Good signs:

- current score is much higher than baseline
- event counts include session-start and compact or session-end events
- recommendations shrink after setup
- telemetry path points outside the git repo, or under ignored `.repo-context-hooks/` when sandbox fallback is needed

Weak signs:

- current score is close to baseline
- no observed events after agent usage
- `AGENTS.md` is missing for partial platforms
- Claude hook registration is missing when native support is expected

This evidence is not a scientific productivity benchmark. It is a practical continuity audit: did the repo contain enough context, did the hooks fire, and can the next agent see a better handoff than a bare README?
