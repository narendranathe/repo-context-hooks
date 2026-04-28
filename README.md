# repo-context-hooks

Agent-level continuity skill for coding agents.

![context score](docs/badge.svg)

<p align="center">
  <img src="assets/brand/repo-context-hooks-logo.png" alt="repo-context-hooks brand mark showing hook events flowing into an impact monitor" width="144">
</p>

![Context Continuity Engine showing README.md, specs/README.md, AGENTS.md, hook events, impact monitor, Score 90, and +70 uplift](assets/diagrams/context-continuity-engine.svg)

`repo-context-hooks` is an agent-level skill that keeps interrupted work, next-step context, and handoff notes alive across sessions. Install once to agent home — every workspace you open picks it up automatically.

The goal: a new agent session should start with full project context without rediscovering everything from scratch.

## Install

```bash
pip install repo-context-hooks
repo-context-hooks install --platform claude
```

That's the full install. Hooks write to `~/.claude/settings.json` and activate in every workspace from that point on.

Need per-repo hooks too?

```bash
repo-context-hooks install --platform claude --also-repo-hooks
```

## Set Up a Workspace Contract (per-repo)

```bash
repo-context-hooks init          # scaffold specs/README.md, UBIQUITOUS_LANGUAGE.md
repo-context-hooks doctor        # verify contract health
repo-context-hooks recommend     # suggest next steps
```

`doctor` answers "is this workspace contract healthy?" `recommend` answers "what should the agent do next?"


## Write Session Decisions Back

The checkpoint command lets the agent record what was built and decided directly into `specs/README.md`. This is the semantic layer on top of the automated hook checkpoints.

```bash
repo-context-hooks checkpoint --message "Built X. Decided Y because Z. Next: W."
```

Entries are written to the `## Session Log` section of `specs/README.md` with a timestamp and branch name. The format that works best:

```
Built: JWT refresh endpoint + migration 0014. Decided: Redis over DB for refresh tokens — DB showed 3x latency under load. Reverted: DB-backed approach (latency spike). Next: wire validation into auth middleware.
```

Fields:
- **Built:** what was shipped or committed
- **Decided:** key choices and rationale
- **Reverted/failed:** dead ends so the next agent does not repeat them
- **Next:** the exact next task

The `context-handoff-hooks` skill instructs the agent to run this command at `PreCompact` and `SessionEnd` so decision history accumulates automatically across sessions.

## Other Platforms

```bash
repo-context-hooks install --platform codex
repo-context-hooks install --platform cursor
repo-context-hooks install --platform replit
repo-context-hooks install --platform windsurf
repo-context-hooks install --platform lovable
repo-context-hooks install --platform openclaw
repo-context-hooks install --platform ollama
repo-context-hooks install --platform kimi
```

## Why Agent-Level, Not Repo-Level

Coding sessions rarely fail because the model forgot a fact. They fail because useful state of the work never survived the session boundary.

The old approach (install a hook per repo) means every new workspace starts from zero. The right approach is a skill installed once at agent home that activates in every workspace and uses checked-in repo files as its persistence layer.

`repo-context-hooks` brings the same model as `superpowers` and `caveman`: install once to the agent runtime, works everywhere.

- Agent skill: fires on `SessionStart`, `PreCompact`, `PostCompact`, `SessionEnd`
- Workspace contract: `specs/README.md` (engineering memory), `README.md` (product intent), `UBIQUITOUS_LANGUAGE.md` (shared terms)
- Telemetry: local JSONL events so `repo-context-hooks measure` can verify hooks actually fired

## How It Works

1. Agent skill loads at session start and reads workspace contract from repo
2. Captures tactical state into `specs/README.md` before compact or handoff
3. Reloads from repo state at next session start - not from fragile session memory
4. Leaves the next session a cleaner handoff than the one inherited

![Lifecycle flow diagram showing an interrupted bugfix, a checkpoint written to specs/README.md, and the next session resuming from repo state](assets/diagrams/lifecycle-flow.svg)

## Supported Platforms

| Platform | Support | Notes |
|----------|---------|-------|
| Claude | `native` | Full lifecycle hooks, session transitions, continuity checkpoints |
| Codex | `partial` | Repo-native continuity via `AGENTS.md`; `install_global_hooks()` writes marker to `~/.codex/settings.json` |
| Cursor | `partial` | Repo contract and instruction surfaces; no Claude-style lifecycle parity |
| Replit | `partial` | `replit.md` and repo contract; no native lifecycle hooks |
| Windsurf | `partial` | Root `AGENTS.md` and `.windsurf/rules`; no native lifecycle hooks |
| Lovable | `partial` | Repo knowledge exports plus `AGENTS.md`; requires manual UI steps |
| OpenClaw | `partial` | `SOUL.md`, `USER.md`, `TOOLS.md`, `AGENTS.md`; requires manual workspace config |
| Ollama | `partial` | `Modelfile.repo-context` for local-model workflows |
| Kimi | `partial` | Root `AGENTS.md` for Kimi Code CLI; no generic API or lifecycle hooks |

See [docs/platforms.md](docs/platforms.md) for the full support matrix.

## Readiness and Recommendations

```bash
repo-context-hooks doctor --all-platforms
repo-context-hooks recommend
```

For scripts and CI:

```bash
repo-context-hooks platforms --json
repo-context-hooks doctor --json
repo-context-hooks recommend --json
repo-context-hooks measure --json
```

## Prove Impact

```bash
repo-context-hooks measure                          # CLI summary
repo-context-hooks measure --open                   # rich browser dashboard
repo-context-hooks measure --snapshot-dir docs/monitoring
repo-context-hooks measure --forecast               # 30-day projection
repo-context-hooks measure --branches               # per-branch score table
repo-context-hooks measure --clean-ghosts           # prune test-run dirs (dry-run safe)
repo-context-hooks measure --badge-out docs/badge.svg
```

### Share Your Results

```bash
repo-context-hooks measure export                    # shareable markdown report (stdout)
repo-context-hooks measure export --format json      # machine-readable JSON
repo-context-hooks measure export -o report.md       # write to file
```

Paste the output directly into a LinkedIn post, pull request description, or README as adoption evidence:

```markdown
## repo-context-hooks Impact Report - my-repo

| Metric | Value |
|--------|-------|
| Contract score | 90 / 100 |
| Continuity uplift | +70 |
| Hook events recorded | 104 |
| Sessions instrumented | ~48 |
| Lifecycle coverage | 100% |
| Tokens injected | ~237,000 |

*Source: local operational telemetry - no source code, prompts, or personal data.
Generated by [repo-context-hooks](https://github.com/narendranathe/repo-context-hooks).*
```

### Run a Before/After Experiment

Capture your contract score before wiring up hooks and again after to measure the delta as concrete evidence of impact.

```bash
repo-context-hooks measure experiment start          # snapshot before score
# ... install hooks, run a few sessions ...
repo-context-hooks measure experiment finish         # compare and print the delta
repo-context-hooks measure experiment status         # check if an experiment is in progress
```

Then run `measure export` to share the results.

### Badge

The badge shows three sections: **label | score | lifecycle coverage%**. Coverage turns green at 75%+, yellow at 25-74%, red below 25%.

```bash
repo-context-hooks measure --badge-out docs/badge.svg
```

```markdown
![context score](docs/badge.svg)
```

### Live telemetry (this repo, v0.6.0)

`measure` compares the current repo contract score against an estimated no-continuity baseline and shows token savings, lifecycle health, and branch drift in one view.

| Metric | Value |
|--------|-------|
| Contract score | **90 / 100** |
| Baseline without hooks | 20 / 100 |
| Continuity uplift | **+70 points** |
| Hook events recorded | 85 |
| Sessions instrumented | ~48 |
| Active days | 2 |
| Lifecycle coverage | 25% (session-start firing; session-end populates after longer sessions) |
| Branches monitored | 3 — main, feat/telemetry-reliability, feat/agent-level-skill-runtime |
| Tokens injected | ~237,000 (4,950 tok/session × 48 sessions) |
| Est. tokens saved | ~28,800 (30% of sessions skip 2,000-tok re-orientation) |
| Est. cost saved | ~$0.09 at current scale ($3/M input, Claude Sonnet) |
| Engineering memory | 11 sections across specs/README.md |

At 30-day scale (~50 sessions/day): ~72,000 tokens saved/day, ~$65/year per developer.

- Monitoring view: [docs/monitoring/index.html](docs/monitoring/index.html)
- Time-series data: [docs/monitoring/history.json](docs/monitoring/history.json)

Remote telemetry is not enabled. Any future community metrics require explicit opt-in per [docs/telemetry-policy.md](docs/telemetry-policy.md).

See [TELEMETRY.md](TELEMETRY.md) for what is collected locally and how to opt out.

## Telemetry Visibility

| Surface | What it shows | How to use it |
|---------|--------------|---------------|
| [Impact monitor](docs/monitoring/index.html) | Score, uplift, tokens injected, lifecycle ring, branch health, forecast | `measure --open` or open from GitHub Pages |
| [History JSON](docs/monitoring/history.json) | Time-series score, daily events, usability metrics, branch scores, forecast | Import into Observable Plot, Vega-Lite, DuckDB |
| Local dashboard | Private full-detail view with branch + forecast panels | `repo-context-hooks measure --open` |
| Public snapshot | Sanitized version for README or docs site | `repo-context-hooks measure --snapshot-dir docs/monitoring` |

### Manage consent

Remote telemetry is disabled by default. Use these commands to inspect, preview, or change the consent state.

```bash
repo-context-hooks telemetry status              # show current consent state
repo-context-hooks telemetry preview             # preview what would be sent (nothing is sent)
repo-context-hooks telemetry enable              # opt in to remote community metrics
repo-context-hooks telemetry disable             # opt out
```

The `preview` command shows the exact payload before you decide. No data leaves your machine until you run `enable` and confirm.

## Concrete Stories

### Interrupted Task Recovery

A compact event lands in the middle of a bugfix. The useful checkpoint is written back into the repo so the next session can resume with context instead of re-explaining the problem.

![Repo contract diagram showing the open PR story in README.md, handoff notes in specs/README.md, and a Cursor, Codex, or Replit session re-entering with repo context](assets/diagrams/repo-contract.svg)

### Before and After Handoffs

Without a checked-in continuity contract, teams repeat themselves. With one, the next session can reopen the repo and keep moving.

![Before and after continuity comparison showing repeated bug explanation versus resuming from checked-in continuity](assets/diagrams/before-after-continuity.svg)

- **Session decision capture** - `repo-context-hooks checkpoint --message "..."` writes decisions, rationale, and next steps directly into `specs/README.md` Session Log; the skill now gives concrete `PreCompact` and `SessionEnd` write-back instructions instead of vague guidance
- **Session Log section** - `specs/README.md` workspace contracts now scaffold a `## Session Log` for agent-written entries, keeping it separate from the automated `## Session Checkpoints`
- **Richer automated checkpoints** - `pre-compact`/`session-end` hook checkpoints now include the last 3 git commits alongside the changed-file list
## What's New in v0.6.0

- **Shareable export** - `measure export` prints a redacted markdown or JSON impact report you can paste directly into a LinkedIn post, README, or PR description
- **Before/after experiment** - `measure experiment start/finish/status` captures your contract score before and after wiring up hooks so you have a real delta as evidence
- **Telemetry consent layer** - `telemetry status/preview/enable/disable` - remote telemetry stays off by default; `preview` shows the exact payload before you decide
- **Sampling gate fix** - `is_sampled()` now bypasses stale file cache; deterministic rates (>=1.0 always True, <=0.0 always False) so lifecycle coverage reflects reality
- **Session duration tracking** - `avg_session_duration_minutes` now populates from session-end events
- **ROI metrics** - dashboard adds "Cold starts prevented (est.)" and "Week-1 uplift" cards

See [CHANGELOG.md](CHANGELOG.md) for full history.

## See Also

- [Platform support](docs/platforms.md)
- [Engineering memory](specs/README.md)
- [Ubiquitous language](UBIQUITOUS_LANGUAGE.md)
- [Architecture](docs/architecture.md)
- [Monitoring and impact evidence](docs/monitoring.md)
- [Telemetry policy](docs/telemetry-policy.md)
- [Competitive analysis](docs/competitive-analysis.md)
- [Minimal repo example](examples/minimal-repo/)
- [Multi-project example](examples/multi-project/)
- [CHANGELOG](CHANGELOG.md)

## Development

```bash
pip install -e ".[dev]"
python -m pytest -q
```

Pull requests are welcome when they make the repo contract clearer, more durable, or easier to adopt without widening the product claims beyond what the implementation supports.

## License

MIT
