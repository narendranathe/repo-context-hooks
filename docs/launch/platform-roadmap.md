# Planned Platform Roadmap

This document is the public backlog seed for future GitHub issues. Most platforms below are intentionally marked as planned, not shipped, but Replit has already graduated to current partial support via `replit.md`, Windsurf has already graduated to current partial support via root `AGENTS.md` and `.windsurf/rules`, Lovable has already graduated to current partial support via repo-owned Project Knowledge and Workspace Knowledge exports, OpenClaw has graduated to current partial support via repo-root workspace files, Ollama has graduated to current partial support via a repo-owned Modelfile template, and Kimi has graduated to current partial support via root `AGENTS.md` for Kimi Code CLI workflows.

## Replit

- Issue: [#2](https://github.com/narendranathe/repo-context-hooks/issues/2)
- Status: current `partial` support via `replit.md` and the repo contract.
- Goal: translate the repo contract into a workspace-agent flow that can reopen a project with useful next-step context.
- Support boundary:
  - no native lifecycle hooks here.
  - Replit does not automate compact checkpoint and restore flows here.
  - `replit.md` points the agent back to the repo contract instead of pretending to be Claude-style parity.
- Follow-up use for issue #2: track incremental improvements to the current partial support, not first-time discovery.

## Windsurf

- Issue: [#8](https://github.com/narendranathe/repo-context-hooks/issues/8)
- Status: current `partial` support via root `AGENTS.md`, `.windsurf/rules`, and the repo contract.
- Goal: translate the repo contract into a rules-driven Cascade workflow that can reopen a project with useful next-step context.
- Support boundary:
  - no native lifecycle hooks here.
  - Windsurf does not automate compact checkpoint and restore flows here.
  - root `AGENTS.md` and `.windsurf/rules` point Cascade back to the repo contract instead of pretending to be Claude-style parity.
- Follow-up use for issue #8: improve the quality of the Windsurf rule templates and any future docs around Windsurf-specific rule composition.

## Lovable

- Issue: [#3](https://github.com/narendranathe/repo-context-hooks/issues/3)
- Status: current `partial` support via repo-owned Project Knowledge and Workspace Knowledge exports plus the repo contract.
- Goal: export the repo contract into a GitHub-synced builder workflow without losing reviewable source-of-truth docs.
- Support boundary:
  - no native lifecycle hooks here.
  - Lovable does not automate compact checkpoint and restore flows here.
  - `.lovable/project-knowledge.md` and `.lovable/workspace-knowledge.md` are canonical repo-owned exports, but the user still has to paste them into Project Knowledge and Workspace Knowledge in the Lovable UI.
  - local `doctor` checks cannot verify whether Lovable's hosted project knowledge matches the repo export.
- Follow-up use for issue #3: track incremental improvements to the current hybrid support, not first-time discovery.

## Ollama

- Issue: [#4](https://github.com/narendranathe/repo-context-hooks/issues/4)
- Status: current `partial` support via `AGENTS.md`, `Modelfile.repo-context`, and manual local-model creation.
- Goal: support local-model workflows that still benefit from checked-in instructions and specs memory without pretending Ollama is a repo-aware agent runtime.
- Support boundary:
  - no native lifecycle hooks here.
  - Ollama does not read repo files automatically.
  - `Modelfile.repo-context` gives a local model a repo-continuity system prompt, but an agent wrapper or pasted context must provide file contents.
- Follow-up use for issue #4: track incremental improvements to the current local-model-template support, not first-time discovery.

## OpenClaw

- Issue: [#5](https://github.com/narendranathe/repo-context-hooks/issues/5)
- Status: current `partial` support via repo-root `AGENTS.md`, `SOUL.md`, `USER.md`, `TOOLS.md`, and manual workspace activation.
- Goal: translate the repo contract into OpenClaw's workspace-file model without treating it as a hook-native platform.
- Support boundary:
  - no native lifecycle hooks here.
  - OpenClaw does not automate compact checkpoint and restore flows here.
  - local `doctor` checks validate generated repo files, not the active OpenClaw workspace path.
- Follow-up use for issue #5: track incremental improvements to the current workspace-file support, not first-time discovery.

## Kimi

- Issue: [#6](https://github.com/narendranathe/repo-context-hooks/issues/6)
- Status: current `partial` support via root `AGENTS.md` and Kimi Code CLI `/init` merge guidance.
- Goal: support Kimi Code CLI project-context workflows without conflating them with generic Kimi API model access.
- Support boundary:
  - no native lifecycle hooks here.
  - no generic Kimi API configuration here.
  - no Kimi-specific rules directory is created until a stable documented path exists.
- Follow-up use for issue #6: track incremental improvements to the current `AGENTS.md`-only support, not first-time discovery.

## Issue-Creation Rule

When these become GitHub issues, each issue should answer three things before implementation starts:

- what continuity surface the platform actually exposes
- which support tier is honest for that surface
- what user-facing claim must stay out of the README until the work is real

Replit is the exception because the exposed surface is already documented well enough to support a current `partial` claim. For Replit, the issue thread should be treated as follow-up work, not proof-of-concept discovery.
