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
- Docs: example Session Log demonstrating the `checkpoint --message` workflow with 7 real v1.0.0 session decisions. Documents the canonical decision-capture pattern so adopters can see what a populated `## Session Log` looks like in practice.
- `specs/README.md`: new "Product Positioning (USPs)" section. 10 falsifiable USPs (each pinned to a CLI command, file path, or metric) plus the defensible-angle note and the hard non-goals list. Source of truth for external positioning so future blog posts, README sections, and PR descriptions anchor to the same claims.
- `marketing/posts/`: phased launch drafts for the v1.0.0 publicity push. Five posts (teaser, problem, solution+USPs, metrics, roadmap+contribute) each with Substack long-form + LinkedIn short-form variants, a posting schedule, a hashtag inventory, and per-post image-generation prompts. Drafts only; not part of the public stability contract.

### Changed
- `README.md` and `specs/README.md` refreshed to reflect the v1.0.0 ship: install snippet, badge row, USP framing, and the closed PRD #68 + PRD #104 milestones. No code or behavior change.

### Deprecated
<!-- none -->

### Removed
<!-- none -->

### Fixed
- `extract_repo_summary()` in both copies of `repo_specs_memory.py` now skips lines inside multi-line HTML comment blocks (#124). The previous implementation's `clean_line` helper only stripped single-line `<...>` tags via a regex that requires the opening and closing markers on the same line, so a multi-line `<!-- ... -->` block (e.g. the `BADGES:START` convention header in this repo's own README) had its body pass the prose filters and got concatenated into the AUTO:REPO_CONTEXT summary. The bug clobbered the AUTO block on every `SessionStart` fire — surfaced repeatedly during the v1.0.0 release session as `specs/README.md` drift in unrelated PRs. Regression test in `tests/test_repo_memory_contract.py::test_extract_repo_summary_skips_multi_line_html_comments` synthesises a README with the exact shape that triggered the bug. Both bundle script copies updated; `tests/test_bundle_integrity.py` enforces they stay in sync. (#124)
- `verify.run_verify()` now routes `Path.home()` through `_logging_setup._safe_home()` to inherit the cross-platform fallback ladder PR #103 added for `logging_setup`. Without this, verify crashed on Windows SYSTEM accounts, AWS Lambda layers, Nix sandboxes with read-only `$HOME`, and distroless containers without `/etc/passwd` — the same global-adoption population v1.0 targets. Phase 2 portability-axis review of PR #112 surfaced the regression. Bonus fix: `_init_synthetic_repo` now falls back from `git init --initial-branch=verify` (git 2.28+, Aug 2020) to plain `git init --quiet` so RHEL 7/8 / UBI 8 adopters with git 2.20/2.27 are not silently broken. (#74)
- `publish.yml`: both publish steps now pass `skip-existing: true` to `pypa/gh-action-pypi-publish`. Without this, retag scenarios fail with "400 File already exists" when the prior cycle already uploaded a given filename (observed when the v1.0.0 retag chain re-uploaded a wheel TestPyPI had already accepted on the first failed run). The TestPyPI flag is essentially mandatory; the PyPI flag makes the retag flow idempotent — PyPI still rejects overwrites unconditionally, the flag just suppresses the action-level error so downstream steps (`gh release edit`) still run.
- `publish.yml`: BOTH the TestPyPI and PyPI publish steps now move `*.sigstore.json` files out of `dist/` before invoking `pypa/gh-action-pypi-publish`. twine inspects the entire dist directory and rejects sigstore bundles as "Unknown distribution format" — observed first on TestPyPI (run 25242241509), then again on PyPI (run 25242421527) after the TestPyPI-only fix. The `attestations: true` flag mints fresh PEP 740 attestations via OIDC at publish time; it does not consume external sigstore bundles. Those bundles are still produced by the `Sign distributions with Sigstore` step in the build job and remain in the workflow artifact for off-PyPI verification (`sigstore verify identity ...`).
- `pages.yml`: main-push deploys now write to a `dev` version slot rather than `latest`. `latest` is reserved exclusively as an alias, repointed atomically on tag pushes via `mike deploy --update-aliases <version> latest`. The previous design (deploy `latest` as a version slot on main) failed the v1.0.0 tag deploy (run 25242241516) with `error: alias 'latest' already specified as a version` — mike forbids name reuse. An idempotent `mike delete --push latest` step cleans up the legacy version slot once; subsequent runs no-op.
- `pages.yml`: the `mike set-default --push latest` step now bootstraps a missing `latest` alias from the highest non-`dev` version on gh-pages before calling `set-default`, and skips cleanly when only `dev` exists. Without this, every main-push deploy after PR #91 failed at `error: identifier 'latest' does not exist` — the legacy-cleanup step had wiped the pre-v1.0.0 `latest` version slot, and no `latest` alias had been recreated since `versions.json` shows only `dev` and `1.0.0` with no aliases attached. First run on main re-aliases `1.0.0` as `latest`; subsequent runs find the alias and just re-set-default (idempotent).
- `README.md`: re-added the platform-support diagram embed (`assets/diagrams/platform-support.svg`) under `## Supported Platforms` and replaced the stale `### Live telemetry (this repo, v1.0.0)` table with a `### Local operational telemetry` section whose metric values are sourced directly from `docs/monitoring/history.json` (score 90, +70 uplift, 108 hook events, 3 active days, 25% lifecycle coverage, per-event-type breakdown). The previous table drifted from the checked-in history snapshot, breaking three README contract tests (`test_readme_embeds_monitoring_brand_assets`, `test_readme_embeds_required_diagrams`, `test_readme_uses_latest_local_telemetry_proof_values`) on every main-push CI run.

### Security
<!-- none -->

### Tests
<!-- none -->

## [1.0.0] - 2026-05-01

The v1.0 production-readiness release. Closes PRD #68 (10 vertical slices: community
health, supply-chain hardening, coverage gate, stability contract, self-observability,
install/uninstall UX, docs depth, release engineering, governance polish, team-scope
clarity) and PRD #104 (cross-workspace telemetry rollup, 5 vertical slices).

Adopters: this is the first release with a stable public surface contract — see
`docs/stability.md` and `docs/deprecation-policy.md`. The `__all__` export, every
documented CLI subcommand and flag, the `--platform` choices, the
`REPO_CONTEXT_HOOKS_*` environment variable namespace, and the documented file
locations are all part of the contract from this release forward.

### Added
- `measure --all-repos`: cross-workspace tokens-saved rollup with `--top`, `--include-ghosts`, `--redact`, and `--json`. Walks every workspace under the telemetry base read-only, applies the same `_build_usability` substring-match formula already used by single-repo `measure`, and prints a fleet summary plus a top-N table. JSON output is a versioned contract (`schema_version: 1`) suitable for CI policy gates and external dashboards. `REPO_CONTEXT_HOOKS_TELEMETRY=0` short-circuits to a one-line opt-out message without reading any files. See `TELEMETRY.md` § Fleet Rollup. (#104, #107, #108, #109, #110)
- Install/uninstall UX layer (#74): new `repo-context-hooks verify [--platform PLATFORM]` subcommand. Synthesizes a `SessionStart` event into an isolated tmpdir, round-trips it through the local telemetry write/read path, schema-validates against the new `repo_context_hooks.telemetry.CANONICAL_EVENT_KEYS` constant, and prints a confirmation receipt (platform, agent home, settings.json sha256 over the **canonical** JSON form, last event timestamp, elapsed ms). Completes in <2s. Exit code: 0 healthy, 1 broken, 2 cold-start (no platforms detected — receipt names the install command to run). `--json` flag emits machine-parseable output for CI policy gates. The `verify` module's public surface is `VerifyReport` + `run_verify(platform)` — M7 (#75) consumes this for mkdocs-click auto-generation. (#74)
- `--dry-run` on `install` and `uninstall`. Routes through new pure planning functions (`plan_global_hooks`, `plan_uninstall_global_hooks`, `plan_deduplicate_hooks`) that compute the would-be `settings.json` diff via `difflib.unified_diff` over canonical JSON (`sort_keys=True, indent=2`) and exit without writing. The dry-run guarantee is mechanical: a unit test monkeypatches `_save_json` to raise, asserting zero writes happen on the dry-run path. `--dry-run` and `--force` are parser-mutex on `install` (argparse exits 2 on conflict — Critic C non-budge). PARTIAL adapters (cursor/codex/replit/windsurf/lovable/openclaw/ollama/kimi) get an explicit "PARTIAL adapter: bundle copy only, no settings.json mutation" line rather than silently no-opping. (#74)
- Version-migration tests using real settings.json fixtures from the v0.5.0 and v0.6.0 lineage (`tests/fixtures/migrations/v0_5_settings.json`, `v0_6_settings.json`). Each fixture deliberately includes user-authored hooks alongside legacy rch hooks. Tests assert (a) every user hook survives `install_global_hooks` re-run, (b) install is idempotent (second install is a no-op), (c) top-level keys like `permissions` are preserved. Plus a Hypothesis property test (`test_property_install_preserves_arbitrary_user_hooks`, 50 examples on the `"rch"` profile) over arbitrary 0.5-shaped settings.json. Plus an empty-bytes regression test. (#74)
- `repo_context_hooks.telemetry.CANONICAL_EVENT_KEYS`: tuple of the 10 keys every `record_event` call carries. Single source of truth for schema-drift detection. `verify` imports this — adding a key in `record_event` without updating this tuple now causes `verify` to flag the drift via `schema_missing_keys`. (#74)
- `repo_context_hooks.platforms.runtime.SettingsPlan`: frozen dataclass returned by the new `plan_*` functions. Fields: `settings_path`, `current_text`, `proposed_text`, `diff` (tuple of unified-diff lines), `action` (`"install"|"skip"|"uninstall"|"no changes"`), `statuses` (mirrors the legacy return-dict contract so the apply wrappers don't change callers). (#74)
- `is_ghost_repo(repo_dir: Path) -> bool` predicate in `repo_context_hooks.telemetry` (#106): side-effect-free classifier extracted from `purge_ghost_repos`. Same rule (`<2 events AND repo_name in {"repo", "tmp", "temp", "test"}`); now callable without triggering deletion. Unblocks #107 (cross-workspace rollup walker) which needs to ask "is this dir a ghost?" while doing read-only aggregation. Behavior of `purge_ghost_repos` is unchanged. (#106)
- PRD spec: `specs/prd-cross-workspace-telemetry-rollup.md` — design doc for `measure --all-repos`, a read-only fleet rollup over local telemetry. Decomposed into vertical-slice issues #106-#110. Implementation lands across those PRs. (#104)
- Cross-workspace rollup CLI (#108): new `measure --all-repos` flag prints a fleet-level rollup walking every workspace under the resolved telemetry base. Reuses the rollup core from #107. Three new measure flags: `--all-repos` (boolean trigger), `--include-ghosts` (flips the default ghost filter off), `--top N` (table truncation, default 15, `--top 0` shows all). Reuses `--json` (emits the `schema_version: 1` JSON contract from #107) and `--redact` (when set, replaces `repo_name` with `sha256(name)[:12]` in both text and JSON output via `redact_repo_name`). `REPO_CONTEXT_HOOKS_TELEMETRY=0` short-circuits at the CLI level: prints "Telemetry disabled; rollup is opt-out." and exits 0 without invoking `rollup_telemetry()` (zero filesystem reads). `tests/contract/public_surface.json::measure.flags` updated with the three new entries — `--redact` and `--json` were already in the contract. (#108)
- Cross-workspace telemetry rollup core (#107): new `repo_context_hooks.telemetry.RollupReport` (with `RollupSummary`, `RollupRepo`) frozen dataclass + `rollup_telemetry(*, base=None, include_ghosts=False) -> RollupReport` walker + `redact_repo_name(name) -> str` hashing helper. Walks every workspace directory under the resolved telemetry base, applies the same `_build_usability` substring-match formula already used by `measure_impact` (`session_starts = sum(1 for n in names if "session-start" in n)`, `tokens_saved = round(session_starts * 0.30 * 2000)`), aggregates event counts and distinct sessions, and returns a versioned report (`schema_version: 1`). Honors the `REPO_CONTEXT_HOOKS_TELEMETRY=0` opt-out (returns an empty report without reading the filesystem) and `REPO_CONTEXT_HOOKS_TELEMETRY_DIR` override. Per-workspace records sort desc by `tokens_saved`. Ghost workspaces are excluded by default via `is_ghost_repo` (#106) and surfaced via `include_ghosts=True`. Corrupt JSONL lines are silently skipped (matches `_read_events` tolerance). The CLI surface (`measure --all-repos`) lands in #108; docs in #110. (#107)
- Docs depth (#75): new `docs/troubleshooting.md` covering six verified failure modes (hooks not firing, `events.jsonl` empty, `settings.json` clobbered, Windows paths, multi-Python shadowing, `verify` exits 1) — each entry sourced from a closed issue (#41, #57, #58, #46, #32, #74/#73), self-contained with symptom/reproduce/fix/last-verified, no admonitions, OS labels inline. New `docs/cli-reference.md` rendered from `repo_context_hooks.cli:build_parser` by the stdlib-only `scripts/render_cli_reference.py` (no `mkdocs-click` plugin — argparse, not Click). New `[project.optional-dependencies] docs` extra (`mkdocs-material>=9,<10`, `mike>=2,<3`) kept separate from `dev` so pytest contributors do not pull mkdocs. `mkdocs.yml` adds `mike` plugin and version selector; `pages.yml` switches from flat `mkdocs gh-deploy` to `mike deploy --push --update-aliases <version> latest` with `mike set-default --push latest`, gated to the canonical repo and serialized via `concurrency: gh-pages-deploy`. New `docs-build` job in `ci.yml` runs `mkdocs build --strict` and the CLI-reference drift gate on every PR. New `tests/contract/test_docs_contract.py` (stdlib-only, travels with the package) asserts subcommand drift, `Last verified` footers, and CDN-free docs. Quickstart copy-paste terminal block added to `README.md` and `docs/index.md` covering install → verify → measure in three steps. (#75)

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
- `measure --redact` flag default flipped from `True` to `False` (#108). The flag was previously documented as "always enforced" because `measure export` hardcodes `redact=True` regardless — so the default was vestigial and the new opt-in semantics for `--all-repos` give the flag actual meaning. `measure export` behavior is unchanged (still always redacts via the hardcoded call site). No other CLI subcommand consumed the `--redact` default. (#108)
- `repo_context_hooks/platforms/runtime.py`: `install_global_hooks`, `uninstall_global_hooks`, `deduplicate_hooks` are now thin wrappers around their pure `plan_*` counterparts. Same signatures, same return-dict contracts — the existing test suite needs zero updates. The split was driven by the consensus from issue #74's three parallel critics (Critic B non-budge: dry-run must route through pure planners). (#74)
- `cli.py` error-reporting `print()` calls now also emit a `logger.error()` record (TEE pattern). User-facing stdout output is preserved byte-for-byte — existing scripts that pipe `repo-context-hooks measure 2>/dev/null` still see error text — but the same message is now appended to `errors.log` so `doctor` and `--debug` runs surface it after the user has moved on. Migration sites: install warnings (cli.py), measure experiment start/finish failures (cli.py), checkpoint missing-git-repo / missing-workspace-contract / non-zero subprocess exit (cli.py). (#73)
- `is_sampled`: NaN sample-rate now coerces to 0.0 (safe-default opt-out) instead of silently falling through to `random.random() < NaN` and returning False with no diagnostic. (issue #71 audit follow-up)
- CI `permissions:` defaults to `contents: read`; the test job alone escalates to `id-token: write` for Codecov OIDC.
- CI matrix adds Python 3.13.

### Deprecated
<!-- none -->

### Removed
<!-- none -->

### Fixed
- `pages.yml` mike deploy: split the `--update-aliases` flag off the non-tag (push-to-main) path. Mike rejects `mike deploy --update-aliases latest latest` with "duplicated version and alias" when the version slot and the alias share a name. Tag pushes still pass `--update-aliases <version> latest`. Caught by the first post-#113 deploy (run 25224017603). (#75 follow-up)
- `logging_setup._default_log_dir()` now wraps `Path.home()` in a `RuntimeError` guard with a `tempfile.gettempdir()` fallback. `Path.home()` raises `RuntimeError` (NOT `OSError`) on Windows SYSTEM accounts with unset `LOCALAPPDATA`, AWS Lambda layers, distroless containers, and hermetic Bazel sandboxes — exactly the global-adoption population v1.0 targets. The error fires before any handler can catch it, so without this fallback `configure_logging` crashed every subcommand including `doctor` itself. Phase 2 portability-axis review found this in PR #103 review. (#73)
- `find_unreleased_changed_lines()` now accepts a `head_changelog` post-image so the gate detects bullets added BELOW an existing `## [Unreleased]` heading. Previously, `--unified=0` diffs without the heading line returned 0 — surfaced when the gate red-X'd its own PR (#94). Regression test pins the exact diff shape. (#76)
- `tests/conftest.py` env-isolation list previously missed `REPO_CONTEXT_HOOKS_TELEMETRY_DIR`; switched to a `startswith()` glob that future-proofs every Wave 2/3 env var.

### Security
- Pin `codecov/codecov-action` to a 40-char SHA (was the floating `@v4` tag).
- Add upper version bounds to dev deps (`pytest<9`, `pytest-cov<8`, `hypothesis<7`) so a compromised future major release cannot auto-install in CI.
- Document why this workflow uses `pull_request` (not `pull_request_target`) so a future maintainer cannot accidentally migrate to the unsafe variant.
- Document Dependabot supply-chain policy in `SECURITY.md` (`pip` + `github-actions` ecosystems, weekly cadence, SHA-pin policy for third-party Actions, upper-bound dev-dep policy, fork extension guidance). Lock the ecosystem set with a stdlib-only regression guard at `tests/test_dependabot_policy.py` frozen against `tests/contract/dependabot_policy.json`. `docs/stability.md` declares `.github/dependabot.yml` a configuration contract — removing either ecosystem is now a MINOR-cycle deprecation event. Inline policy comment block added to `.github/dependabot.yml` so adopters reading the file in isolation know what they inherit. (#85)

### Tests
- Cross-workspace rollup integration test (#109): `tests/test_telemetry_rollup_integration.py` builds a synthetic 3-workspace telemetry tree (real with 5 session-starts, ghost matching the `<2 events AND repo_name in {"repo","tmp","temp","test"}` heuristic, real with 1 valid + 1 corrupt JSONL + 1 valid line) and locks down the headline numbers across the entire M1-M6 chain. By-hand math: real-only `tokens_saved == round(6 * 0.30 * 2000) == 3600`, `tokens_injected == 27000`. Asserts ghost excluded by default and surfaced under `include_ghosts=True`, corrupt JSONL silently skipped, sort order desc by `tokens_saved`, `schema_version: 1`, and end-to-end through `main(["measure", "--all-repos", "--json"])`. The synthetic-base builder is intentionally local — promoting to `conftest.py` would expand its surface (currently scoped to isolation concerns); a second consumer can lift the helper later. (#109)
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
