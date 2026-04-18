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

## What This Is

- lifecycle hooks for session start, compact, and session end
- a dual-document contract: `README.md` for users, `specs/README.md` for engineering memory
- bundled skills for loading context and checkpointing work
- zero external database or hosted service requirement

## What This Is Not

- not a vector memory layer
- not a hosted memory service
- not a knowledge graph database
- not Claude-only, even if Claude Code inspired the first version

## Install

```bash
python -m pip install -e .
repo-context-hooks install --platform codex
```

Compatibility aliases:

```bash
repohandoff install --platform codex
graphify install --platform codex
```

## What `install` Does

1. Installs bundled skills into the target agent home directory
2. Copies helper scripts into `.claude/scripts`
3. Merges lifecycle hook entries into `.claude/settings.json`
4. Bootstraps `specs/README.md` continuity for the current repo

## Repo Contract

- `README.md`: user-facing project explanation and contribution guide
- `specs/README.md`: engineering memory, decisions, constraints, failures, and next work

## Who This Helps

- developers using Claude Code or Codex in long-running repos
- teams onboarding new agents into partially complete projects
- engineers who want deterministic continuity without extra infrastructure

## Development

```bash
python -m pytest -q --basetemp .pytest-tmp
```

## License

MIT
