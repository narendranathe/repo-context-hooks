# repo-context-hooks

Agent-level continuity skill for coding agents.

<p align="center">
  <img src="assets/brand/repo-context-hooks-logo.png" alt="repo-context-hooks brand mark showing hook events flowing into an impact monitor" width="144">
</p>

![Context Continuity Engine showing README.md, specs/README.md, AGENTS.md, hook events, impact monitor, Score 90, and +70 uplift](assets/diagrams/context-continuity-engine.svg)

`repo-context-hooks` is an agent-level skill that keeps interrupted work, next-step context, and handoff notes alive across sessions. It runs at the agent runtime level - installed once to `~/.claude/skills/`, `~/.codex/skills/`, or equivalent agent home - and uses repository workspace contracts as its durable persistence layer.

The goal: a new agent session should start with full project context without rediscovering everything from scratch.

## Install as Agent Skill (primary path)

```bash
# Claude Code
python -m pip install repo-context-hooks
repo-context-hooks install --platform claude

# Codex
repo-context-hooks install --platform codex
```

This installs the skill to agent home (`~/.claude/skills/context-handoff-hooks/`). Once installed, every Claude Code session in any workspace picks up the continuity skill automatically.

## Set Up Workspace Contract (per-repo, optional)

```bash
python -m pip install -e .
repo-context-hooks init          # scaffold specs/README.md, UBIQUITOUS_LANGUAGE.md
repo-context-hooks doctor        # verify workspace contract health
repo-context-hooks recommend     # suggest next steps
```

`doctor` answers "is this workspace contract healthy?" `recommend` answers "what should the agent do next in this workspace?"

## Pick Your Platform

Run one platform install command after the repo contract is healthy.

Claude:

```bash
repo-context-hooks install --platform claude
```

Cursor:

```bash
repo-context-hooks install --platform cursor
```

Codex:

```bash
repo-context-hooks install --platform codex
```

Replit:

```bash
repo-context-hooks install --platform replit
```

Windsurf:

```bash
repo-context-hooks install --platform windsurf
```

Lovable:

```bash
repo-context-hooks install --platform lovable
```

OpenClaw:

```bash
repo-context-hooks install --platform openclaw
```

Ollama:

```bash
repo-context-hooks install --platform ollama
```

Kimi:

```bash
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

The continuity loop is agent-first:

1. agent skill loads at session start and reads workspace contract from repo
2. captures tactical state into `specs/README.md` before compact or handoff
3. reloads from repo state at next session start - not from fragile session memory
4. leaves the next session a cleaner handoff than the one inherited

Claude exposes the full lifecycle surface. Cursor, Codex, Replit, Windsurf, Lovable, OpenClaw, Ollama, and Kimi benefit from the same workspace contract through narrower platform-specific surfaces.

![Lifecycle flow diagram showing an interrupted bugfix, a checkpoint written to specs/README.md, and the next session resuming from repo state](assets/diagrams/lifecycle-flow.svg)

## Supported Today

The public support story is intentionally narrow and explicit. These are the platforms currently supported:

- Claude (`native`): strongest support for repo hooks, session transitions, and continuity checkpoints.
- Cursor (`partial`): supports the repo contract and instruction surfaces, but not full Claude-style lifecycle parity.
- Codex (`partial`): supports repo-native continuity through checked-in repo docs and `AGENTS.md`, but not native lifecycle hooks.
- Replit (`partial`): supports repo-native continuity through `replit.md` and the repo contract, but not native lifecycle hooks or compact automation.
- Windsurf (`partial`): supports repo-native continuity through root `AGENTS.md` and `.windsurf/rules`, but not native lifecycle hooks or compact automation.
- Lovable (`partial`): supports repo-owned knowledge exports plus `AGENTS.md`, but still requires manual Project Knowledge and Workspace Knowledge steps in the Lovable UI.
- OpenClaw (`partial`): supports repo-root workspace files such as `SOUL.md`, `USER.md`, `TOOLS.md`, and `AGENTS.md`, but still requires manual OpenClaw workspace configuration.
- Ollama (`partial`): supports a repo-owned `Modelfile.repo-context` for local-model workflows, but Ollama itself is not a repo-aware agent runtime.
- Kimi (`partial`): supports root `AGENTS.md` for Kimi Code CLI project context, but not generic Kimi API setup or lifecycle hooks.

## Platform Support

The support tiers are `native`, `partial`, and `planned`.

See [docs/platforms.md](docs/platforms.md) for the support matrix, platform-specific caveats, and the current claim boundary. The short version is that we do not claim universal agent support, and we do not claim hook parity or compact automation for Cursor, Codex, Replit, Windsurf, Lovable, OpenClaw, Ollama, or Kimi.

## Readiness And Recommendations

Use the new repo-first commands together:

```bash
repo-context-hooks doctor --all-platforms
repo-context-hooks recommend
```

- `doctor --all-platforms` prints a compact readiness matrix across the current support matrix.
- `recommend` ranks the best next setup paths for the current repo, prints the repo signals it used, and gives the exact next install command to run.

That combination keeps the product honest: readiness is verification, recommendation is advice, and neither widens the public support claim.

For scripts, CI, and agent wrappers, add `--json`:

```bash
repo-context-hooks platforms --json
repo-context-hooks doctor --json
repo-context-hooks doctor --all-platforms --json
repo-context-hooks recommend --json
repo-context-hooks measure --json
```

## Prove Impact

`repo-context-hooks` now includes a local evidence loop so teams can show what continuity changed instead of only claiming it helped.

```bash
repo-context-hooks measure
repo-context-hooks measure --json
repo-context-hooks measure --snapshot-dir docs/monitoring
```

`measure` compares the current repo continuity score against an estimated no-continuity baseline, then reports observed hook and skill events from local JSONL telemetry. Hook scripts write small events to your OS cache by default, outside the git repo. If that cache is unavailable in a sandbox, telemetry falls back to `.repo-context-hooks/`, which `init` adds to `.gitignore`.

Use `--snapshot-dir` when you intentionally want to publish a sanitized dashboard and `history.json` from your local evidence. The snapshot includes aggregate scores, event counts, lifecycle coverage, and time-series usability only.

Use it before and after installing a platform adapter:

```bash
repo-context-hooks measure
repo-context-hooks install --platform claude
# start a new Claude session or run a compact/session-end flow
repo-context-hooks measure
```

The output is intentionally operational rather than magical: it shows repo-contract readiness, observed lifecycle events, evidence-log location, and concrete recommendations. See [docs/monitoring.md](docs/monitoring.md) for the metric definitions, privacy boundary, and before/after workflow.

Current repo snapshot:

- Score `90`
- Baseline `20`
- Uplift `+70`
- Observed hook events `32`
- Active days `2`
- Lifecycle coverage `100%`
- Monitoring view: [docs/monitoring/index.html](docs/monitoring/index.html)
- Time-series data: [docs/monitoring/history.json](docs/monitoring/history.json)

Remote telemetry is not enabled in the MVP. Any future community usage metrics must be explicit opt-in and follow [docs/telemetry-policy.md](docs/telemetry-policy.md).

## Telemetry Visibility

The landing-page proof surface is designed to be inspectable, portable, and honest. The repo does not ask users to trust a hidden service; it gives them local telemetry, a generated HTML monitor, and a checked-in JSON snapshot they can visualize anywhere.

| Surface | What it shows | How to use it |
| --- | --- | --- |
| [Impact monitor](docs/monitoring/index.html) | Score, uplift, lifecycle coverage, event mix, and recent hook evidence | Open it directly from GitHub or publish it with GitHub Pages |
| [History JSON](docs/monitoring/history.json) | Time-series score, daily hook events, and usability metrics | Import into Observable Plot, Vega-Lite, Evidence, DuckDB, or a docs site |
| Local dashboard | Private per-repo `monitoring.html` generated beside the local event log | Run `repo-context-hooks measure` after real agent sessions |
| Public snapshot | Sanitized dashboard and `history.json` for a README, demo, or adoption note | Run `repo-context-hooks measure --snapshot-dir docs/monitoring` |

Visualization tools that fit the current MVP:

- Observable Plot for a lightweight public notebook over `docs/monitoring/history.json`.
- Vega-Lite for an embeddable JSON-driven chart in docs or a portfolio case study.
- GitHub Pages for hosting `docs/monitoring/index.html` without adding a backend.
- DuckDB or SQLite for local trend analysis once the JSONL log grows across many sessions.

## Concrete Stories

The visuals in this repo are about specific interrupted-work situations, not abstract architecture theater.

### Interrupted Task Recovery

A compact event lands in the middle of a bugfix. The useful checkpoint is written back into the repo so the next session can resume with context instead of re-explaining the problem.

![Repo contract diagram showing the open PR story in README.md, handoff notes in specs/README.md, and a Cursor, Codex, or Replit session re-entering with repo context](assets/diagrams/repo-contract.svg)

### Before And After Handoffs

Without a checked-in continuity contract, teams repeat themselves. With one, the next session can reopen the repo and keep moving.

![Before and after continuity comparison showing repeated bug explanation versus resuming from checked-in continuity](assets/diagrams/before-after-continuity.svg)

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

## Development

```bash
python -m pip install -e .
python -m pytest -q --basetemp .pytest-tmp-readme-full
```

Pull requests are welcome when they make the repo contract clearer, more durable, or easier to adopt without widening the product claims beyond what the implementation supports.

## License

MIT
