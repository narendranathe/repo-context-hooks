# Planned Platform Roadmap

This document is the public backlog seed for future GitHub issues. Every platform below is intentionally marked as planned, not shipped.

## Replit

- Goal: translate the repo contract into a workspace agent flow that can reopen a project with useful next-step context.
- Tier: provisional until the platform continuity surface is verified.
- Open question: which workspace surfaces can host checked-in continuity guidance without inventing fake hook parity?
- Issue-ready acceptance criteria:
  - identify the actual continuity surface Replit exposes
  - decide whether `partial` support is honest
  - define which install or template steps can be automated
  - define which claims must stay out of the README

## Lovable

- Goal: export the repo contract into a GitHub-synced builder workflow without losing reviewable source-of-truth docs.
- Tier: provisional until the platform continuity surface is verified.
- Open question: how much continuity can stay repo-native when most orchestration happens in a hosted product surface?
- Issue-ready acceptance criteria:
  - identify which repo files Lovable can reliably consume
  - decide whether an adapter is honest or whether docs-only guidance is better
  - define the minimum useful continuity workflow
  - define which claims must stay out of the README

## Ollama

- Goal: support local-model workflows that still benefit from checked-in instructions, specs memory, and restart-from-repo handoffs.
- Tier: provisional until the platform continuity surface is verified.
- Open question: what installer or template shape is realistic for local runtime setups without overcommitting on automation?
- Issue-ready acceptance criteria:
  - define whether this should be an adapter, template pack, or docs-only workflow
  - decide the honest support tier after install/runtime surfaces are verified
  - define what continuity can be automated and what remains manual
  - define unsupported claims explicitly

## OpenClaw

- Goal: investigate whether its orchestration model can consume the same continuity contract used by Claude, Cursor, and Codex.
- Tier: provisional until the platform continuity surface is verified.
- Open question: what platform adapter boundary is needed before this becomes more than a naming exercise?
- Issue-ready acceptance criteria:
  - identify the actual instruction and continuity surfaces OpenClaw exposes
  - decide whether an adapter is honest or whether discovery should continue
  - define what minimum useful integration would look like
  - define which README claims must stay out-of-bounds

## Kimi

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
