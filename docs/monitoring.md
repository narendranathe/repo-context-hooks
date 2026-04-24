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
```

The public snapshot for this repo lives at [docs/monitoring/index.html](monitoring/index.html). It is a checked-in snapshot, while the local hook-generated dashboard keeps updating in the telemetry directory.

## What Gets Measured

The report includes:

- current continuity score
- estimated baseline score without repo continuity
- estimated uplift
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
- hashed repo id
- repo folder name
- git branch name
- repo continuity score
- estimated baseline score
- small event details such as counts and local file paths

Events do not upload code, prompts, compact summaries, issue bodies, or file contents.

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

For reproducible comparisons:

```bash
repo-context-hooks measure --json > before.json
repo-context-hooks init
repo-context-hooks install --platform claude
repo-context-hooks measure --json > after.json
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
