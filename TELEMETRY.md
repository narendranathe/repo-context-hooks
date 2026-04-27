# Telemetry

`repo-context-hooks` writes local telemetry to help you verify that hooks are firing and
continuity is working. No data leaves your machine by default.

## What Is Collected

Each lifecycle hook event writes a JSONL record that may include:

- `timestamp` - ISO-8601 timestamp of when the event fired
- `event` - lifecycle event name (`session-start`, `pre-compact`, `post-compact`, `session-end`)
- `event_source` - which script produced the record (`repo_specs_memory`, `session_context`)
- `hashed_repo_id` - SHA-256 hash of the repo root path (not the path itself)
- `repo_name` - the repo folder name (basename only, not the full path)
- `git_branch` - current git branch name
- `continuity_score` - computed continuity score for the workspace (0-100)
- `estimated_baseline_score` - estimated score without the continuity skill installed
- `next_work_count` - number of open next-work items in `specs/README.md`
- `open_issues_count` - number of open issues detected in the workspace
- `local_evidence_log_path` - path to the JSONL evidence log on this machine
- `session_id` - random UUID generated at session start (not tied to any account)
- `is_sampled` - whether this record was sampled for probabilistic metrics (default 10%)

**What is never collected:**

- No source code
- No prompts or AI responses
- No compact summaries
- No issue bodies or PR descriptions
- No secrets, API keys, or environment variable values
- No resume or personal career data
- No full filesystem inventory

## Where It Is Stored

All telemetry is written locally to:

- **Linux / macOS**: `~/.cache/repo-context-hooks/`
- **Windows**: `%LOCALAPPDATA%\repo-context-hooks\`

The evidence log is a plain JSONL file you can read, delete, or inspect at any time.
It is never uploaded, synced, or transmitted anywhere by default.

## How to Opt Out

**Permanent opt-out via shell profile** (disables all telemetry writes):

```bash
# Add to ~/.bashrc, ~/.zshrc, or equivalent:
export REPO_CONTEXT_HOOKS_TELEMETRY=0
```

**Bake opt-out into installed hook command strings** (persists across shell sessions):

```bash
repo-context-hooks install --no-telemetry --platform claude
```

This writes `REPO_CONTEXT_HOOKS_TELEMETRY=0` as a prefix into every hook command string
stored in `~/.claude/settings.json`, so the env var is set whenever a hook fires regardless
of your shell environment.

**One-time opt-out** (disables for a single command):

```bash
REPO_CONTEXT_HOOKS_TELEMETRY=0 repo-context-hooks <command>
```

## No Remote Telemetry

All telemetry described above is strictly local. No data is sent to any server, analytics
service, or third-party endpoint by this tool. Remote telemetry is an explicit opt-in feature
that does not exist yet. If it is ever added, it will require a separate consent step before
any data leaves your machine. See [docs/telemetry-policy.md](docs/telemetry-policy.md) for
the full policy.
