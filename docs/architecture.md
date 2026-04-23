# Architecture

`repo-context-hooks` is a repo-native continuity layer for coding agents.

## Core Model

The repository is the memory boundary. Instead of treating continuity as hidden session state, the project stores the useful parts of the work where the next session can inspect them:

- `README.md` carries the public product story
- `specs/README.md` carries engineering memory, active constraints, and next-step context
- platform-root files such as `replit.md` carry platform-specific continuity guidance when the agent reads from the repo root
- repo rule directories such as `.windsurf/rules` carry platform-specific continuity guidance when the platform uses a rules engine
- repo-owned knowledge exports such as `.lovable/project-knowledge.md` and `.lovable/workspace-knowledge.md` carry platform-specific continuity guidance for hosted knowledge UIs
- workspace-loaded Markdown files such as `SOUL.md`, `USER.md`, and `TOOLS.md` carry platform-specific continuity guidance when the platform uses a configured workspace as its context boundary
- local-model templates such as `Modelfile.repo-context` carry the repo contract into model runtimes that do not read files by themselves
- platform-specific automation helps move that state forward between sessions

## Current Continuity Surfaces

Current support is intentionally built around eight platforms: Claude, Cursor, Codex, Replit, Windsurf, Lovable, OpenClaw, and Ollama.

Claude is the strongest path because it exposes lifecycle primitives that can automate more of the continuity loop. Cursor and Codex matter for a different reason: they prove that platform adapters expose different continuity surfaces while still relying on the same checked-in repo contract. Replit matters for the same repo-contract story, but through `replit.md` instead of native lifecycle hooks. Windsurf matters because it consumes root `AGENTS.md` and `.windsurf/rules` through the same rules engine that powers Cascade customizations. Lovable matters because it combines repo-visible `AGENTS.md` with repo-owned exports that feed Project Knowledge and Workspace Knowledge in the hosted UI. OpenClaw matters because its agent runtime can load repo-root workspace files such as `SOUL.md`, `USER.md`, `TOOLS.md`, and `AGENTS.md`, while still requiring manual workspace configuration. Ollama matters because local model users can create a repo-context model from `Modelfile.repo-context`, while still needing an agent wrapper or pasted context for actual repo access.

That distinction is important. The architecture is not trying to flatten every platform into the same hook model. It is trying to preserve a stable repo-native contract while the surrounding automation changes.

## Interrupt And Resume Flow

The continuity loop follows a practical task story:

1. an agent starts work from checked-in repo context
2. the session is interrupted by compact, handoff, or context loss
3. useful tactical state is written back into `specs/README.md` or a platform-root file such as `replit.md`
4. the next session resumes from repo state instead of replaying the entire task from memory

## Why The Repo Contract Matters

A continuity system is only trustworthy if teammates can inspect it. By keeping the continuity contract in git, teams can review what the agent is carrying forward, refine what belongs in public docs versus engineering memory, and recover from bad assumptions without depending on opaque memory infrastructure.
