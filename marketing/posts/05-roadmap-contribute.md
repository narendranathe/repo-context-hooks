# Post 5: Roadmap + How to Contribute

**Posting slot:** Thu 2026-05-28, 9-10 AM CT
**Theme:** What's shipped, what's next, how to contribute, what feedback is most useful.
**CTA:** Open an issue / discussion. Recruit 5 contributors.

---

## Substack draft

### Title

The road to `repo-context-hooks` 1.1 — and the 3 things I want your help on

### Body

Wrapping the launch series with where the project stands, what's coming, and the specific places I would love community contribution.

### What's already shipped (v1.0.0)

The v1.0 release in early May was a 10-vertical-slice production-readiness push. Specifically:

- **Community health** — `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, issue + PR templates.
- **Supply chain** — Sigstore signing, Dependabot, SHA-pinned actions, CodeQL workflow, OIDC trusted publishing.
- **Coverage gate** — 85% line coverage via Hypothesis property tests on the critical paths.
- **Stability contract** — explicit `__all__`, `tests/contract/public_surface.json` snapshot, public-surface CI gate.
- **Self-observability** — `repo_context_hooks.logging_setup` module, global `--debug`, `doctor` last-error surface.
- **Install/uninstall UX** — `verify` command, `--dry-run` on install/uninstall.
- **Docs depth** — troubleshooting, mkdocs-click CLI reference, `mike` versioned docs, copy-paste quickstart.
- **Release engineering** — changelog gate, auto-populated GH Release notes, richer `--version`.
- **Governance** — `NOTICE`, zero-deps callout, maintainer-status section.
- **Cross-workspace rollup** — `measure --all-repos` walks every workspace under the telemetry base and prints fleet-level numbers.

Versioned docs site: https://narendranathe.github.io/repo-context-hooks/latest/

### What's next (v1.1 and beyond)

Live issues, ordered by my current priority:

- **#124 / PR #125** — Bug: AUTO:REPO_CONTEXT block clobber on every SessionStart. Confirmed root cause in `extract_repo_summary`. Merge candidate this week.
- **#126** — Auto decision-capture at Stop / PreCompact. The current `checkpoint --message` flow is manual — adopters skip it, semantic decisions never persist. Working on a hook-injected prompt that nudges the agent to call `checkpoint` at the right moments.
- **#75** — Docs depth round 2: more troubleshooting recipes, an asciinema demo, more `mike` aliases.
- **#23** — Guided before/after experiment flow improvements. The `measure experiment` command works; it can be made more conversational.
- **#26** — Team rollup server. Today `measure --all-repos` is single-machine. v1.1 will optionally accept a consented remote endpoint for team-level fleet rollup. Hard non-goal: a hosted dashboard. The endpoint stays open spec, run-it-yourself.

### Where I want community help

Three concrete asks. All have open issues you can pick up.

**1. Field-test the partial-tier adapters.** Claude is `native`. Cursor, Codex, Replit, Windsurf, Lovable, OpenClaw, Ollama, and Kimi are `partial`. The `partial` tier scaffolds the right repo surface but does not wire lifecycle hooks because those platforms don't expose them yet. If you primarily use one of those agents, file issues with concrete examples of what "lifecycle parity" would look like for it. Issue label: `platform-parity`.

**2. Better default workspace contract templates.** `specs/README.md` and `UBIQUITOUS_LANGUAGE.md` get scaffolded with sensible defaults, but every team has a different shape. PRs welcome with alternative templates for: data eng (dbt / Airflow / Spark stacks), ML training loops, Chrome extensions, Rust crates. Issue label: `template-pack`.

**3. Honest before/after data.** Run `measure experiment start | finish` for a week and post the JSON output (the redacted form is safe to share). I want to validate the `cold_start_time_saved_minutes` heuristic against real adoption. If the 5-minute constant is wrong, I want to know.

### Ideas on making it better

Open the discussions tab: https://github.com/narendranathe/repo-context-hooks/discussions

Topics I would love thoughts on:

- Should `checkpoint --message` be auto-triggered? If yes, what's the right hook signal?
- Is the `docs/badge.svg` worth the build cost, or does no one look at it?
- Would you pay for a hosted team-rollup endpoint, or is self-hosted the only acceptable model?
- What other agents should get a `partial` adapter? Aider? Continue.dev? Roo Code?

### How to contribute

`CONTRIBUTING.md` covers the basics. Quick orientation:

- Stack: Python 3.9-3.13, zero runtime dependencies, `pyproject.toml`, Hypothesis property tests.
- 85% coverage gate, stability contract via `tests/contract/public_surface.json`.
- Every PR adds a CHANGELOG entry under `[Unreleased]`.
- I respond to issues and PRs within 48 hours on weekdays (best-effort; this is a single-maintainer project).

If you've made it through all 5 posts in this series, you understand the product better than most contributors will when they first land. **Star the repo, open one issue, and tell me one thing you'd change.** That's the highest-signal contribution.

Repo: https://github.com/narendranathe/repo-context-hooks
Docs: https://narendranathe.github.io/repo-context-hooks/latest/
Discussions: https://github.com/narendranathe/repo-context-hooks/discussions
PyPI: https://pypi.org/project/repo-context-hooks/

Thanks for reading the series. Next post will probably be a deep dive on the v1.1 hook auto-trigger design — drop a comment if there's a specific angle you want covered.

---

## LinkedIn draft

Closing out the 5-post `repo-context-hooks` launch series.

What's shipped in v1.0:
- 10-slice production-readiness push (community health, supply chain, stability contract, self-observability, install UX, docs depth, release engineering, governance, cross-workspace rollup)
- 85% test coverage gate via Hypothesis property tests
- OIDC trusted publishing + Sigstore attestations
- 9 platform adapters (Claude native, 8 partial)
- Versioned docs site at narendranathe.github.io/repo-context-hooks/latest

What I'm working on next:
- Auto decision-capture (#126) so `checkpoint --message` fires from a hook instead of being manual
- AUTO:REPO_CONTEXT clobber bug (PR #125, merge candidate this week)
- Team rollup endpoint (#26) — single-machine `measure --all-repos` is shipped; v1.1 adds optional consented endpoint

Three concrete asks for the community:

1. **Field-test the partial-tier adapters** (Cursor, Codex, Replit, Windsurf, Lovable, OpenClaw, Ollama, Kimi). If you use one of these primarily, open an issue with what "lifecycle parity" would look like. Label: `platform-parity`.

2. **Contribute workspace contract templates** for your stack (data eng, ML training, Chrome MV3, Rust crates). Label: `template-pack`.

3. **Share honest before/after data** from a week of running the hooks. I want to validate the `cold_start_time_saved_minutes` heuristic against real adoption.

If you've followed the whole series, you know the product better than most first-time contributors. The single highest-signal thing you can do: **star the repo, open one issue, tell me one thing you'd change.**

Repo: https://github.com/narendranathe/repo-context-hooks
Docs: https://narendranathe.github.io/repo-context-hooks/latest/
Discussions: https://github.com/narendranathe/repo-context-hooks/discussions

What would you build on top of a deterministic, repo-tracked workspace contract? Curious where the community wants this to go.

#ClaudeCode #OpenSource #DeveloperTools #AIAgents #BuildInPublic #PythonDev #LLMOps #ContextEngineering #AIEngineering
