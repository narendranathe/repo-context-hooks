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

## Fleet Rollup

`repo-context-hooks measure --all-repos` walks every workspace under your
telemetry base and prints a fleet-level summary — tokens saved, sessions,
event counts, top workspaces by tokens saved. The walk is read-only; the
on-disk format is unchanged.

```bash
repo-context-hooks measure --all-repos
repo-context-hooks measure --all-repos --json | jq '.summary.tokens_saved'
```

The headline number is `tokens_saved`, computed identically to the
single-repo `measure` formula:

```
session_starts = sum of events whose name contains "session-start"
tokens_saved   = round(session_starts × 0.30 × 2000)
tokens_injected = session_starts × 4500
cost_saved_usd = round(tokens_saved / 1_000_000 × 3.0, 3)
```

Flags:

- `--all-repos` — turn on the rollup. Without this flag, `measure` operates
  on the current repo only.
- `--top N` — table truncation. Default `15`. Pass `--top 0` to show every
  workspace.
- `--include-ghosts` — include test-run / ephemeral worktree directories
  (those with fewer than 2 events AND a repo name in
  `{"repo", "tmp", "temp", "test"}`). By default these are filtered out
  by the same classifier used by `measure --clean-ghosts`.
- `--redact` — replace `repo_name` with `sha256(name)[:12]` in both text
  and JSON output. Use this when sharing the rollup output in a public
  context (a recruiter-facing demo, a blog post, a conference slide).
- `--json` — emit a versioned JSON contract (`schema_version: 1`) suitable
  for CI policy gates, weekly digests, or external dashboards.

Example output:

```
==============================================================================
repo-context-hooks  Fleet Rollup
==============================================================================
Telemetry root          : /home/you/.cache/repo-context-hooks/telemetry
Workspaces (real)       : 25  (485 ghosts excluded; --include-ghosts to show)
Distinct sessions       : 676
Total events            : 754
session-start           : 624
Tokens injected (ctx)   : 2,808,000
Tokens SAVED (vs cold)  : 374,400      (30% × 2,000 tok re-orient avoided)
Cost saved (Claude in)  : $1.12

Top 15 workspaces by tokens saved
------------------------------------------------------------------------------
repo_id           name                          sess  starts     saved
abf293c549492716  repohandoff                     82     107    64,200
db9f15a890d32e9c  repo-context-hooks              38      38    22,800
...
```

The opt-out toggle below applies to the rollup too: with
`REPO_CONTEXT_HOOKS_TELEMETRY=0` set, `measure --all-repos` prints
`Telemetry disabled; rollup is opt-out.` and exits 0 without reading any
files.

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
