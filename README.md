# repo-context-hooks

Hook-based repo context continuity for coding agents.

`repo-context-hooks` preserves repository context across session start, compaction, and handoff using repo-local hooks, specs memory, and installable skills.

It is built for teams and solo developers who want agents to continue work from the repo's actual state instead of relying on fragile chat memory.

## Why This Exists

Agent sessions usually fail in predictable ways:

- a new session re-discovers the repo from scratch
- auto-compact drops tactical decisions
- next-work context goes stale
- issue context disappears between sessions

Claude Code's hooks model points to the right primitives. This package turns that pattern into a reusable, repo-local workflow.

## How It Works

`repo-context-hooks` treats repository context as an operational contract instead of a prompt artifact.

At session start, the hooks load project memory and current priorities. Before compaction, the hooks checkpoint tactical state into the repo. After compaction, the condensed context is reloaded so the next turn has continuity instead of drift. At session end, the repo gets one more continuity note for the next agent or session.

![Lifecycle flow diagram showing SessionStart, PreCompact, PostCompact, and SessionEnd](assets/diagrams/lifecycle-flow.svg)

## Repo Contract

The repo stays the source of truth:

- `README.md` explains the project to users and contributors
- `specs/README.md` carries engineering memory, constraints, decisions, failures, and next work
- hooks and skills keep those layers synchronized enough to survive handoffs

![Repo contract diagram showing README.md, specs/README.md, and hooks plus skills](assets/diagrams/repo-contract.svg)

## Before / After

Before this workflow, new agent sessions often re-discover the repo, repeat old decisions, and lose the next useful action after compaction.

After this workflow, sessions start with more structure, compaction preserves tactical state, and handoffs become more deterministic.

![Before and after continuity comparison showing context drift versus deterministic handoff](assets/diagrams/before-after-continuity.svg)

## What `install` Actually Does

1. Installs bundled skills into:
   - `~/.codex/skills`
   - `~/.claude/skills`
2. Copies helper scripts into:
   - `.claude/scripts/repo_specs_memory.py`
   - `.claude/scripts/session_context.py`
3. Merges lifecycle hook entries into:
   - `.claude/settings.json`
4. Requires the repo to already have:
   - `README.md`
   - `specs/README.md`

Install commands:

```bash
python -m pip install -e .
repo-context-hooks install --platform codex
repohandoff install --platform codex
graphify install --platform codex
```

## Technical Details

- Primary CLI: `repo-context-hooks`
- Compatibility aliases: `repohandoff`, `graphify`
- Supported agent targets today: Codex and Claude
- Expected repo contract: `README.md` plus `specs/README.md`
- Architecture notes: [docs/architecture.md](docs/architecture.md)
- Minimal example: [examples/minimal-repo/](examples/minimal-repo/)
- Multi-project example: [examples/multi-project/](examples/multi-project/)

## Honest Critique

- This is not a vector memory layer.
- This is not a hosted memory service.
- This does not replace repo discipline.
- Poor `specs/README.md` hygiene reduces the value quickly.
- Teams that need cross-repo semantic memory may still want another tool alongside this one.

## Examples

- [Minimal repo example](examples/minimal-repo/)
- [Multi-project example](examples/multi-project/)
- [Architecture notes](docs/architecture.md)

## Development

```bash
python -m pip install -e .
python -m pytest -q --basetemp .pytest-tmp-readme-full
```

Pull requests are welcome when they improve reliability, clarity, or the repo contract without turning the project into a vague memory platform.

## License

MIT
