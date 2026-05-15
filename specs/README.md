# Engineering Memory

This file is the persistent project context for agents and maintainers.

## Repo Context Index

<!-- AUTO:REPO_CONTEXT_START -->
### Canonical Context Sources

- User-facing overview: `README.md`
- Engineering memory: `specs/README.md`
- Glossary: `UBIQUITOUS_LANGUAGE.md`
- Source of truth: checked-in repo docs, not chat-only summaries

### Repo Summary

- Agent-level continuity skill for coding agents. `repo-context-hooks` is an agent-level skill that keeps interrupted work, next-step context, and handoff notes alive across sessions. Install once to agent home — every workspace you open picks it up automatically.
<!-- AUTO:REPO_CONTEXT_END -->

## Architecture and Design Constraints

- Keep the public claim boundary honest. Claude is the native path; the other shipped platforms are partial integrations with documented caveats.
- Favor repo-native continuity over hosted memory claims. This product should remain inspectable in git and understandable without a separate memory backend.
- Treat `README.md`, `specs/README.md`, and `UBIQUITOUS_LANGUAGE.md` as durable source-of-truth files, not disposable bootstrap output.
- Prefer platform-specific adapters and playbooks over generic "supports every agent" language.

## Built So Far

- We turned an internal continuity workflow into a public open source product named `repo-context-hooks`.
- The product is intentionally positioned around repo-native continuity for coding agents rather than generic "AI memory" claims.
- We shipped a real install/runtime surface with three command names that resolve to the same product:
  - `repo-context-hooks`
  - `repohandoff`
  - `graphify`
- We built and documented credible support for:
  - Claude (`native`)
  - Cursor (`partial`)
  - Codex (`partial`)
  - Replit (`partial`)
  - Windsurf (`partial`)
  - Lovable (`partial`)
  - OpenClaw (`partial`)
  - Ollama (`partial`)
  - Kimi (`partial`)
- We also shipped the surrounding product surface:
  - installer flows
  - repo contract bootstrap
  - doctor checks
  - platform playbooks
  - diagrams
  - launch copy
  - roadmap/issues
- Releases completed so far:
  - `v0.1.0`: initial public platform foundation
  - `v0.2.0`: platform polish and consolidation
  - `v0.2.1`: canonical repo memory contract plus repo-first onboarding
  - `v0.2.4`: continuity impact monitoring, public telemetry snapshots, and README brand/visibility polish
  - `v0.3.0`: agent-level skill runtime, session metrics sampling, CI/CD matrix, PyPI OIDC publish
  - `v0.5.0`: telemetry reliability — sampling gate fixes, lifecycle coverage repair, session duration
  - `v0.6.0`: session decision capture (`checkpoint`), shareable export, before/after experiment, telemetry consent layer
  - `v1.0.0`: production-readiness release — first stable public surface contract; closes PRD #68 (10 slices) + PRD #104 (cross-workspace rollup, 5 slices). PyPI 1.0.0 published with Sigstore + PEP 740 attestations; docs site versioned via `mike`
- We shipped semantic decision capture: `repo-context-hooks checkpoint --message "..."` writes agent decisions and rationale into `## Session Log` in `specs/README.md`.
  - `write_decision_entry()` in `repo_specs_memory.py` appends timestamped, branch-stamped entries under the Session Log heading
  - Automated checkpoints (`pre-compact`, `session-end`) now include the last 3 git commits alongside changed files
  - `context-handoff-hooks` SKILL.md rewritten with concrete PreCompact and SessionEnd write-back steps + checkpoint message format template
  - 2 new tests: `test_decision_entry_written_to_session_log`, `test_checkpoint_appends_recent_commits`
  - 2 new CLI tests: `test_parser_supports_checkpoint_command`, `test_parser_checkpoint_requires_message`
  - `## Session Log` section now scaffolded in every new workspace contract
- We shipped cross-workspace telemetry rollup (PRD #104) — `measure --all-repos` walks every workspace under the telemetry base read-only and prints fleet-level tokens-saved, session counts, and a top-N table. The chain landed across five PRs:
  - `#106` extracts `is_ghost_repo` predicate from `purge_ghost_repos` (side-effect-free classifier the rollup walker reuses)
  - `#107` adds the rollup core: `RollupReport` + `RollupSummary` + `RollupRepo` frozen dataclasses, `rollup_telemetry()` walker, `redact_repo_name()` helper, `schema_version: 1` JSON contract
  - `#108` wires the CLI: `measure --all-repos --include-ghosts --top --redact --json` with an env opt-out short-circuit and `public_surface.json` contract update
  - `#109` adds a regression-grade integration test that locks down headline numbers against by-hand math on a synthetic 3-workspace tree (real / ghost / corrupt-JSONL)
  - `#110` ships the docs (this entry, `TELEMETRY.md` § Fleet Rollup, and a cross-link from `docs/monitoring.md`)
- We shipped the v1.0 production-readiness sprint (PRD #68) — closes ten vertical slices and ships the first stable public surface contract:
  - `#69` community health files (`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, issue/PR templates)
  - `#70` supply-chain hardening (Sigstore signing, Dependabot weekly cadence with SHA pins, CodeQL workflow)
  - `#71` coverage gate (85% via `pyproject.toml`) + Hypothesis property tests for `is_sampled` / `repo_id` / `deduplicate_hooks`
  - `#72` stability contract — explicit `__all__`, `tests/contract/public_surface.json` snapshot, `scripts/check_public_surface.py --verify-removals` CI gate, `docs/stability.md` and `docs/deprecation-policy.md`
  - `#73` self-observability — `repo_context_hooks.logging_setup` module, global `--debug` flag, `doctor` "Last error" surface
  - `#74` install/uninstall UX — `verify` command, `--dry-run` on install/uninstall, version-migration tests against real v0.5/v0.6 fixtures
  - `#75` docs depth — troubleshooting page, auto-rendered CLI reference, `mike` versioned docs, copy-paste quickstart
  - `#76` release engineering — changelog gate, auto-populated GitHub Release notes, richer `--version`
  - `#77` legal/governance polish (`NOTICE`, zero-deps callout, maintainer-status section)
  - `#78` team-scope clarity (link `#26` from README, single-dev scope callout)

### 2026-04-27 21:50 - decision (main)

Built: repo-context-hooks checkpoint --message CLI command + Session Log section in workspace contracts + write_decision_entry() in repo_specs_memory.py. Decided: keep session-start as read-only (no auto-scaffold) to preserve degradation contract — init is the explicit setup step. Decided: Session Log (agent-written semantic entries) stays separate from Session Checkpoints (automated mechanical data). Decided: SKILL.md rewritten with hard PreCompact/SessionEnd write-back steps + checkpoint message format template so the agent knows exactly what to write. Built: richer automated checkpoints now include last 3 git commits. 253/253 tests pass. Synced to ~/.claude/skills. Next: cut a release (v0.6.0) with these changes.

### 2026-05-01 23:03 - decision (docs/demo-session-log-checkpoints)

Built: docs/cli-reference.md auto-rendered from cli.py:build_parser via stdlib script (scripts/render_cli_reference.py + drift gate in tests/contract/test_docs_contract.py). Decided: amend issue #75's mkdocs-click spec because mkdocs-click is Click-only and build_parser returns argparse.ArgumentParser; porting to Click would break docs/stability.md's v1.0 surface contract. Stdlib pre-render + diff gives the same 'no drift possible' guarantee with zero new build deps. Three layers of drift gating: contract test re-runs the renderer in-process, --check step in pages.yml + ci.yml, plus a literal-subcommand assertion. Next: shipped as PR #113 (M7 docs depth).

### 2026-05-01 23:03 - decision (docs/demo-session-log-checkpoints)

Built: pages.yml splits deploys by trigger — main pushes write to a 'dev' version slot, tag pushes use 'mike deploy --push --update-aliases <version> latest'. Decided: 'latest' is reserved exclusively as an alias because mike forbids reusing a name as both version slot and alias (fails with 'error: alias latest already specified as a version'). Idempotent 'mike delete --push latest' step handles the one-time legacy cleanup. Caught when v1.0.0 tag deploy run 25242241516 failed against the previous design that deployed 'latest' as a version slot on every main push. Next: shipped as PR #119 (release-engineering fix).

### 2026-05-01 23:03 - decision (docs/demo-session-log-checkpoints)

Built: publish.yml moves *.sigstore.json out of dist/ before BOTH TestPyPI and PyPI publish steps; passes skip-existing: true to both. Decided: pypa/gh-action-pypi-publish's 'attestations: true' flag mints fresh PEP 740 attestations via OIDC at publish time — it does NOT consume external sigstore bundles produced by gh-action-sigstore-python. The bundles trip twine's check on every file in dist/ before any attestation logic runs. Bundles are kept in the workflow artifact for off-PyPI verification only. Decided: skip-existing on TestPyPI is essentially mandatory for retag idempotency (every retag re-uploads the same filename); on PyPI it just suppresses action-level error so downstream gh release edit still runs. Caught when v1.0.0 retag chain hit InvalidDistribution then 400 File already exists. Next: shipped as PRs #121 and #122.

### 2026-05-01 23:03 - decision (docs/demo-session-log-checkpoints)

Built: --redact CLI flag default flipped from True to False as part of measure --all-repos wiring. Decided: the original default=True was vestigial — measure export hardcoded redact=True regardless of the flag, so the default carried no observable behavior. The new opt-in semantics for 'measure --all-repos --redact' give the flag actual meaning (replace repo_name with sha256(name)[:12] in both text and JSON output via redact_repo_name). measure export is unchanged (still always redacts via the hardcoded call site). Verified by tests/test_cli.py::test_measure_export_redact_default continuing to pass — the redact flag was never the source-of-truth for export, only for the new --all-repos rollup. Next: shipped as PR #116 (M5+M6 CLI surface).

### 2026-05-01 23:04 - decision (docs/demo-session-log-checkpoints)

Built: 3-workspace synthetic test fixture for cross-workspace rollup integration test. Decided: keep _build_three_workspace_tree LOCAL to tests/test_telemetry_rollup_integration.py rather than promoting to tests/conftest.py. conftest.py is currently scoped tightly to isolation concerns (Hypothesis storage, profile, env-var stripping); adding a workspace-fixture builder for a single consumer would expand its surface prematurely. When a second consumer materializes, the helper imports cleanly from the test module or can be lifted then. Trade-off: minor duplication risk if PRD #104 grows more integration tests vs cleaner conftest.py boundary today. Next: shipped as PR #117 (M7 integration).

### 2026-05-01 23:04 - decision (docs/demo-session-log-checkpoints)

Built: codified when to use Phase-1+Phase-2 critic-and-ALT pattern vs pure TDD. Decided: Phase-1 (3 critics: global-adoption / repo-conventions / failure-modes lens) + Phase-2 (5 parallel ALT implementations in worktrees, judged on Repo fit / Global-adoption / Maintenance / Pain-relief, total /20) is the right tool for HIGH-STAKES shippables — used for issues #73 (self-observability), #74 (verify command), #75 (docs depth). Phase 1 won every time (19/20, 20/20) but ALTs surfaced real concerns the consensus would have missed (e.g., ALT 1 caught the Path.home() regression now scheduled as the May 8 follow-up routine). Decided: pure TDD red-green-refactor in a single session is sufficient for SMALLER single-issue feature slices like the PRD #104 chain (#107 / #108 / #109 / #110) — the fortress is overkill for <300 line slices. Next: heuristic captured in this Session Log entry so future sessions can route by complexity without re-litigating.

### 2026-05-01 23:04 - decision (docs/demo-session-log-checkpoints)

Built: shipped v1.0.0 to PyPI with Sigstore + PEP 740 attestations after THREE retag cycles. Decided: capture the release-engineering tax explicitly so v1.0.1 onward is one-shot. Tax was three separable bugs that only surface on the first real tag: (1) PR #119 — pages.yml mike collision, latest reserved as alias not version slot; (2) PR #121 — publish.yml had to move sigstore bundles out of dist/ before PyPI step (PR #119 only patched TestPyPI; my misdiagnosis assumed attestations: true would consume external bundles, but it mints fresh attestations via OIDC); (3) PR #122 — skip-existing: true on both publish targets for retag idempotency (TestPyPI rejects same-filename re-upload). Each fix unblocked the next stage and exposed the next gotcha. Verified live: PyPI 1.0.0 published, docs site /1.0.0/ renders, latest alias points at 1.0.0, GitHub Release notes auto-populated from CHANGELOG. Next: hold the v1.0 surface; v1.0.1 will ship from the same workflow without retag cycles.

## Delivery Timeline

### Phase 1: Product Identity

- We renamed and repositioned the project until the public name matched what the product actually does.
- We rejected vague memory-platform language because it overlapped with existing products and would have overpromised the implementation.
- We settled on a sharper product story: repo-native continuity, interruption-safe handoff, and restart-from-repo workflows.

### Phase 2: Public GitHub Surface

- We rewrote the README so it could work as a real public landing page instead of an internal operator notebook.
- We added diagrams, docs, examples, launch materials, and competitive framing.
- We removed internal-only wording and draft-only critique sections that were useful during design but wrong for the public README.

### Phase 3: Adapter Foundation

- We introduced explicit platform adapters and support tiers instead of pretending every tool has the same lifecycle primitives.
- We created a platform matrix backed by tests so the docs could not drift too far from the implementation.
- We opened follow-up issues for unsupported or partially-supported ecosystems instead of inflating the support story.

### Phase 4: Platform Expansion

- We implemented credible partial support for Replit, Windsurf, Lovable, OpenClaw, Ollama, and Kimi.
- For hybrid/manual platforms, we kept the support boundary honest:
  - Lovable uses exported repo knowledge plus manual UI knowledge steps
  - OpenClaw uses workspace files but still requires manual runtime configuration
  - Ollama support is Modelfile/template support, not full repo-aware agent-runtime support
  - Kimi support is scoped to Kimi Code CLI project context

### Phase 5: Canonical Repo Memory Contract

- We promoted `specs/README.md` and `UBIQUITOUS_LANGUAGE.md` into tracked canonical files on `main`.
- We reduced the noisy memory-sync behavior so branch-specific churn stopped polluting the top-level memory block.
- This made the repo contract inherit cleanly across future worktrees.

### Phase 6: Repo-First Onboarding

- We added:
  - `repo-context-hooks init`
  - repo-wide `repo-context-hooks doctor`
- This aligned the CLI with the product story:
  - establish repo contract first
  - validate repo contract
  - then install platform-specific continuity surfaces

### Phase 7: Platform Readiness

- We designed and implemented the next operator layer:
  - `repo-context-hooks doctor --all-platforms`
  - `repo-context-hooks recommend`
- This phase reduces guesswork after onboarding by showing support-wide readiness and transparent next-step recommendations.
- The implementation is complete in the active feature branch and verified locally.

### Phase 8: Agent-Level Skill Runtime

- We promoted the install model from per-repo hooks to agent-home hooks:
  - hooks write to `~/.claude/settings.json` once; active in every workspace automatically
  - `--also-repo-hooks` flag for per-repo opt-in alongside the global skill
- We added session metrics infrastructure:
  - `session_id` in every telemetry event
  - `is_sampled()` probabilistic gate (10% default, `REPO_CONTEXT_HOOKS_SAMPLE_RATE` env var)
  - `auto_commit_snapshot()` on session end
- We added graceful degradation for non-git and no-contract workspaces.
- We shipped Codex global hooks parity via `install_global_hooks()`.
- We added GitHub Actions CI matrix (Python 3.9-3.12, ubuntu + windows) and OIDC PyPI publish.
- Released as `v0.3.0` — live on PyPI.

## Design Decisions

- Position the product as repo-native continuity, not as a generic AI memory database.
- Keep the public README outcome-focused and move operator-heavy details into docs and playbooks.
- Model platform support with explicit tiers (`native`, `partial`, `planned`) instead of broad compatibility claims.
- Track compatibility aliases (`repo-context-hooks`, `repohandoff`, `graphify`) while keeping the product language centered on `repo-context-hooks`.
- Treat the repo contract as the durable continuity boundary:
  - `README.md` for user-facing understanding
  - `specs/README.md` for engineering memory
  - `UBIQUITOUS_LANGUAGE.md` for shared terminology
- Keep verification and advice separate:
  - `doctor` verifies actual state
  - `recommend` explains the best next move
- Keep evidence and claims separate:
  - `measure` reports local continuity signals and observed hook events
  - public copy must describe this as operational evidence, not a scientific productivity benchmark
- Keep telemetry trust boundaries explicit:
  - local telemetry is on by default because it stays local
  - remote telemetry must be opt-in, revocable, and policy-backed
  - cookies are not appropriate for CLI/hook/MCP telemetry
- Keep partial platforms useful without pretending they expose Claude-style hook parity.

## What Worked

- Tight claim boundaries improved trust: each platform is documented according to its real integration surface.
- Platform-specific adapters plus playbooks made the product more useful without pretending every tool has Claude-style hooks.
- Contract tests on README, docs, templates, and visuals helped keep product positioning and implementation in sync.
- Repo-first onboarding made the product easier to understand and made the CLI match the product promise.
- Canonical tracked memory files reduced repeated worktree clutter and made context continuity feel intentional.
- Product-driven development with real issues, PRs, releases, and checkpoints created a stronger public artifact than one large undocumented push would have.
- Adding a local measurement loop makes the product easier to trust because users can inspect whether hooks actually fired before they believe the continuity story.

## What Failed or Was Reverted

- Overly internal README sections hurt the public GitHub landing page and had to be removed.
- Broad "all agents" wording created avoidable trust gaps because the runtime support was narrower than the marketing language.
- Leaving repo memory files untracked caused repeated worktree noise and made the contract feel optional instead of canonical.
- Early diagrams were too generic and had to be improved because they explained the mechanism without showing enough real product value.
- Some verification paths exposed environment-specific issues that should be tracked separately instead of patched blindly inside feature branches.
- Editable-install verification on Windows/Conda exposed a console-launcher quirk that is now tracked as follow-up work instead of being buried.

## Releases, PRs, and Current State

- `main` currently includes all shipped work through `v1.0.0`:
  - platform foundation, polish, and adapters for nine platforms
  - canonical repo memory contract and repo-first onboarding
  - continuity impact monitoring and local evidence loop
  - agent-level skill runtime, session metrics, CI/CD matrix
  - session decision capture (`checkpoint --message`) + Session Log scaffolding
  - cross-workspace telemetry rollup (PRD #104)
  - v1.0 production-readiness (PRD #68): community files, supply-chain hardening, coverage gate, stability contract, self-observability, install/uninstall UX, docs depth, release engineering, legal/governance polish
- Latest release: `v1.0.0` — live on PyPI (`pip install repo-context-hooks`) with Sigstore signature and PEP 740 attestations
- Docs site: [https://narendranathe.github.io/repo-context-hooks/1.0.0/](https://narendranathe.github.io/repo-context-hooks/1.0.0/) (versioned via `mike`; `latest` alias points at 1.0.0)
- CI: 611 tests, matrix jobs (ubuntu + windows, Python 3.9/3.11/3.12/3.13), coverage 88%+ enforced at 85% gate
- Public surface contract enforced by `tests/contract/public_surface.json` + `scripts/check_public_surface.py --verify-removals` so any breaking change without a deprecation cycle fails CI

## Open Issues and Next Work

PRD #68 (v1.0 production-readiness) and PRD #104 (cross-workspace rollup) both shipped via v1.0.0 on 2026-05-01. The repo is now in steady state.

Priority backlog (next-action items):

- **#74 portability follow-up** - scheduled remote agent (`trig_01BekHmLKcYnZahPCoQaKMLg`) opens a PR routing `verify.run_verify()`'s `Path.home()` through `_logging_setup._safe_home()` to inherit the cross-platform fallback ladder PR #103 added for `logging_setup`. Bonus: `_init_synthetic_repo` falls back from `git init --initial-branch=verify` to plain `git init` for RHEL 7/8 / UBI 8 with git 2.20/2.27.
- **#97** - Property-test argparse graph for stability-gate top-level-flag regressions
- **#96** - Drop git dependency in public-surface gate `--verify-removals` (frozen baseline file)
- **#101** - Tighten SECURITY.md cross-link test
- **#82 / #83** - Dependabot github_actions bumps for `setup-python` and `checkout` (close the Node.js 20 deprecation gap)
- **Long-tail (post-v1.x)**:
  - **#26** - Build consented remote telemetry and MCP reporting (the v1.x successor to PRD #104)
  - **#25** - Investigate Codex hook telemetry when hook support stabilizes
  - **#23** - Improve guided before/after impact experiment flow

Ongoing:
- Keep the repo memory contract canonical and low-noise.
- Continue raising platform quality through real support surfaces, not expanded marketing copy.
- Hold the public surface contract — any change to the v1.0 surface needs a deprecation cycle through `docs/deprecation-policy.md`.

## How To Work in This Repo

- Read `README.md` first for user-facing behavior and contribution flow.
- Read this `specs/README.md` before implementation.
- Read `UBIQUITOUS_LANGUAGE.md` before renaming core concepts or adding new public terms.
- Keep support claims narrow unless docs, tests, and install behavior all support widening them.
- Update this file before `compact` and at session end.
- Preserve merged feature and release branches unless the user explicitly asks to delete them.

## Session Log

- Append decision summaries and handoff notes here at session end and compaction.
- Each entry records what was built, key decisions made, and the next step.
- Written by the agent via `repo-context-hooks checkpoint --message '...'`.

### 2026-05-01 - decision (main): v1.0.0 release sprint

**Built**: Closed PRD #68 (10 vertical slices) and PRD #104 (5 slices) and shipped v1.0.0 to PyPI with Sigstore + PEP 740 attestations. Live docs site at `/1.0.0/` with `latest` alias via `mike`. 611 tests, coverage 88.4%.

**Key decisions and trade-offs surfaced this session:**

- **CLI reference rendering** — issue #75 specified `mkdocs-click` for auto-rendering `cli.py:build_parser`, but `mkdocs-click` is Click-only and `build_parser` returns `argparse.ArgumentParser`. Three resolutions considered: (a) port to Click, rejected because it would break `docs/stability.md`'s v1.0 surface contract; (b) `mkdocs-argparse` plugin, rejected because third-party / unmaintained on PyPI; (c) stdlib pre-render script + drift gate. **Picked (c)**: `scripts/render_cli_reference.py` introspects argparse via `_actions` + `_SubParsersAction.choices`, emits markdown deterministically, and `tests/contract/test_docs_contract.py` asserts the committed file matches the renderer's output. Same "no drift possible" guarantee as `mkdocs-click` would have given, with zero new build deps.

- **`--redact` default flip from `True` to `False` (PR #116, M5+M6 CLI surface)** — the existing `--redact` flag was vestigial: `measure export` hardcoded `redact=True` regardless of the flag, so the `default=True` carried no observable behavior. The new opt-in semantics for `--all-repos --redact` give the flag actual meaning. `measure export` is unchanged (still always redacts via the hardcoded call site). Verified by `test_measure_export_redact_default` continuing to pass.

- **`mike` deploy: `dev` vs `latest` separation (PR #119)** — the original pages.yml deployed every push to a version slot named `latest`. When the v1.0.0 tag fired `mike deploy --update-aliases 1.0.0 latest`, mike rejected it: `error: alias 'latest' already specified as a version` because aliases and versions share a namespace. **Decision**: reserve `latest` exclusively as an alias; main pushes deploy to a `dev` version slot instead. Idempotent `mike delete --push latest` step handles the one-time legacy cleanup.

- **Sigstore bundles vs. twine (PRs #119, #121)** — `sigstore/gh-action-sigstore-python` produces `*.sigstore.json` bundles in `dist/`; `pypa/gh-action-pypi-publish` invokes `twine check` on every file in `dist/` and rejects unknown extensions. Initial misdiagnosis: I assumed `attestations: true` on the publish action would consume the external bundles. Wrong — that flag mints **fresh** PEP 740 attestations via OIDC. **Fix**: move `*.sigstore.json` out of `dist/` before BOTH the TestPyPI and the PyPI publish steps. Bundles still exist in the workflow artifact for off-PyPI verification (`sigstore verify identity ...`).

- **`skip-existing: true` on both publish targets (PR #122)** — retag scenarios upload the same filename twice. TestPyPI rejects duplicate filenames; the failed-bundle-but-wheel-uploaded state on the first cycle made every retag fail with "400 File already exists". Fix is essentially mandatory for TestPyPI. Added to PyPI too for retag idempotency (PyPI still rejects overwrites unconditionally; the flag just keeps the action from erroring so the downstream `gh release edit` step still runs).

- **Synthetic-base test fixture: keep local, do NOT promote to `conftest.py` (PR #117)** — issue #109 left this open as a maintainer judgment call. Decision: keep `_build_three_workspace_tree` local to `tests/test_telemetry_rollup_integration.py`. `conftest.py` is currently scoped tightly to isolation concerns (Hypothesis storage, profile, env-var stripping); adding a workspace-fixture builder for a single consumer would expand its surface prematurely. When a second consumer materializes, the helper imports cleanly from the test module or can be lifted then.

- **Phase-1 + Phase-2 critic-and-ALT pattern is the right tool for high-stakes shippables** — used for issues #73, #74, #75. For each: spawn 3 critics (global-adoption, repo-conventions, failure-modes lens), synthesize consensus spec, implement, then spawn 5 parallel ALT implementations in worktrees and judge. Phase 1 won every time, but the ALTs surfaced real concerns (e.g., ALT 1 in PR #112 caught a `Path.home()` regression that's now scheduled for follow-up via remote agent on May 8 / fired ad hoc 2026-05-01). For smaller single-issue feature slices (PRD #104 chain: #107 / #108 / #109 / #110), pure TDD in a single session was sufficient — tests-first / red-green-refactor / lint / pytest / open PR. The Phase 1+2 fortress pattern is overkill for slices that touch <300 lines of production code.

- **Three retag cycles for v1.0.0 (release-engineering tax)** — pages.yml mike collision → publish.yml TestPyPI bundle issue → publish.yml PyPI bundle issue (same fix, missed PyPI step in the first patch) → TestPyPI duplicate filename. Each fix unblocked the next stage and exposed the next gotcha. v1.0.1 onward will be one-shot because the workflows now match the actual artifact shape. Captured in CHANGELOG `[Unreleased] / Fixed`.

**Next**: hold the v1.0 surface; address the remote-agent-fired #74 portability follow-up if it opens a PR; consider closing the Node.js 20 GitHub Actions deprecation gap by merging dependabot PRs #82 and #83.

## Session Checkpoints

### 2026-04-24 - visual refresh branch

- Branch: `feat/visual-refresh`
- Goal: redesign README image assets because the first visual pass felt crowded and some artwork/text sat too close to image borders.
- Design direction:
  - editorial control-room style
  - warm paper background
  - dark ink cards
  - fewer words per card
  - no transform-based edge positioning
  - direct coordinates with safe margins
- Updated assets:
  - `assets/brand/repo-context-hooks-logo.png`
  - `assets/brand/repo-context-hooks-logo.svg`
  - `assets/diagrams/context-continuity-engine.svg`
  - `assets/diagrams/lifecycle-flow.svg`
  - `assets/diagrams/repo-contract.svg`
  - `assets/diagrams/before-after-continuity.svg`
- Added visual safety tests:
  - visible rect/text/circle elements stay inside safe margins
  - visible paths, lines, and polylines stay inside the viewBox
  - diagrams avoid transform-based layout so future overflow is easier to catch

### 2026-04-24 - evidence monitoring branch

- Branch: `feat/evidence-monitoring`
- Goal: add `repo-context-hooks measure` so users can prove the effect of repo continuity instead of only reading product claims.
- Design boundary: telemetry is local-only, writes outside the repo by default, and reports operational readiness plus observed lifecycle events.
- Local proof after installing hooks:
  - Claude doctor: `ok`
  - repo contract: `ok`
  - ready platforms: Claude native, Codex partial, Kimi partial
  - measure score: `90`
  - estimated baseline: `20`
  - estimated uplift: `+70`
  - observed hook events: `32`
  - active days: `2`
  - lifecycle coverage: `100%`
  - resume events: `28`
  - checkpoint events: `2`
  - reload events: `2`
  - session-end events: `1`
- Current implementation slice:
  - `repo_context_hooks/telemetry.py`
  - `repo-context-hooks measure`
  - `repo-context-hooks measure --snapshot-dir docs/monitoring`
  - time-series usability metrics in `ImpactHistory` and `UsabilityMetrics`
  - local `monitoring.html` dashboard generated from the telemetry log
  - sanitized checked-in public snapshot at `docs/monitoring/index.html`
  - generated public history at `docs/monitoring/history.json`
  - README telemetry visibility section for Observable Plot, Vega-Lite, GitHub Pages, and local analysis workflows
  - PNG/SVG brand assets at `assets/brand/repo-context-hooks-logo.*`
  - checked-in visual brand asset at `assets/diagrams/context-continuity-engine.svg`
  - hook-script telemetry emission from `repo_specs_memory.py` and `session_context.py`
  - README and monitoring guide updates
  - `.claude/settings.json`
  - `.claude/scripts/repo_specs_memory.py`
  - `.claude/scripts/session_context.py`
  - `AGENTS.md`
- Claim boundary:
  - this is an impact evidence layer, not hosted analytics
  - this is an estimated before/after continuity audit, not a controlled productivity benchmark
  - remote telemetry requires explicit consent and is not implemented in the MVP

### 2026-04-24 - release v0.2.4

- Active branch:
  - `release/v0.2.4`
- Release goal:
  - ship merged evidence-monitoring work from PR #22 as `v0.2.4`
- What shipped:
  - local `repo-context-hooks measure`
  - local hook/skill JSONL events
  - automatic private `monitoring.html`
  - sanitized public dashboard export with `repo-context-hooks measure --snapshot-dir docs/monitoring`
  - checked-in public monitoring dashboard and `history.json`
  - consent-first remote telemetry policy
  - README telemetry visibility section
  - PNG/SVG brand assets
- Branch policy:
  - preserve `feat/evidence-monitoring`
  - preserve `release/v0.2.4`

### Current Checkpoint

- v0.3.0 shipped to PyPI on 2026-04-26.
- Branch: `feat/agent-level-skill-runtime` merged to `main` via PR #50.
- 174 tests passing. CI matrix green (ubuntu + windows, Python 3.9/3.11/3.12).
- Next phase: issues #43 (auto-detect platform), #42 (uninstall), #45 (first-run UX), #47 (GitHub Pages docs).
- Start next phase from fresh `main`.

### 2026-04-27 13:55 - pre-compact

- Branch: `feat/telemetry-reliability`
- Working changes: .claude/settings.json, docs/superpowers/specs/2026-04-17-repo-context-hooks-design.md, repo_context_hooks/platforms/runtime.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_readme_contract.py, tests/test_session_metrics.py, tests/test_telemetry_sampling_regression.py

### 2026-04-27 13:55 - pre-compact

- Branch: `feat/telemetry-reliability`
- Last commit: `chore: bump version to 0.5.0, update CHANGELOG`
- Working changes: .claude/settings.json, docs/superpowers/specs/2026-04-17-repo-context-hooks-design.md, repo_context_hooks/platforms/runtime.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_readme_contract.py, tests/test_session_metrics.py, tests/test_telemetry_sampling_regression.py

### 2026-04-27 13:58 - pre-compact

- Branch: `feat/telemetry-reliability`
- Working changes: .claude/settings.json, docs/superpowers/specs/2026-04-17-repo-context-hooks-design.md, repo_context_hooks/bundle/skills/context-handoff-hooks/scripts/repo_specs_memory.py, repo_context_hooks/doctor.py, repo_context_hooks/platforms/runtime.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_doctor.py, tests/test_readme_contract.py, tests/test_session_metrics.py

### 2026-04-27 13:58 - pre-compact

- Branch: `feat/telemetry-reliability`
- Last commit: `chore: bump version to 0.5.0, update CHANGELOG`
- Working changes: .claude/settings.json, docs/superpowers/specs/2026-04-17-repo-context-hooks-design.md, repo_context_hooks/bundle/skills/context-handoff-hooks/scripts/repo_specs_memory.py, repo_context_hooks/doctor.py, repo_context_hooks/platforms/runtime.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_doctor.py, tests/test_readme_contract.py, tests/test_session_metrics.py

### 2026-04-27 13:59 - pre-compact

- Branch: `feat/telemetry-reliability`
- Last commit: `chore: bump version to 0.5.0, update CHANGELOG`
- Working changes: .claude/settings.json, docs/superpowers/specs/2026-04-17-repo-context-hooks-design.md, repo_context_hooks/bundle/skills/context-handoff-hooks/scripts/repo_specs_memory.py, repo_context_hooks/doctor.py, repo_context_hooks/platforms/runtime.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_doctor.py, tests/test_readme_contract.py, tests/test_session_metrics.py

### 2026-04-27 13:59 - pre-compact

- Branch: `feat/telemetry-reliability`
- Working changes: .claude/settings.json, docs/superpowers/specs/2026-04-17-repo-context-hooks-design.md, specs/README.md, tests/test_readme_contract.py, tests/test_session_metrics.py, tests/test_telemetry_sampling_regression.py

### 2026-04-27 13:59 - pre-compact

- Branch: `feat/telemetry-reliability`
- Last commit: `feat(doctor): detect duplicate hook entries in settings.json â€” closes #62`
- Working changes: .claude/settings.json, docs/superpowers/specs/2026-04-17-repo-context-hooks-design.md, specs/README.md, tests/test_readme_contract.py, tests/test_session_metrics.py, tests/test_telemetry_sampling_regression.py

### 2026-04-27 14:00 - pre-compact

- Branch: `feat/telemetry-reliability`
- Last commit: `feat(doctor): detect duplicate hook entries in settings.json â€” closes #62`
- Working changes: .claude/settings.json, docs/superpowers/specs/2026-04-17-repo-context-hooks-design.md, specs/README.md, tests/test_readme_contract.py, tests/test_session_metrics.py, tests/test_telemetry_sampling_regression.py

### 2026-04-27 15:08 - session-end

- Branch: `main`
- Last commit: `feat: Telemetry Reliability & Analytics sprint â€” closes #57-#64`
- Working changes: specs/README.md

### 2026-04-27 15:21 - pre-compact

- Branch: `main`
- Last commit: `fix(tests): load alias modules from project root to avoid graphifyy conda conflict`
- Working changes: docs/monitoring/history.json, docs/monitoring/index.html, repo_context_hooks/cli.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_telemetry.py

### 2026-04-27 15:21 - pre-compact

- Branch: `main`
- Last commit: `fix(tests): load alias modules from project root to avoid graphifyy conda conflict`
- Working changes: docs/monitoring/history.json, docs/monitoring/index.html, repo_context_hooks/cli.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_monitoring_surface.py, tests/test_telemetry.py

### 2026-04-27 15:21 - pre-compact

- Branch: `main`
- Last commit: `fix(tests): load alias modules from project root to avoid graphifyy conda conflict`
- Working changes: docs/monitoring/history.json, docs/monitoring/index.html, repo_context_hooks/cli.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_monitoring_surface.py, tests/test_telemetry.py

### 2026-04-27 15:22 - pre-compact

- Branch: `main`
- Last commit: `fix(tests): load alias modules from project root to avoid graphifyy conda conflict`
- Working changes: docs/monitoring/history.json, docs/monitoring/index.html, repo_context_hooks/cli.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_monitoring_surface.py, tests/test_telemetry.py

### 2026-04-27 15:22 - pre-compact

- Branch: `main`
- Last commit: `fix(tests): load alias modules from project root to avoid graphifyy conda conflict`
- Working changes: docs/monitoring/history.json, docs/monitoring/index.html, repo_context_hooks/cli.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_monitoring_surface.py, tests/test_telemetry.py

### 2026-04-27 15:22 - pre-compact

- Branch: `main`
- Last commit: `fix(tests): load alias modules from project root to avoid graphifyy conda conflict`
- Working changes: docs/monitoring/history.json, docs/monitoring/index.html, repo_context_hooks/cli.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_monitoring_surface.py, tests/test_telemetry.py

### 2026-04-27 15:22 - pre-compact

- Branch: `main`
- Last commit: `fix(tests): load alias modules from project root to avoid graphifyy conda conflict`
- Working changes: README.md, docs/monitoring/history.json, docs/monitoring/index.html, repo_context_hooks/cli.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_monitoring_surface.py, tests/test_telemetry.py

### 2026-04-27 15:23 - pre-compact

- Branch: `main`
- Last commit: `fix(tests): load alias modules from project root to avoid graphifyy conda conflict`
- Working changes: README.md, docs/monitoring/history.json, docs/monitoring/index.html, repo_context_hooks/cli.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_monitoring_surface.py, tests/test_telemetry.py

### 2026-04-27 15:23 - pre-compact

- Branch: `main`
- Last commit: `fix(tests): load alias modules from project root to avoid graphifyy conda conflict`
- Working changes: README.md, docs/monitoring/history.json, docs/monitoring/index.html, repo_context_hooks/cli.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_monitoring_surface.py, tests/test_telemetry.py

### 2026-04-27 15:23 - pre-compact

- Branch: `main`
- Last commit: `fix(tests): load alias modules from project root to avoid graphifyy conda conflict`
- Working changes: README.md, docs/monitoring/history.json, docs/monitoring/index.html, repo_context_hooks/cli.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_monitoring_surface.py, tests/test_telemetry.py

### 2026-04-27 15:23 - pre-compact

- Branch: `main`
- Last commit: `fix(tests): load alias modules from project root to avoid graphifyy conda conflict`
- Working changes: README.md, docs/monitoring/history.json, docs/monitoring/index.html, repo_context_hooks/cli.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_monitoring_surface.py, tests/test_telemetry.py

### 2026-04-27 15:23 - pre-compact

- Branch: `main`
- Last commit: `fix(tests): load alias modules from project root to avoid graphifyy conda conflict`
- Working changes: README.md, docs/monitoring/history.json, docs/monitoring/index.html, repo_context_hooks/cli.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_monitoring_surface.py, tests/test_telemetry.py

### 2026-04-27 15:24 - pre-compact

- Branch: `main`
- Last commit: `fix(tests): load alias modules from project root to avoid graphifyy conda conflict`
- Working changes: README.md, docs/monitoring/history.json, docs/monitoring/index.html, repo_context_hooks/cli.py, repo_context_hooks/telemetry.py, specs/README.md, tests/test_monitoring_surface.py, tests/test_telemetry.py

### 2026-04-27 15:24 - pre-compact

- Branch: `main`
- Last commit: `feat(dashboard): rich browser dashboard with tokens/cost/lifecycle/branches/forecast`
- Working changes: specs/README.md

### 2026-04-27 21:36 - session-end

- Branch: `main`
- Last commit: `chore: update monitoring snapshot`
- Working changes: repo_context_hooks/bundle/skills/context-handoff-hooks/SKILL.md, repo_context_hooks/bundle/skills/context-handoff-hooks/scripts/repo_specs_memory.py, repo_context_hooks/cli.py, specs/README.md, tests/test_cli.py, tests/test_repo_memory_contract.py, docs/superpowers/plans/2026-04-27-sampling-fix-roi-metrics.md

### 2026-04-27 22:46 - session-end

- Branch: `feat/issues-23-24-26`
- Last commit: `feat: add measure export, measure experiment, and telemetry consent layer (closes #24, #23, #26)`
- Working changes: README.md, repo_context_hooks/bundle/skills/context-handoff-hooks/SKILL.md, repo_context_hooks/bundle/skills/context-handoff-hooks/scripts/repo_specs_memory.py, specs/README.md, tests/test_cli.py, tests/test_repo_memory_contract.py, .claude/worktrees/, docs/superpowers/plans/2026-04-27-sampling-fix-roi-metrics.md

### 2026-04-28 17:39 - session-end

- Branch: `claude/add-dependabot-config-f1xAw`
- Working changes: none
