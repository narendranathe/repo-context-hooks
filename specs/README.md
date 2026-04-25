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

- Repo-native continuity for coding agents. `repo-context-hooks` keeps interrupted work, next-step context, and handoff notes in the repository instead of leaving them trapped in chat history. The goal is simple: a new session should be able to reopen the repo, understand the work in progress, and continue without rediscovering everything from scratch.
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
- Current active branch adds the next layer:
  - `doctor --all-platforms`
  - `recommend`
- Current monitoring branch adds local impact evidence:
  - `measure`
  - `measure --snapshot-dir docs/monitoring`
  - local JSONL hook/skill events
  - estimated current-vs-baseline continuity uplift
  - committed Claude repo hooks so the evidence loop is automatic for this repo
  - documented consent-first remote telemetry as a future product path, not part of the MVP

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

- `main` currently includes:
  - platform foundation
  - platform polish
  - canonical repo memory contract
  - repo-first onboarding
  - release `v0.2.1`
- Active feature branch:
  - `feat/platform-readiness`
- Active PR:
  - adds `doctor --all-platforms`
  - adds `recommend`
  - updates docs to explain readiness vs recommendations
- Active follow-up issue:
  - Windows editable launcher behavior discovered during verification and tracked separately from feature logic
- Expected path from here:
  - update memory
  - merge readiness PR
  - cut next release
  - start the next product phase from fresh `origin/main`

## Open Issues and Next Work

- Keep the repo memory contract canonical and low-noise so future worktrees stop accumulating untracked bootstrap files.
- Continue raising platform quality through real support surfaces, not expanded marketing copy.
- Improve launch assets and public examples only when they stay faithful to the implementation boundary.
- Merge the platform-readiness branch after final review.
- Cut the next release so readiness and recommendation commands become part of the published package.
- Resolve the Windows editable-launcher issue separately, because it affects verification confidence on Windows even though feature logic is passing.
- Start the next product phase from fresh `main` rather than stacking more work on an aging branch.

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

- This file captures the project history through the platform-readiness phase and the public README/JSON-output release.
- Active branch:
  - `release/v0.2.4`
- Release completed:
  - `v0.2.4`
- What shipped:
  - continuity impact monitoring and local evidence loop
  - public monitoring snapshot export
  - telemetry policy and README visualization guidance
  - README brand mark and telemetry visibility facelift
- Verification completed:
  - full suite passing locally
  - release package version bumped to `0.2.4`
- Branch policy:
  - merged branches are preserved for future review and revert workflows

### 2026-04-24 11:16 - post-compact

- Branch: `feat/evidence-monitoring`
- Working changes: repo_context_hooks/telemetry.py, tests/test_readme_contract.py, tests/test_telemetry.py, tests/test_visual_contract.py, tests/test_monitoring_surface.py

### 2026-04-24 11:16 - session-end

- Branch: `feat/evidence-monitoring`
- Working changes: repo_context_hooks/telemetry.py, tests/test_readme_contract.py, tests/test_telemetry.py, tests/test_visual_contract.py, tests/test_monitoring_surface.py

### 2026-04-24 11:16 - session-end

- Branch: `feat/evidence-monitoring`
- Working changes: repo_context_hooks/telemetry.py, specs/README.md, tests/test_readme_contract.py, tests/test_telemetry.py, tests/test_visual_contract.py, tests/test_monitoring_surface.py

### 2026-04-24 - observability proof strip branch

- Branch: `feat/observability-proof-strip`
- Goal: make telemetry visible on the GitHub landing page and add a credible monitoring-tool path for developers.
- Product decision:
  - implement Prometheus/OpenMetrics text export as the real integration surface
  - document Grafana as the strongest dashboard showcase path
  - document Datadog through OpenMetrics-compatible collection, not native API publishing
  - keep remote telemetry out of the MVP unless explicit opt-in consent and policy-backed collection are implemented later
- Implementation slice:
  - `repo-context-hooks measure --prometheus`
  - aggregate-only Prometheus metrics without local paths, prompts, code, compact summaries, or resume content
  - README `Live Evidence Snapshot` section with a generated graph from public telemetry history
  - `docs/monitoring/timeseries.svg` generated from `docs/monitoring/history.json`
  - `docs/observability.md`
  - monitoring guide links from README and `docs/monitoring.md`
- Correction after critique:
  - removed the hand-authored telemetry proof strip because it was a claim card, not proof
  - wired the public snapshot writer to generate the README graph from telemetry data
  - the HTML dashboard remains useful, but the README now embeds actual generated time-series evidence directly
- Follow-up correction after SVG readability critique:
  - redesigned `docs/monitoring/timeseries.svg` to avoid spilling content
  - added a model/session-only baseline versus repo-continuity comparison
  - added previous-vs-latest telemetry day labels
  - added metric-source copy inside the SVG so readers can see which snapshot fields derive the graph
  - added visual contract coverage for the README telemetry graph
- Agent/model comparison follow-up:
  - telemetry events now carry `agent_platform` and optional `model_name`
  - event sources infer platform where possible, with explicit environment overrides available
  - public snapshots now include `agent_comparison`
  - Prometheus output now includes agent/model event and latest-score metrics
  - README SVG now renders an agent/model comparison panel from the public snapshot
- Claim boundary:
  - the project now has a real local observability export
  - Grafana and Datadog are documented integration paths over OpenMetrics
  - there is still no hosted telemetry service, no cookies, and no remote community analytics in the MVP
