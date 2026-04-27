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

- `main` currently includes all shipped work through `v0.3.0`:
  - platform foundation and polish
  - canonical repo memory contract and repo-first onboarding
  - continuity impact monitoring and local evidence loop
  - agent-level skill runtime, session metrics, CI/CD matrix
- Latest release: `v0.3.0` — live on PyPI (`pip install repo-context-hooks`)
- PR #50 merged: agent-level skill runtime feature
- CI: 174 tests, 6 matrix jobs (ubuntu + windows, Python 3.9/3.11/3.12) — all green
- Next phase starts from fresh `main`

## Open Issues and Next Work

Priority backlog for the next phase:

- **#43** - Auto-detect platform (`--platform` flag should be optional): biggest DX win
- **#42** - `uninstall` command: developers need a clean exit
- **#45** - First-run "what just happened" output: reduces churn on first install
- **#47** - GitHub Pages docs site: needed before any public launch

Ongoing:
- Keep the repo memory contract canonical and low-noise.
- Continue raising platform quality through real support surfaces, not expanded marketing copy.

## How To Work in This Repo

- Read `README.md` first for user-facing behavior and contribution flow.
- Read this `specs/README.md` before implementation.
- Read `UBIQUITOUS_LANGUAGE.md` before renaming core concepts or adding new public terms.
- Keep support claims narrow unless docs, tests, and install behavior all support widening them.
- Update this file before `compact` and at session end.
- Preserve merged feature and release branches unless the user explicitly asks to delete them.

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
