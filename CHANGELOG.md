# Changelog

All notable changes to this project will be documented in this file.

<!--
  CHANGELOG CONTRACT (issue #71). Every user-facing PR adds a bullet under
  [Unreleased] using ONE of these subheadings, in this order, omitting
  empty ones at release-cut time. This keeps line-merge conflicts away
  when sibling Wave 2/3 PRs land in parallel.
-->

## [Unreleased]

### Added
- Coverage gate via `pyproject.toml [tool.coverage.report] fail_under = 80`; CI enforces on every push and PR. Threshold rationale and ratchet plan: see issue [#92](https://github.com/narendranathe/repo-context-hooks/issues/92). (#71)
- Hypothesis property tests for telemetry hot paths: `is_sampled` boundaries + cached-decision stability + cache-invalidation re-roll, `repo_id` shape + stability, `deduplicate_hooks` on-disk idempotency. (#71)
- `tests/conftest.py`: shared `"rch"` Hypothesis profile, glob-based `REPO_CONTEXT_HOOKS_*` env-var isolation, pinned Hypothesis storage dir for read-only `$HOME` runners.
- `tests/test_bundle_scripts_compile.py`: `py_compile` smoke for every script shipped under `bundle/`.
- `tests/test_telemetry_edge_cases.py`: NaN/+inf/-inf rate contracts.
- README Codecov badge inside `<!-- BADGES:START/END -->` anchor block.
- Public-API stability contract (issue #72): explicit `__all__ = ["__version__"]` in `repo_context_hooks/__init__.py`, machine-readable snapshot at `tests/contract/public_surface.json`, CI gate `scripts/check_public_surface.py` (drift check + `--verify-removals` mode against prior release tag), and contract tests under `tests/contract/`. `docs/stability.md` and `docs/deprecation-policy.md` document stable vs internal surfaces and the one-MINOR-cycle deprecation rule. README adds `## Stability` section. (#72)

### Changed
- `is_sampled`: NaN sample-rate now coerces to 0.0 (safe-default opt-out) instead of silently falling through to `random.random() < NaN` and returning False with no diagnostic. (issue #71 audit follow-up)
- CI `permissions:` defaults to `contents: read`; the test job alone escalates to `id-token: write` for Codecov OIDC.
- CI matrix adds Python 3.13.

### Deprecated
<!-- none -->

### Removed
<!-- none -->

### Fixed
- `tests/conftest.py` env-isolation list previously missed `REPO_CONTEXT_HOOKS_TELEMETRY_DIR`; switched to a `startswith()` glob that future-proofs every Wave 2/3 env var.

### Security
- Pin `codecov/codecov-action` to a 40-char SHA (was the floating `@v4` tag).
- Add upper version bounds to dev deps (`pytest<9`, `pytest-cov<8`, `hypothesis<7`) so a compromised future major release cannot auto-install in CI.
- Document why this workflow uses `pull_request` (not `pull_request_target`) so a future maintainer cannot accidentally migrate to the unsafe variant.

### Tests
- 347 tests (from 338 in PR #90); +9 added by this hardening branch.
- Property-based tests via Hypothesis: `tests/test_property_telemetry.py` covers `is_sampled` boundary behaviour (rate ≥ 1.0 → True, rate ≤ 0.0 → False, mid-range cached decision is stable) and `repo_id` shape (16 lowercase hex chars, stable across calls); `tests/test_installer.py` adds an idempotency property test for `deduplicate_hooks` over realistic hook payloads
- `tests/conftest.py`: autouse fixture clears `REPO_CONTEXT_HOOKS_*` env vars between tests so local dev environments do not leak telemetry decisions into the suite
- `pytest-cov`, `hypothesis` added to `[project.optional-dependencies].dev`
- README badge: Codecov status next to the existing context-score badge
- CI uploads `coverage.xml` to Codecov via `codecov/codecov-action@v4` (gated on the canonical repo + one matrix cell so forks are not broken by missing enrollment)

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
