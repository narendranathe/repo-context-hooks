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

### Badge

The badge shows three sections: **label | score | lifecycle coverage%**. Coverage turns green at 75%+, yellow at 25-74%, red below 25%.

```bash
repo-context-hooks measure --badge-out docs/badge.svg
```

```markdown
![context score](docs/badge.svg)
```

### Live telemetry (this repo, v0.5.0)

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

## Concrete Stories

### Interrupted Task Recovery

A compact event lands in the middle of a bugfix. The useful checkpoint is written back into the repo so the next session can resume with context instead of re-explaining the problem.

![Repo contract diagram showing the open PR story in README.md, handoff notes in specs/README.md, and a Cursor, Codex, or Replit session re-entering with repo context](assets/diagrams/repo-contract.svg)

### Before and After Handoffs

Without a checked-in continuity contract, teams repeat themselves. With one, the next session can reopen the repo and keep moving.

![Before and after continuity comparison showing repeated bug explanation versus resuming from checked-in continuity](assets/diagrams/before-after-continuity.svg)

## What's New in v0.5.0

- **Rich browser dashboard** - `measure --open` launches a single-file HTML view showing tokens injected, estimated cost savings, lifecycle coverage ring, branch health table, and 30-day forecast
- **Session duration tracking** - session-end events now carry `duration_minutes`; `measure` reports avg and max
- **Hook deduplication** - `install --dedup` normalises backslash/forward-slash paths; auto-runs on every install
- **Ghost repo cleanup** - `measure --clean-ghosts [--no-dry-run]` removes test-run dirs from the telemetry store
- **30-day forecast** - `measure --forecast` projects events from 7-day rolling average with high/medium/low confidence
- **Per-branch scores** - `measure --branches` shows session count, avg score, and last-seen per git branch
- **Doctor hook health** - `doctor --platform claude` detects duplicate hook entries and exits 1
- **Two-field badge** - SVG badge now shows score + lifecycle coverage% as separate coloured sections
- **0% lifecycle fix** - removed inline `measure_impact()` call from `record_event()`; session-end timeout raised 10s → 30s

See [CHANGELOG.md](CHANGELOG.md) for full history.
- **CI/CD** - GitHub Actions with pytest matrix (Python 3.9-3.12, ubuntu + windows) and OIDC PyPI publish

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
