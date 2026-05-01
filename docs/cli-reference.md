# CLI Reference

This page is auto-generated from `repo_context_hooks.cli:build_parser`. Do not
edit by hand — your changes will be overwritten the next time the CI drift gate
regenerates it.

To regenerate after editing the parser:

```bash
python scripts/render_cli_reference.py --write
```

The drift check that runs in CI is:

```bash
python scripts/render_cli_reference.py --check
```

The full list of stable subcommands and flags is also pinned in
[`docs/stability.md`](stability.md) — every name on this page is part of the
v1.0 public contract and follows the
[deprecation policy](deprecation-policy.md) before removal.

## `repo-context-hooks`

Install repo context continuity skills and lifecycle hooks.

Top-level flags:

- `--version` — Print version (semver, git sha, python, platform, install method) and exit.
- `--debug` — Verbose diagnostics: stderr at DEBUG, full tracebacks to <cache>/errors.log. Use when 'something is silently broken' — e.g. continuity score not moving, hooks firing without effect.

## Subcommands

### `install`

Flags:

- `--platform` {claude,cursor,codex,replit,windsurf,lovable,openclaw,ollama,kimi} — Target platform for installation. If omitted, auto-detects installed agents.
- `--repo-root` REPO_ROOT — Repository root for repo context setup (default: current directory).
- `--also-repo-hooks` — Also install per-repo hooks into .claude/settings.json in the current repo. Agent-level install is the default; pass this flag to additionally write workspace artifacts.
- `--skip-repo-hooks` — Agent-level install is now the default; this flag is a no-op unless --also-repo-hooks is passed.
- `--force` — Overwrite existing installed artifacts.
- `--dry-run` — Compute the settings.json diff that install WOULD apply and exit without writing anything. Pair with --json for machine-parseable output suitable for CI policy gates.
- `--no-telemetry` — Bake REPO_CONTEXT_HOOKS_TELEMETRY=0 into hook command strings (local opt-out).
- `--dedup` — Remove duplicate hook entries from settings.json before installing.
- `--json` — Emit dry-run results as JSON (only effective with --dry-run).


### `init`

Flags:

- `--repo-root` REPO_ROOT — Repository root to initialize (default: current directory).
- `--force` — Overwrite bootstrapped files when supported.


### `doctor`

Flags:

- `--platform` {claude,cursor,codex,replit,windsurf,lovable,openclaw,ollama,kimi} — Target platform to validate.
- `--all-platforms` — Validate repo contract health plus readiness across all supported platforms.
- `--repo-root` REPO_ROOT — Repository root to inspect (default: current directory).
- `--json` — Print machine-readable JSON output.


### `recommend`

Flags:

- `--repo-root` REPO_ROOT — Repository root to inspect (default: current directory).
- `--limit` LIMIT — Maximum number of platform recommendations to print (default: 3).
- `--json` — Print machine-readable JSON output.


### `measure`

Flags:

- `--repo-root` REPO_ROOT — Repository root to inspect (default: current directory).
- `--json` — Print machine-readable JSON output.
- `--snapshot-dir` SNAPSHOT_DIR — Write a sanitized public monitoring snapshot to this directory (for example: docs/monitoring).
- `--badge` — Output an SVG badge showing the current contract score.
- `--badge-out` PATH — Write the SVG badge to this file path (implies --badge).
- `--open` — Generate the local monitoring dashboard and open it in the browser.
- `--forecast` — Show a 30-day activity projection based on current daily rate.
- `--branches` — Show per-branch score and session count, sorted by last seen.
- `--clean-ghosts` — Remove test-run ghost repos from the telemetry store (dry-run by default).
- `--no-dry-run` — Actually delete ghost repos (use with --clean-ghosts).
- `--format` {markdown,json} — Output format for 'export' (default: markdown).
- `--redact` — Redact local filesystem paths from the export (default: on; always enforced).
- `--output`, `-o` PATH — Write export output to this file path instead of stdout.
- `--experiment-dir` PATH — Directory to store before.json/after.json for experiments (default: .repo-context-hooks/experiment in the repo root).


### `platforms`

Flags:

- `--json` — Print machine-readable JSON output.


### `uninstall`

Flags:

- `--platform` {claude,cursor,codex,replit,windsurf,lovable,openclaw,ollama,kimi} — Platform to uninstall.
- `--dry-run` — Compute the settings.json diff that uninstall WOULD apply and exit without writing anything or removing files. Pair with --json for machine-parseable output.
- `--json` — Emit dry-run results as JSON (only effective with --dry-run).


### `verify`

Flags:

- `--platform` {claude,cursor,codex,replit,windsurf,lovable,openclaw,ollama,kimi} — Platform to verify. If omitted, auto-detects installed agents (scans ~/.{platform}/ existence) and verifies each.
- `--json` — Emit the receipt as JSON (one object per platform under `platforms`).


### `checkpoint`

Flags:

- `--message` MESSAGE — Decision summary to record (what was built, key decisions, next step).
- `--path` PATH — Repository root (default: current directory).


### `telemetry`

Sub-commands:

#### `status`


#### `enable`

Flags:

- `--yes` — Skip interactive confirmation prompt (for CI/non-interactive use).


#### `disable`


#### `preview`

Flags:

- `--repo-root` REPO_ROOT — Repository root to include continuity score in the preview (optional).
