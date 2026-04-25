# Observability Integrations

`repo-context-hooks` can export local continuity evidence as Prometheus/OpenMetrics text. That gives developers a practical monitoring story without turning the MVP into a hosted analytics product.

Telemetry collection happens at the agent-session level. Installed lifecycle hooks record events automatically; the CLI measurement commands read that evidence for inspection and export.

The goal is useful proof:

- show that hooks are firing over time
- show continuity score and uplift trends
- show lifecycle coverage across session start, compact, reload, and session end
- keep prompts, code, resume content, and local filesystem paths out of exported metrics

## Prometheus Export

Run:

```bash
repo-context-hooks measure --prometheus
repo-context-hooks rollup --prometheus
```

Example metric names:

```text
repo_context_hooks_continuity_score
repo_context_hooks_baseline_score
repo_context_hooks_uplift
repo_context_hooks_observed_events_total
repo_context_hooks_lifecycle_coverage_percent
repo_context_hooks_active_days
repo_context_hooks_event_count
repo_context_hooks_agent_events_total
repo_context_hooks_agent_latest_score
repo_context_hooks_rollup_repos_total
repo_context_hooks_rollup_events_total
repo_context_hooks_rollup_context_threshold_events_total
repo_context_hooks_repo_events_total
repo_context_hooks_repo_max_context_usage_percent
```

The exporter uses aggregate labels such as `repo`, `event_name`, `agent_platform`, and `model_name`. It does not export the local telemetry path, prompt text, source files, or compact summaries.

## Grafana Panels

Grafana is the strongest showcase path for the project because it makes agent continuity visible as an operational system.

Useful starter panels:

| Panel | PromQL |
| --- | --- |
| Continuity score | `repo_context_hooks_continuity_score` |
| Uplift over baseline | `repo_context_hooks_uplift` |
| Lifecycle coverage | `repo_context_hooks_lifecycle_coverage_percent` |
| Observed events | `repo_context_hooks_observed_events_total` |
| Event mix | `sum by (event_name) (repo_context_hooks_event_count)` |
| Agent/model usage | `sum by (agent_platform, model_name) (repo_context_hooks_agent_events_total)` |
| Agent/model score | `repo_context_hooks_agent_latest_score` |
| Cross-repo hook coverage | `repo_context_hooks_rollup_repos_total` |
| Cross-repo event volume | `repo_context_hooks_rollup_events_total` |
| Context pressure caught | `repo_context_hooks_rollup_context_threshold_events_total` |
| Max context pressure by repo | `repo_context_hooks_repo_max_context_usage_percent` |

For a local Prometheus setup, write the metrics into a textfile collector path on a schedule:

```bash
repo-context-hooks measure --prometheus > /var/lib/node_exporter/textfile_collector/repo_context_hooks.prom
repo-context-hooks rollup --prometheus > /var/lib/node_exporter/textfile_collector/repo_context_hooks_rollup.prom
```

On Windows, use the equivalent collector path for your exporter or schedule the command with Task Scheduler and point your collector at the generated `.prom` file.

## Datadog Path

Native Datadog API publishing is not implemented in the MVP. The honest integration path is OpenMetrics-compatible collection:

1. Generate Prometheus/OpenMetrics text with `repo-context-hooks measure --prometheus`.
2. Point a Datadog Agent OpenMetrics check or compatible collector at the generated metrics.
3. Build Datadog dashboards over the same metric names.

This keeps the product useful for teams that already operate Datadog while avoiding a premature hosted telemetry backend.

## Public Snapshot Path

For GitHub READMEs, docs sites, and portfolio demos, use the sanitized snapshot instead of raw local telemetry:

```bash
repo-context-hooks measure --snapshot-dir docs/monitoring
repo-context-hooks rollup --snapshot-dir docs/rollup
```

That writes:

- `docs/monitoring/index.html`
- `docs/monitoring/history.json`
- `docs/monitoring/timeseries.svg`
- `docs/rollup/index.html`
- `docs/rollup/rollup.json`

The README should embed `docs/monitoring/timeseries.svg` when you want the repo landing page to show a real graph. The SVG is generated from `history.json`, so it changes as local telemetry history grows and you refresh the public snapshot.

For explicit platform/model labels in new telemetry events, set:

```bash
REPO_CONTEXT_HOOKS_AGENT_PLATFORM=codex
REPO_CONTEXT_HOOKS_MODEL_NAME=gpt-5.5
REPO_CONTEXT_HOOKS_AGENT_SESSION_ID=optional-session-id
```

If labels are not supplied, repo hook sources are inferred when possible and the public graph falls back to `unknown model`.

The checked-in snapshot is intentionally aggregate-only. It is safe to review before commit and does not require any remote telemetry account.

## Context Window Telemetry

Native lifecycle hooks are platform-specific. Claude can emit `PreCompact` through its hook surface, but VS Code extensions, local model runners, and other wrappers need to provide their own context-window signal.

Use `record-context` wherever a runner can see used tokens and context limit:

```bash
repo-context-hooks record-context \
  --used-tokens 99000 \
  --limit-tokens 100000 \
  --threshold-percent 99 \
  --checkpoint \
  --source vscode-extension \
  --agent-platform codex \
  --model-name gpt-5.5
```

The command records `context-window-threshold` when usage reaches the configured threshold. With `--checkpoint`, it also records a `pre-compact` event. This is how wrappers can model the "1% before auto-compact" behavior without claiming the package can inspect every model's private context window by itself.

## Privacy Boundary

Default behavior is local-only.

Exported metrics include:

- score
- baseline
- uplift
- observed event totals
- event counts by event name
- event counts by agent platform and model name
- context-window usage percentages when explicitly reported by a wrapper
- lifecycle coverage
- active days

Exported metrics do not include:

- prompts
- code
- resume content
- issue bodies
- compact summaries
- local telemetry paths
- source file contents

Remote community telemetry remains a future opt-in feature, not an MVP default.
