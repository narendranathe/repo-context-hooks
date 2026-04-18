# Repo Context Hooks Design

Date: 2026-04-17
Status: Proposed
Author: Codex with Narendranath Edara

## Summary

This spec repositions the current `repohandoff` package into a clearer, community-shareable product named `repo-context-hooks`.

The product solves a narrow but painful problem: coding-agent sessions often lose tactical project context across restarts, compaction, and handoffs. Claude Code's documentation already exposes the right lifecycle primitives through `SessionStart`, `PreCompact`, and `SessionEnd`; this project packages those ideas into a repo-local workflow that teams can install, understand, and extend.

The goal is not to build another memory platform. The goal is to make repository context durable and operational using hooks, docs, and deterministic checkpoints.

## Problem

In real repositories, agent memory fails in predictable ways:

- fresh sessions repeat repo discovery
- compaction drops active decisions and next-work state
- issue context and priorities get lost between sessions
- teams compensate with long prompts or ad hoc memory files

This creates friction exactly where agents should feel most useful: continuing work cleanly in an already-moving project.

## Goals

- Rename the public package, repo, and CLI around a literal, searchable identity.
- Position the project as repo context continuity infrastructure rather than an AI memory product.
- Preserve compatibility for anyone already using `graphify` or `repohandoff`.
- Make the GitHub repository credible and immediately useful to the community.
- Produce launch-ready LinkedIn and Substack posts grounded in the real origin story.

## Non-Goals

- Build a hosted memory service.
- Claim this solves long-term agent memory in general.
- Depend on embeddings, vector databases, or external storage.
- Over-optimize for one agent vendor at the expense of repo-local portability.

## Chosen Identity

### Public Name

`repo-context-hooks`

### Rationale

The name is intentionally literal and searchable. It communicates:

- `repo`: the repository is the source of truth
- `context`: the primary problem being solved
- `hooks`: the mechanism that makes the system deterministic

This is clearer than `repohandoff`, which is brandable but vague, and clearer than `graphify`, which suggests knowledge graphs more than operational continuity.

### Compatibility Policy

The project will keep legacy command aliases:

- `repo-context-hooks` as the primary command
- `repohandoff` as a compatibility alias
- `graphify` as a compatibility alias

This allows a cleaner public story without breaking early adopters or previous examples.

## Product Positioning

### One-Line Pitch

Hook-based repo context continuity for coding agents.

### Extended Pitch

`repo-context-hooks` preserves repository context across session start, compaction, and handoff using repo-local hooks, specs memory, and installable skills.

### Category

Agent workflow infrastructure for repository-local context continuity.

### Differentiation

Most adjacent tools focus on one of three things:

- memory retrieval
- workflow orchestration
- agent plugins and extensions

`repo-context-hooks` instead packages a deterministic operating pattern:

- lifecycle hooks
- a dual-document contract
- compact-safe checkpoints
- startup context loading

The project should describe itself as complementary to memory and orchestration tools, not as a replacement for them.

## Architecture

### Package

- Python package name: `repo-context-hooks`
- Python module name: `repo_context_hooks`

### CLI

- Primary executable: `repo-context-hooks`
- Compatibility aliases: `repohandoff`, `graphify`

### Bundled Assets

The package will continue to ship installable bundle assets for:

- reusable skills
- helper scripts
- hook configuration templates

### Runtime Contract

The installed workflow will rely on a repo-local documentation pattern:

- `README.md` for user-facing project explanation
- `specs/README.md` for build history, constraints, decisions, failures, and next-work state

The hooks synchronize and reload this state at key lifecycle boundaries.

## Repository Structure

The public repository should be structured for immediate comprehension:

- `README.md`
- `pyproject.toml`
- `repo_context_hooks/`
- `docs/`
- `examples/`
- `tests/`

Supporting docs should include:

- positioning
- competitive analysis
- architecture
- practical examples

This keeps the landing page sharp while giving deeper readers enough substance to trust the design.

## GitHub Landing Strategy

The repository must work as both a utility and a portfolio-quality public artifact.

The README should lead with:

1. the problem
2. what the package does
3. why hooks are the right primitive
4. quick install
5. example repo layout
6. supported agent environments

The README should avoid inflated claims such as "fixes agent memory" and instead emphasize deterministic continuity for real repos.

## Launch Content

The launch content should reflect a builder's perspective:

- Claude Code exposed the pain clearly
- the official docs already hinted at the right lifecycle model
- ideas from other memory and plugin projects helped shape the solution
- the final product is purpose-built around a narrower, more honest need

Two launch assets will be produced:

- a LinkedIn post optimized for short-form credibility and shareability
- a Substack post optimized for narrative, critique, and deeper explanation

## Self-Critique

This project has several risks and weaknesses that should be acknowledged publicly and addressed in the repo copy.

### Risk 1: The name is clear but not memorable

`repo-context-hooks` is stronger for discovery than branding. This is an intentional tradeoff. If the tool becomes widely adopted later, a stronger umbrella brand can sit above the package name.

### Risk 2: The category can be misunderstood

People may still interpret this as "memory for agents." The docs must repeatedly explain that this is a repo-operating pattern packaged as hooks and skills, not a long-term memory layer.

### Risk 3: The utility is only as good as the repo discipline

If a team does not maintain `specs/README.md`, the handoff quality degrades. The README and examples need to show how lightweight this upkeep can be.

### Risk 4: Existing tools already overlap partially

Some plugins and memory tools already offer resume flows, session search, or safety hooks. The project should not overstate novelty. The differentiated value is deterministic repo-local continuity using lifecycle hooks and structured project memory.

### Risk 5: The current package internals are still legacy-shaped

The implementation still carries naming and layout choices from earlier iterations. The rename must include a cleanup pass so the public repo feels intentional rather than re-skinned.

## Implementation Scope

The next implementation phase will cover:

- renaming package metadata
- renaming the Python module to `repo_context_hooks`
- adding CLI compatibility aliases
- rewriting the README for public release quality
- expanding docs for architecture and examples
- validating install and tests after the rename
- publishing a clean GitHub repository
- writing LinkedIn and Substack launch drafts

## Acceptance Criteria

- A new user can understand what the project does from the repository name and README alone.
- The package installs and the primary CLI uses the new name.
- Existing `graphify` and `repohandoff` commands continue to function.
- The repository contains enough documentation and examples for community adoption.
- The launch copy accurately tells the origin story without overclaiming.

## Open Questions

No blocking product questions remain for the rename and public packaging pass.

The main implementation judgment call is how much of the old module layout should be preserved temporarily for compatibility versus renamed immediately for clarity. The default should be to prefer clarity in the public codebase while keeping CLI aliases stable.
