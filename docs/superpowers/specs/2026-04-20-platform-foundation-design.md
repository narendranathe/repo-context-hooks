# Repo Context Hooks Platform Foundation Design

Date: 2026-04-20
Status: Proposed
Author: Narendranath Edara

## Summary

This spec defines Phase 1 of the `repo-context-hooks` product expansion: a real platform-adapter foundation with strong first-wave support for Claude, Cursor, and Codex.

The goal of this phase is not to maximize the number of logos on the README. The goal is to make the product structurally honest, extensible, and genuinely useful across more than one agent ecosystem without pretending all platforms support the same lifecycle model.

The approved direction is:

- build a narrow adapter architecture
- implement Claude as the flagship native experience
- implement Cursor and Codex as real first-wave integrations with explicit support tiers
- create GitHub issues for planned platforms that cannot be implemented credibly in this phase
- tighten the public product story around repo-native continuity rather than vague "AI memory"

## Problem

The current repository has a promising core idea, but the product surface is ahead of the implementation:

- the code only truly supports `claude` and `codex`
- the current install path is hard-coded rather than adapter-driven
- Claude is the only platform with a real runtime lifecycle path
- Codex support is skills-oriented, not parity-level runtime support
- the public README currently explains internal mechanisms better than it explains user value
- the current diagrams explain the workflow, but do not yet show a memorable interrupted-task or handoff scenario

This creates a trust gap:

- the product idea feels broader than the implemented reality
- expanding support platform-by-platform will get messy without an adapter boundary
- the README risks overpromising if the runtime model remains Claude-shaped underneath

## Goals

- Introduce a platform-adapter architecture that can support multiple agent ecosystems honestly.
- Implement Phase 1 support for Claude, Cursor, and Codex.
- Define machine-readable support tiers so docs, tests, and CLI share one source of truth.
- Add validation and platform discovery so installation claims are testable.
- Create a product-ready backlog for additional platforms using GitHub issues.
- Reposition the public story toward repo-native continuity, compaction-safe handoff, and reviewable team memory.
- Upgrade visuals and examples enough that the repo demonstrates a memorable use case rather than only abstract mechanics.

## Non-Goals

- Claim universal support for all coding agents in Phase 1.
- Force Claude-style lifecycle parity onto platforms that do not expose equivalent primitives.
- Build hosted sync, vector memory, or cross-repo semantic search.
- Expand into platform-specific features that do not directly improve repo-context continuity.
- Ship low-confidence adapters simply to grow the support matrix.

## Chosen Approach

### Product Strategy

Phase 1 will be a strong foundation with three implemented platforms, not a shallow compatibility list.

This approach was chosen because it reduces the largest product risk: a gap between the public promise and the runtime truth. A narrower but real platform story is stronger than a broad but fragile one.

### Platform Strategy

The first-wave platforms are:

- Claude
- Cursor
- Codex

These were chosen because they represent the strongest available mix of:

- lifecycle automation
- repo-context surfaces
- existing momentum in the current codebase
- community relevance for agent-enabled development workflows

Additional platforms such as Replit, Lovable, Ollama, OpenClaw, and Kimi will be tracked as planned work through GitHub issues created during this phase.

## Product Positioning

The core product claim for this phase is:

`repo-context-hooks` is the repo-native continuity layer for coding agents.

The public story should emphasize three ideas:

- the repo is the memory boundary
- useful context survives session transitions and compaction
- teams can review and improve the continuity contract in git

The public story should not claim:

- universal agent support
- lifecycle parity across all platforms
- a replacement for general memory systems

## Architecture

### Platform Adapter Boundary

The product should stop branching on platform strings inside the installer and instead use explicit platform adapters.

Each adapter should describe:

- its platform id
- display name
- support tier
- installable surfaces
- validation behavior
- lifecycle capabilities
- manual setup requirements, if any

This boundary should be narrow. Phase 1 should only add capabilities required by Claude, Cursor, and Codex.

### Core Types

The architecture should introduce:

- `PlatformAdapter`
- `InstallPlan`
- `PlatformRegistry`
- `SupportTier`

`PlatformAdapter` owns platform-specific behavior.

`InstallPlan` is the platform-neutral description of what will be written, merged, skipped, or left as manual guidance.

`PlatformRegistry` resolves adapters for CLI commands and support-matrix generation.

`SupportTier` defines the honesty boundary for docs, CLI output, and tests.

### Support Tiers

The support tiers are:

- `native`
- `partial`
- `planned`

Definitions:

- `native`
  - automated install
  - validated by tests
  - meaningful runtime or lifecycle integration
  - can be described as first-class support in public docs
- `partial`
  - automated install for some but not all useful surfaces
  - validated core behavior
  - explicit limits documented
  - cannot be described as parity with `native`
- `planned`
  - issue exists
  - intended integration shape documented
  - not publicly claimed as supported

## Phase 1 Platform Scope

### Claude

Tier: `native`

Claude remains the flagship implementation in Phase 1.

Claude support must include:

- skill installation into `~/.claude/skills`
- repo-local script installation into `.claude/scripts`
- settings merge for lifecycle hooks in `.claude/settings.json`
- validation of repo contract and Claude-specific runtime surfaces
- continuity support across `SessionStart`, `PreCompact`, `PostCompact`, and `SessionEnd`

Claude is the reference implementation for the adapter architecture, but it must not distort the abstraction to the point that other platforms become awkward.

### Cursor

Tier: `partial`

Cursor support must be real, useful, and explicitly narrower than Claude.

Cursor support should include:

- generation or installation of `.cursor/rules/*.mdc` artifacts that encode repo continuity expectations
- support for `AGENTS.md` as part of the repo contract
- validation of Cursor-facing rule and repo-context files
- optional background-agent guidance only if the resulting experience is concrete and testable

Cursor support must not claim:

- Claude hook parity
- equivalent compaction lifecycle semantics unless implemented and validated

### Codex

Tier: `partial`

Codex support should formalize the repo-contract workflow already implied by the current package.

Codex support should include:

- skill installation into the Codex skills home
- `AGENTS.md` integration as part of the repo contract
- validation of installed skills and required repo context files
- clear documentation of what continuity Codex users get and what they do not

Codex support must not claim native lifecycle hook parity unless a real mechanism exists and is tested.

## Repo Contract

The repo contract in Phase 1 is:

- `README.md`
- `specs/README.md`
- `AGENTS.md`

Responsibilities:

- `README.md`
  - user-facing product and contribution intent
- `specs/README.md`
  - engineering memory, constraints, decisions, failures, next work
- `AGENTS.md`
  - agent operating instructions and repo-context loading expectations

The contract is universal.

What changes per platform is how that contract is surfaced, installed, validated, and reinforced.

## CLI And Validation

Phase 1 should add or formalize these CLI surfaces:

- `repo-context-hooks install --platform <id>`
- `repo-context-hooks platforms`
- `repo-context-hooks doctor`

`install` should resolve the selected adapter, execute its install plan, and print a clear summary of:

- what was installed
- what was validated
- what remains manual

`platforms` should list:

- platform id
- display name
- support tier
- short description of installed surfaces

The support-matrix output should be generated from the same adapter metadata used by the installer and validator. Public docs must not maintain a separate hand-written support table that can drift away from the code.

`doctor` should validate:

- repo contract files
- platform-specific install surfaces
- obvious missing or inconsistent state

The CLI should become the public truth source for support claims.

## Documentation Strategy

Phase 1 documentation should separate public product messaging from operator detail.

### Public README

The public README should:

- lead with outcome-first positioning
- describe the repo-native continuity value clearly
- show concrete interrupted-task and handoff examples
- publish a support matrix based on support tiers
- explicitly say that Phase 1 is currently tested around Claude, Cursor, and Codex
- avoid surfacing internal critique as a primary section

The README should not remain an operator manual.

### Supporting Docs

Operator detail should move into focused docs such as:

- install details
- platform matrix
- architecture notes
- limitations and comparisons

## Visual Strategy

The current diagrams should be upgraded from abstract concept diagrams to concrete operational stories.

The three key visuals should answer different questions:

- what happens during an interrupted session and resume
- where state lives in the repo and platform surfaces
- why outcomes differ before and after the continuity layer

Preferred examples:

- a bugfix interrupted by compaction
- a new agent resuming from repo state
- a handoff grounded in repo artifacts instead of chat history

## Testing Strategy

Phase 1 should follow test-driven development.

Tests should cover:

- adapter registry and lookup
- install plan generation per platform
- support tier metadata
- platform-specific install behavior
- `platforms` CLI output
- `doctor` validation output
- README/support-matrix consistency where appropriate

Tests must prevent support-tier drift. A platform cannot be documented more strongly than the code and tests justify.

## Product-Driven Development Backlog

Platforms that are not implemented in Phase 1 should get GitHub issues during this phase.

At minimum, create issues for:

- Replit adapter
- Lovable adapter
- Ollama adapter strategy
- OpenClaw adapter strategy
- Kimi adapter strategy

Each issue should define:

- proposed support tier
- likely integration surface
- what would count as a credible implementation
- open questions or blockers

The issue set should also establish labels or a naming convention that makes the roadmap readable from the GitHub issue list alone, such as `platform`, `planned`, and the specific platform name.

## Deliverables

Phase 1 should produce:

- adapter architecture in code
- Claude adapter at `native`
- Cursor adapter at `partial`
- Codex adapter at `partial`
- CLI support for install, platforms, and doctor
- updated tests for adapter-driven behavior
- public README repositioned around repo-native continuity
- upgraded visuals that show concrete continuity scenarios
- GitHub issues for planned platforms

## Risks

- The adapter layer could become over-engineered if it is designed for hypothetical platforms instead of real Phase 1 needs.
- Cursor and Codex support could be described too generously if the support tier bar is not enforced in tests.
- README polish could get ahead of runtime reality if the public copy is rewritten before the support matrix is grounded in code.
- The visual refresh could stay too abstract if it avoids showing a real interrupted work scenario.

## Mitigations

- Keep the adapter interface narrow and justified by current platforms only.
- Tie support-matrix output to machine-readable tier metadata.
- Validate support claims in tests.
- Prefer one concrete workflow example over three abstract diagrams.
- Create issues for anything not credibly shippable in this phase instead of inflating support.

## Success Criteria

Phase 1 is successful if:

- the codebase no longer hard-codes platform behavior in one tuple-based installer path
- Claude, Cursor, and Codex have explicit adapter implementations
- the CLI can list and validate supported platforms
- public docs clearly distinguish `native`, `partial`, and `planned`
- no public documentation claims support beyond what code and tests validate
- additional platform work is captured as GitHub issues rather than implied promises
