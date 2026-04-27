# Architecture

`repo-context-hooks` is an agent-level continuity skill. It runs at the agent runtime level - installed once to agent home - and uses the repository workspace contract as its durable persistence layer.

## Core Model

The agent runtime is the primary boundary. The repository is the persistence medium. Instead of treating continuity as hidden session state or a per-repo hook, the skill installs once and operates across every workspace the agent opens:

- `README.md` carries the public product story
- `specs/README.md` carries engineering memory, active constraints, and next-step context
- platform-root files such as `replit.md` carry platform-specific continuity guidance when the agent reads from the repo root
- repo rule directories such as `.windsurf/rules` carry platform-specific continuity guidance when the platform uses a rules engine
- repo-owned knowledge exports such as `.lovable/project-knowledge.md` and `.lovable/workspace-knowledge.md` carry platform-specific continuity guidance for hosted knowledge UIs
- workspace-loaded Markdown files such as `SOUL.md`, `USER.md`, and `TOOLS.md` carry platform-specific continuity guidance when the platform uses a configured workspace as its context boundary
- local-model templates such as `Modelfile.repo-context` carry the repo contract into model runtimes that do not read files by themselves
- shared agent instruction files such as `AGENTS.md` carry the repo contract into Kimi Code CLI workflows without inventing a Kimi-specific rules directory
- platform-specific automation helps move that state forward between sessions

That is also the onboarding model:

1. install the skill to agent home: `repo-context-hooks install --platform claude`
2. optionally scaffold the workspace contract: `repo-context-hooks init`
3. verify: `repo-context-hooks doctor`

Agent skill install comes first. Workspace contract setup is optional scaffolding for workspaces that do not already have `specs/README.md`.

## Current Continuity Surfaces

Current support is intentionally built around nine platforms: Claude, Cursor, Codex, Replit, Windsurf, Lovable, OpenClaw, Ollama, and Kimi.

Claude is the strongest path because it exposes lifecycle primitives that can automate more of the continuity loop. Cursor and Codex matter for a different reason: they prove that platform adapters expose different continuity surfaces while still relying on the same checked-in repo contract. Replit matters for the same repo-contract story, but through `replit.md` instead of native lifecycle hooks. Windsurf matters because it consumes root `AGENTS.md` and `.windsurf/rules` through the same rules engine that powers Cascade customizations. Lovable matters because it combines repo-visible `AGENTS.md` with repo-owned exports that feed Project Knowledge and Workspace Knowledge in the hosted UI. OpenClaw matters because its agent runtime can load repo-root workspace files such as `SOUL.md`, `USER.md`, `TOOLS.md`, and `AGENTS.md`, while still requiring manual workspace configuration. Ollama matters because local model users can create a repo-context model from `Modelfile.repo-context`, while still needing an agent wrapper or pasted context for actual repo access. Kimi matters because Kimi Code CLI workflows can use root `AGENTS.md` for project context, while generic Kimi API usage remains out of scope.

That distinction is important. The architecture is not trying to flatten every platform into the same hook model. It is trying to preserve a stable repo-native contract while the surrounding automation changes.

## Interrupt And Resume Flow

The continuity loop is agent-driven:

1. agent skill activates at `SessionStart` and reads workspace contract from the repo
2. session is interrupted by compact, handoff, or context loss
3. `PreCompact` hook writes useful tactical state back into `specs/README.md`
4. next session's `SessionStart` reloads from repo state - not from fragile session memory
5. `SessionEnd` writes a final handoff summary for the next agent session

## Why The Repo Contract Matters

A continuity system is only trustworthy if teammates can inspect it. By keeping state in git-tracked workspace files, teams can review what the agent is carrying forward, refine what belongs in public docs versus engineering memory, and recover from bad assumptions without depending on opaque external memory infrastructure.
