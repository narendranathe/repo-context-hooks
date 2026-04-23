# Repo Context Hooks: Turning Repo Context Into Infrastructure

I have been spending a lot of time with coding agents recently, and one failure mode kept repeating:

the more real the project became, the more fragile the agent's working context felt.

Claude Code made that especially obvious for me. It is easy to say "the model forgot," but that framing is incomplete. In real work, the bigger issue is that useful project state often never makes it back into the repo.

When I went back through the documentation, the more interesting takeaway was that the building blocks already existed. Claude Code exposes lifecycle hooks around session start, compaction, and session end. Other tools expose different surfaces: rules files, `AGENTS.md`, workspace files, knowledge exports, or local-model prompts.

That changed the question for me.

Instead of asking:

> How do I make the model remember everything?

I started asking:

> How do I make project continuity deterministic enough that any new agent session can re-enter from repo state?

That is what led me to build `repo-context-hooks`.

## What It Is

`repo-context-hooks` is a repo-native continuity layer for coding agents.

It is not a memory database. It is not a hosted knowledge layer. It is not trying to solve "AI memory" in the abstract.

It does a smaller, more operational thing:

- load repo context at session start
- checkpoint tactical state before compact
- restore working continuity after compact
- keep durable handoff state inside the repository
- adapt that repo contract to the surfaces each agent actually exposes

## The Repo Contract

The project uses a simple split:

- `README.md` explains the public project: what it does, why it exists, how to use it, and how to contribute.
- `specs/README.md` carries engineering memory: design constraints, decisions, failed attempts, active work, and handoff notes.
- `AGENTS.md` gives agents a predictable re-entry contract.

The goal is not to make a model magically remember. The goal is to make the repo a stable place for context to land.

## Platform Support

The support model is intentionally honest:

- Claude is the native lifecycle-hook path.
- Cursor uses repo rules and the repo contract.
- Codex uses `AGENTS.md` and repo-local guidance.
- Replit uses `replit.md`.
- Windsurf uses root `AGENTS.md` and `.windsurf/rules`.
- Lovable uses repo-owned Project Knowledge and Workspace Knowledge exports that still need manual UI setup.
- OpenClaw uses repo-root workspace files such as `SOUL.md`, `USER.md`, and `TOOLS.md`.
- Ollama uses a `Modelfile.repo-context` template for local-model workflows, but Ollama itself does not read repo files.
- Kimi uses root `AGENTS.md` for Kimi Code CLI project context, not generic Kimi API setup.

That boundary matters. A lot of AI tooling loses trust by treating every platform as if it exposes the same capabilities. This project tries to do the opposite: use the strongest real surface available and say clearly what remains manual.

## Why I Think This Matters

As coding agents become normal parts of development, the bottleneck will not only be model intelligence. It will also be operational reliability.

Can a new agent session understand the repo?
Can it see what was already decided?
Can it resume interrupted work without repeating the entire investigation?
Can a human teammate review the context being carried forward?

Those are repo and workflow problems, not just model problems.

`repo-context-hooks` is my attempt to make that workflow reusable.

Project:

https://github.com/narendranathe/repo-context-hooks
