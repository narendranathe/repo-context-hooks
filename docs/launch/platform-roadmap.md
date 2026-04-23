# Planned Platform Roadmap

This document is the public backlog seed for future GitHub issues. Most platforms below are intentionally marked as planned, not shipped, but Replit has already graduated to current partial support via `replit.md`, Windsurf has already graduated to current partial support via root `AGENTS.md` and `.windsurf/rules`, Lovable has already graduated to current partial support via repo-owned Project Knowledge and Workspace Knowledge exports, and OpenClaw has graduated to current partial support via repo-root workspace files.

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
- Goal: support local-model workflows that still benefit from checked-in instructions, specs memory, and restart-from-repo handoffs.
- Tier: provisional until the platform continuity surface is verified.
- Open question: what installer or template shape is realistic for local runtime setups without overcommitting on automation?
- Issue-ready acceptance criteria:
  - define whether this should be an adapter, template pack, or docs-only workflow
  - decide the honest support tier after install/runtime surfaces are verified
  - define what continuity can be automated and what remains manual
  - define unsupported claims explicitly

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
- Goal: evaluate whether repo-native continuity can map onto its coding workflow in a way that is honest and useful.
- Tier: provisional until the platform continuity surface is verified.
- Open question: what instruction, tool, or session surfaces are available for carrying forward checked-in task state?
- Issue-ready acceptance criteria:
  - identify what coding-workflow continuity surfaces Kimi actually exposes
  - decide the honest support tier after those surfaces are verified
  - define what could be automated and what remains manual
  - define which claims must stay out of the README

## Issue-Creation Rule

When these become GitHub issues, each issue should answer three things before implementation starts:

- what continuity surface the platform actually exposes
- which support tier is honest for that surface
- what user-facing claim must stay out of the README until the work is real

Replit is the exception because the exposed surface is already documented well enough to support a current `partial` claim. For Replit, the issue thread should be treated as follow-up work, not proof-of-concept discovery.
