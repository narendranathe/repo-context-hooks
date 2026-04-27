# repo-context-hooks

Hook-based repo context continuity for coding agents.

`repo-context-hooks` is an agent-level skill that keeps interrupted work, next-step context, and handoff notes alive across sessions. Install once to agent home - every workspace you open picks it up automatically.

A new agent session should start with full project context without rediscovering everything from scratch.

## Key Features

- **One-time install** - hooks write to agent home (`~/.claude/settings.json` or equivalent) and activate in every workspace automatically
- **Workspace contracts** - `specs/README.md` and `AGENTS.md` serve as durable, agent-readable state
- **Platform-native** - native support for Claude Code, with partial support for Cursor, Codex, Replit, Windsurf, and more
- **Local-first telemetry** - all monitoring is local JSONL; no data leaves your machine without explicit opt-in
- **Doctor + recommend** - built-in CLI tools to verify contract health and surface next steps
- **Zero runtime dependencies** - pure Python, no server, no cloud account required

## Quick Install

```bash
pip install repo-context-hooks
repo-context-hooks install --platform claude
```

That's it. Hooks are active in every workspace from that point on.

Need per-repo hooks too?

```bash
repo-context-hooks install --platform claude --also-repo-hooks
```

## Set Up a Workspace Contract

```bash
repo-context-hooks init      # scaffold specs/README.md, UBIQUITOUS_LANGUAGE.md
repo-context-hooks doctor    # verify contract health
repo-context-hooks recommend # suggest next steps
```

## Documentation

- [Install Guide](architecture.md) - architecture and full install reference
- [Platform Matrix](platforms.md) - support tiers across all platforms
- [Platform Playbooks](platform-playbooks.md) - per-platform operating guides
- [Telemetry Policy](telemetry-policy.md) - local-only by default; opt-in required for remote
- [Monitoring](monitoring.md) - local evidence and impact measurement
- [Competitive Analysis](competitive-analysis.md) - where this fits in the landscape
