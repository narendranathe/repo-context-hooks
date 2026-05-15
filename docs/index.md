# repo-context-hooks

Hook-based repo context continuity for coding agents.

`repo-context-hooks` is an agent-level skill that keeps interrupted work, next-step context, and handoff notes alive across sessions. Install once to agent home - every workspace you open picks it up automatically.

A new agent session should start with full project context without rediscovering everything from scratch.

## Quickstart

Three commands; each block runs in under thirty seconds on a healthy machine.
No CDN, no JavaScript, no account.

```bash
# 1. Install the package and wire the hooks
pip install repo-context-hooks
repo-context-hooks install --platform claude

# 2. Confirm the plumbing — synthesises an event end-to-end and prints a
#    receipt. Exits 0 healthy, 1 broken, 2 cold-start.
repo-context-hooks verify --platform claude

# 3. Measure your continuity score on the current repo
repo-context-hooks measure --repo-root .
```

If `verify` exits non-zero, jump straight to
[Troubleshooting](troubleshooting.md). The `Last error` line in
`doctor` output will name the log path and the failing step.

## Scope

**Today:** repo-context-hooks runs at **single-developer scope**. Each developer
has their own local telemetry on their own machine; there is no shared team
aggregation. The hooks work the same whether you are solo or one of fifty
engineers each running them locally.

**Roadmap:** team aggregation (shared event streams, multi-seat dashboards)
is tracked in [#26](https://github.com/narendranathe/repo-context-hooks/issues/26).
If your team needs this, leave a +1 on that issue.

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

## Verify the Install in <2 Seconds

After `install`, you don't have to wait for the next agent session to know the
plumbing works. The `verify` command synthesises a hook event end-to-end and
prints a confirmation receipt:

```bash
repo-context-hooks verify
# Platform: claude
# Agent home: /home/you/.claude
# Settings path: /home/you/.claude/settings.json
# Settings sha256 (canonical): a1b2c3...
# Synthetic event round-trip: OK
# Last event timestamp: 2026-04-30T12:00:00Z
# Schema valid: yes
# Elapsed: 142 ms
# Status: HEALTHY
```

`verify` writes its synthetic event to an isolated tmpdir — your real
telemetry is never touched. Pair with `--json` for machine-parseable output
suitable for CI policy gates.

## Audit Before You Commit

`install` and `uninstall` accept `--dry-run`, which prints the unified diff
that would be applied to `~/.claude/settings.json` without writing anything:

```bash
repo-context-hooks install --platform claude --dry-run
repo-context-hooks install --platform claude --dry-run --json | jq '.platforms[0].diff'
```

Use this for security review, change-control workflows, or just to see what
the tool would do before letting it run.

## Documentation

- [Install Guide](architecture.md) - architecture and full install reference
- [Troubleshooting](troubleshooting.md) - six documented failure modes with reproductions and fixes
- [CLI Reference](cli-reference.md) - every flag and subcommand, auto-generated from the parser
- [Platform Matrix](platforms.md) - support tiers across all platforms
- [Platform Playbooks](platform-playbooks.md) - per-platform operating guides
- [Telemetry Policy](telemetry-policy.md) - local-only by default; opt-in required for remote
- [Monitoring](monitoring.md) - local evidence and impact measurement
- [Competitive Analysis](competitive-analysis.md) - where this fits in the landscape
