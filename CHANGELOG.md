# Changelog

All notable changes to this project will be documented in this file.

## [0.6.0] - 2026-04-28

### Added
- `measure export [--format markdown|json] [-o PATH]` - redacted shareable impact report; paste directly into LinkedIn post, README, or PR description
- `measure experiment start/finish/status` - guided before/after continuity experiment; captures contract score delta as concrete adoption evidence
- `telemetry status/preview/enable/disable` - remote telemetry consent layer; `preview` shows exact payload before any data leaves the machine
- Two new ROI dashboard cards: "Cold starts prevented (est.)" and "Week-1 uplift" (score at day 7 minus day 0)

### Fixed
- `is_sampled()` bypasses stale file cache; deterministic rates (>=1.0 always True, <=0.0 always False) - resolves 0% lifecycle coverage where old sampling decisions silently blocked pre-compact/post-compact/session-end events
- `avg_session_duration_minutes` now populates from session-end events (was null in 0.5.0)
- Export output uses ASCII hyphens - fixes `?` rendering on Windows cp1252 consoles
- Bundle script `_VALID_EVENTS` validation prevents pytest argv leaking as EVENT values

### Tests
- 249 tests (from 210 in 0.5.0)

## [0.5.0] - 2026-04-27

### Added
- `measure --badge` outputs a shields.io flat-style SVG badge showing the current contract score; `--badge-out PATH` writes it to a file. `docs/badge.svg` embedded in README.
- MkDocs Material site for docs/ — deployed to GitHub Pages at https://narendranathe.github.io/repo-context-hooks/ via pages.yml workflow
- CI platform-matrix job: install_platform() verified for all 9 platforms (claude, cursor, codex, replit, windsurf, lovable, openclaw, ollama, kimi) with fail-fast:false

### Tests
- 210 tests (from 199 in 0.4.0)

## [0.4.0] - 2026-04-27

### Added
- `uninstall` command: removes skills bundle and surgically cleans hook entries from settings.json (user hooks preserved, idempotent)
- Auto-detect platform: `install` with no `--platform` detects installed agents via `~/.{platform_id}/` and installs to all in one command
- `--no-telemetry` install flag: bakes `REPO_CONTEXT_HOOKS_TELEMETRY=0` into hook command strings for permanent local opt-out
- `TELEMETRY.md`: documents what is collected (local only), where it lives, and all three opt-out paths
- First-run guidance: install prints "What happens next" block (init/doctor/measure)
- Telemetry sampling fix: env var hard bypass, default rate 1.0, 8-hour staleness, session state in OS temp dir for worktree isolation

### Fixed
- CI smoke test uses real CLI (`install` + `doctor`) and verifies settings.json content on both Linux and Windows
- `is_sampled()` now reads env var before any file I/O

### Tests
- 199 tests (from 177 in 0.3.0)

## [0.3.0] - 2026-04-26

### Added
- Agent-level install: `install_global_hooks()` writes to `~/.claude/settings.json` — install once, active in every workspace
- Session metrics sampling: `session_id` in every telemetry record, `is_sampled()` probabilistic gate (10% default, configurable via `REPO_CONTEXT_HOOKS_SAMPLE_RATE`)
- `auto_commit_snapshot()` — auto-commits `docs/monitoring/history.json` on session end
- `--also-repo-hooks` flag — opt into per-repo hooks in addition to agent-level
- Two-section install output: "Agent skill install" / "Workspace artifacts"
- Codex `install_global_hooks()` parity
- Graceful degradation: non-git and no-workspace-contract paths now print helpful messages and exit 0

### Fixed
- Hook command paths now use POSIX forward slashes (cross-platform correctness)
- `install_global_hooks()` merges hook arrays instead of clobbering pre-existing same-key entries
- `is_sampled()` returns "skipped" when re-run with no changes
- `session_context.py` now calls `clear_session_state()` on session-end

### Tests
- 174 tests (from 142 in 0.2.4)

## [0.2.4] - (previous release)
