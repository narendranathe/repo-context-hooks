# Kimi Code Adapter Design

Date: 2026-04-22
Status: Proposed
Author: Narendranath Edara

## Summary

This spec defines a deliberately narrow Kimi integration for `repo-context-hooks`: add `partial` support for Kimi Code CLI workflows through root `AGENTS.md`.

Kimi has multiple meanings:

- Moonshot/Kimi API model access
- Kimi models used inside other coding tools
- Kimi Code CLI as a coding agent workflow

`repo-context-hooks` should only claim support for the Kimi Code CLI workflow where `AGENTS.md` is a documented/reported project-context artifact. It should not claim generic Kimi API, model-provider, or hosted IDE support.

## Verified Platform Surface

The official Kimi resource article about using Kimi Code CLI in a production refactor says the team used `/init` to generate an `AGENTS.md` file, then refined it with project scope, constraints, structure, and build process details.

That is a credible repo-facing continuity surface, but it is narrow. The public docs do not provide a stable Kimi-specific rules directory or lifecycle hook equivalent that this project should automate.

## Problem

The roadmap currently treats Kimi as planned-only. That underclaims a useful minimal integration if Kimi Code CLI consumes `AGENTS.md`, but overclaiming broad Kimi support would be misleading.

## Goals

- Add `KimiAdapter` as `partial` support.
- Install root `AGENTS.md`.
- Print manual steps telling users to run/review Kimi Code `/init` and merge any generated guidance with the repo contract.
- Warn that this is Kimi Code CLI guidance, not generic Kimi API or lifecycle-hook support.
- Update docs and roadmap honestly.

## Non-Goals

- Do not claim generic Kimi API support.
- Do not claim Kimi Code lifecycle hooks.
- Do not invent a `.kimi/` rules directory.
- Do not claim compact checkpoint automation.
- Do not run Kimi Code CLI.

## Chosen Approach

Tier: `partial`

Install shape:

- `AGENTS.md`

Behavior:

- reuse the shared repo `AGENTS.md` contract
- keep the support surface intentionally smaller than Windsurf, OpenClaw, or Ollama
- warn that Kimi Code users should merge any `/init` output with the repo contract rather than overwrite it

## Architecture Impact

Add:

- `repo_context_hooks/platforms/kimi.py`

Update:

- `repo_context_hooks/platforms/__init__.py`
- platform registry, install-plan, artifact, doctor, CLI, README, and docs contract tests
- public docs and roadmap files

## Validation Strategy

`doctor` should validate:

- `AGENTS.md`

Existing `AGENTS.md` marker validation already checks:

- `README.md`
- `specs/README.md`
- `repo as the continuity source of truth`

No new doctor marker branch is required.

## Self-Critique Pass 1

This is the thinnest adapter in the project. That is acceptable only because it is explicit. If we tried to add Kimi-specific rule files without official stable paths, we would be inventing integration surface.

## Self-Critique Pass 2

The Kimi API and Kimi Code CLI should not be conflated. The API is a model-provider surface. The CLI is an agent workflow. This adapter is for Kimi Code CLI project-context setup only.

## Success Criteria

This phase is successful if:

- `repo-context-hooks install --platform kimi` writes or preserves `AGENTS.md`
- `repo-context-hooks doctor --platform kimi` validates `AGENTS.md`
- public docs describe Kimi as narrow `partial` support
- docs explicitly say the generic Kimi API is not being configured
- tests protect that boundary
