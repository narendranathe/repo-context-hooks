# RepoHandoff

Deterministic context continuity for coding-agent repositories.

`RepoHandoff` installs a compact-safe lifecycle pipeline across:

- Session start
- Pre-compact
- Post-compact
- Session end

It keeps project context operational via a dual-document contract:

- `README.md` for users/contributors
- `specs/README.md` for engineering memory and next-work state

## Positioning

Projects like `mem0` and `claude-mem` focus on long-term memory storage and retrieval.
RepoHandoff focuses on deterministic repository-local execution handoff:

- No vector DB
- No hosted memory service
- Hooks + docs as source of truth
- Predictable behavior across compaction boundaries

Category:

- Agent Runtime Reliability Layer (ARRL)

## Install (editable)

```bash
python -m pip install -e .
```

## Command

```bash
repohandoff install --platform codex
# backward-compatible alias
graphify install --platform codex
```

Options:

- `--platform codex|claude` (required)
- `--repo-root <path>` (default `.`)
- `--skip-repo-hooks` (skills only)
- `--force` (overwrite existing skill folders)

## What `install` does

1. Installs bundled skills to:
   - Codex: `~/.codex/skills`
   - Claude: `~/.claude/skills`
2. If target is a git repo, installs scripts into `.claude/scripts` and merges hook entries into `.claude/settings.json`.

## Who this is for

- Teams running Codex/Claude in long sessions with auto-compact
- Repos where new agents frequently lose execution context
- Engineering orgs that want deterministic handoff without adding infra

## Bundled Skills

- `context-handoff-hooks`
- `session-start-context-loader`
- `precompact-checkpoint`
- `postcompact-context-reload`

## Validation

```bash
python -m pytest -q
```

## License

MIT
