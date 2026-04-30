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
- PRD spec: `specs/prd-cross-workspace-telemetry-rollup.md` — design doc for `measure --all-repos`, a read-only fleet rollup over local telemetry. Decomposed into vertical-slice issues #106-#110. Implementation lands across those PRs. (#104)
- Self-observability layer (#73): new `repo_context_hooks.logging_setup` module — stdlib-only, zero-dep. WARNING records go to stderr by default; ERROR records are also appended to `<cache>/errors.log` (rotated 5 × 1 MB) where `<cache>` is `$XDG_CACHE_HOME/repo-context-hooks/logs/` on POSIX or `%LOCALAPPDATA%\repo-context-hooks\logs\` on Windows. Public surface is `configure_logging()`, `get_last_error()`, `log_path()`, and the test seam `_LOG_DIR_OVERRIDE`. M6's `verify` command (#74) imports the same surface. (#73)
- Global `--debug` flag on the CLI parser. Promotes stderr to DEBUG and writes full tracebacks to the rotating log. Top-level convention matches `--version`: intercepted in `main()` before subcommand dispatch, accessible from any subcommand via `args.debug`. (#73)
- `doctor` output now ends with a "Last error:" section. Reads the last non-blank line of `errors.log` via 4 KB seek-backwards (O(1) on arbitrarily large logs) and decodes with `errors="replace"` so a corrupt tail cannot crash the command. JSON output gains `last_error` and `log_path` keys for programmatic consumers. (#73)
- `repo-context-hooks --version` now prints semver + short git SHA + Python version + OS + best-effort install method (`pipx`/`uv`/`pip`). Source-checkout output: `repo-context-hooks 0.6.0 (git: a1b2c3d, python: 3.11.5, platform: linux)`; wheel-install output omits the `git:` segment. Monorepo-safe: SHA is suppressed unless the resolved git toplevel's `pyproject.toml` declares `name = "repo-context-hooks"`. Published regex `repo_context_hooks.version_info.RCH_VERSION_RE` for downstream parsers. (#76)
- `repo_context_hooks.changelog` module: stdlib-only CHANGELOG parser. `extract_section(text, version)` returns the body of `## [X.Y.Z]` for release-notes population (raises `LookupError` on missing/empty sections); `find_unreleased_changed_lines(diff_text)` powers the PR gate. CLI: `python -m repo_context_hooks.changelog [extract|gate]`. (#76)
- `.github/workflows/changelog-check.yml` enforces a `## [Unreleased]` entry on every PR. Strictness goes beyond "file changed" — we verify ≥1 added line lands inside `[Unreleased]` (an edit to a historical release section does NOT satisfy the gate). Skip via labels `skip-changelog`, `documentation`, `chore`, or `dependencies`; Dependabot/Renovate PRs are auto-exempted via actor check. (#76)
- `.github/workflows/publish.yml` auto-populates the GitHub Release page from `CHANGELOG.md` after a successful PyPI publish. Job-scoped `permissions: contents: write` (NEVER promote to top-level). Fails loud on missing/empty release section rather than silently overwriting an existing release body. (#76)
- Coverage gate via `pyproject.toml [tool.coverage.report] fail_under = 80`; CI enforces on every push and PR. Threshold rationale and ratchet plan: see issue [#92](https://github.com/narendranathe/repo-context-hooks/issues/92). (#71)
- Hypothesis property tests for telemetry hot paths: `is_sampled` boundaries + cached-decision stability + cache-invalidation re-roll, `repo_id` shape + stability, `deduplicate_hooks` on-disk idempotency. (#71)
- `tests/conftest.py`: shared `"rch"` Hypothesis profile, glob-based `REPO_CONTEXT_HOOKS_*` env-var isolation, pinned Hypothesis storage dir for read-only `$HOME` runners.
- `tests/test_bundle_scripts_compile.py`: `py_compile` smoke for every script shipped under `bundle/`.
- `tests/test_telemetry_edge_cases.py`: NaN/+inf/-inf rate contracts.
- README Codecov badge inside `<!-- BADGES:START/END -->` anchor block.
- Public-API stability contract (issue #72): explicit `__all__ = ["__version__"]` in `repo_context_hooks/__init__.py`, machine-readable snapshot at `tests/contract/public_surface.json`, CI gate `scripts/check_public_surface.py` (drift check + `--verify-removals` mode against prior release tag), and contract tests under `tests/contract/`. `docs/stability.md` and `docs/deprecation-policy.md` document stable vs internal surfaces and the one-MINOR-cycle deprecation rule. README adds `## Stability` section. (#72)

### Changed
- `cli.py` error-reporting `print()` calls now also emit a `logger.error()` record (TEE pattern). User-facing stdout output is preserved byte-for-byte — existing scripts that pipe `repo-context-hooks measure 2>/dev/null` still see error text — but the same message is now appended to `errors.log` so `doctor` and `--debug` runs surface it after the user has moved on. Migration sites: install warnings (cli.py), measure experiment start/finish failures (cli.py), checkpoint missing-git-repo / missing-workspace-contract / non-zero subprocess exit (cli.py). (#73)
- `is_sampled`: NaN sample-rate now coerces to 0.0 (safe-default opt-out) instead of silently falling through to `random.random() < NaN` and returning False with no diagnostic. (issue #71 audit follow-up)
- CI `permissions:` defaults to `contents: read`; the test job alone escalates to `id-token: write` for Codecov OIDC.
- CI matrix adds Python 3.13.

### Deprecated
<!-- none -->

### Removed
<!-- none -->

### Fixed
- `logging_setup._default_log_dir()` now wraps `Path.home()` in a `RuntimeError` guard with a `tempfile.gettempdir()` fallback. `Path.home()` raises `RuntimeError` (NOT `OSError`) on Windows SYSTEM accounts with unset `LOCALAPPDATA`, AWS Lambda layers, distroless containers, and hermetic Bazel sandboxes — exactly the global-adoption population v1.0 targets. The error fires before any handler can catch it, so without this fallback `configure_logging` crashed every subcommand including `doctor` itself. Phase 2 portability-axis review found this in PR #103 review. (#73)
- `find_unreleased_changed_lines()` now accepts a `head_changelog` post-image so the gate detects bullets added BELOW an existing `## [Unreleased]` heading. Previously, `--unified=0` diffs without the heading line returned 0 — surfaced when the gate red-X'd its own PR (#94). Regression test pins the exact diff shape. (#76)
- `tests/conftest.py` env-isolation list previously missed `REPO_CONTEXT_HOOKS_TELEMETRY_DIR`; switched to a `startswith()` glob that future-proofs every Wave 2/3 env var.

### Security
- Pin `codecov/codecov-action` to a 40-char SHA (was the floating `@v4` tag).
- Add upper version bounds to dev deps (`pytest<9`, `pytest-cov<8`, `hypothesis<7`) so a compromised future major release cannot auto-install in CI.
- Document why this workflow uses `pull_request` (not `pull_request_target`) so a future maintainer cannot accidentally migrate to the unsafe variant.
- Document Dependabot supply-chain policy in `SECURITY.md` (`pip` + `github-actions` ecosystems, weekly cadence, SHA-pin policy for third-party Actions, upper-bound dev-dep policy, fork extension guidance). Lock the ecosystem set with a stdlib-only regression guard at `tests/test_dependabot_policy.py` frozen against `tests/contract/dependabot_policy.json`. `docs/stability.md` declares `.github/dependabot.yml` a configuration contract — removing either ecosystem is now a MINOR-cycle deprecation event. Inline policy comment block added to `.github/dependabot.yml` so adopters reading the file in isolation know what they inherit. (#85)

### Tests
- New `tests/test_logging_setup.py` (~17 tests): Hypothesis-driven path-resolution matrix (XDG/LOCALAPPDATA/override × `os.name`), real rotation-fires test (writes 1.1 MB and asserts `errors.log.1` exists), `backupCount=4` cap test, lazy-attach-on-first-error, read-only fallback never raises, `get_last_error` edge cases (missing/empty/binary tail/oversize log <1s), idempotent configure. (#73)
- New `tests/test_doctor_last_error.py`: `Last error:` text rendering shows "No errors recorded" when the log is missing and the actual entry when populated; JSON payload gains `last_error` and `log_path` keys without disturbing existing `platform_id`/`ok` keys. (#73)
- New `tests/test_cli.py::test_parser_accepts_global_debug_flag`: verifies `--debug` is a top-level flag and the `args.debug` attribute is reachable from any subcommand. (#73)
- New `tests/test_logging_setup.py::test_log_path_falls_back_to_tempdir_when_home_unresolvable`: monkey-patches `Path.home()` to raise `RuntimeError` and asserts `log_path()` returns a path under `tempfile.gettempdir()` instead of crashing. Locks down the Windows-SYSTEM/Lambda/Nix-sandbox fix from Phase 2. (#73)
- New contract tests `tests/contract/test_public_surface.py::test_module_surface_pins_logging_setup_helpers` and `::test_doctor_json_emits_pinned_keys`: enforce that `repo_context_hooks.logging_setup.{configure_logging, get_last_error, log_path}` and the `doctor --json` keys (`last_error`, `log_path`, `ok`, `platform_id`) are stable for sibling PRs. M6's `verify` command (#74) imports these on day one — a rename is now a contract event, not a silent break. (#73)
- 347 tests (from 338 in PR #90); +9 added by this hardening branch.
- `tests/test_cli.py`: backfill `_checkpoint`, `_measure --clean-ghosts`, `_measure export`, `_measure experiment {start,finish,status}`, `_resolve_experiment_dir`, `_telemetry_cmd` (status/enable/disable/preview), and `main()` dispatch routing for `checkpoint`/`telemetry` — 46 new tests asserting output format, return code, and side effects (no call-the-function-for-the-line). Coverage gate `fail_under` ratchets from 80 to 85 (project total now ≥87%, `cli.py` ≥87%). Class-scoped autouse fixture redirects `consent._CONFIG_PATH_OVERRIDE` to a tmp path for every `_telemetry_cmd` test so `pytest` can never pollute the developer's real `%LOCALAPPDATA%`/`~/.config` consent state. Adopter note: `[tool.coverage.run] source = ["repo_context_hooks"]` scopes the gate to OUR code only — your own modules are unaffected. (#92)
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
