# Repo Context Hooks README And Visual Polish Design

Date: 2026-04-20
Status: Proposed
Author: Narendranath Edara

## Summary

This spec defines the public-facing README and visual-polish pass for `repo-context-hooks`.

The goal is to turn the repository from a technically correct package into a stronger community-facing artifact that developers can trust quickly, understand deeply, and share easily. The README should support fast adoption without feeling shallow, and the visual layer should explain the lifecycle and repo contract without depending on fragile GitHub-unfriendly animation.

The approved direction is:

- a balanced README
- static SVG diagrams as the primary visual medium
- stronger inline technical detail
- an explicit self-critique section

## Problem

The current repository is functional, but the landing experience is still too narrow:

- it explains the product at a high level, but not with enough mechanical clarity
- it does not visually explain how the lifecycle hooks work
- it does not surface enough implementation detail for skeptical developers
- it does not yet demonstrate self-awareness about tradeoffs and limitations

For a community-facing open-source repo, that creates risk:

- interested users may not install because the mechanism still feels abstract
- experienced engineers may not trust the claims without technical specifics
- the repo misses an opportunity to become a portfolio-quality artifact with strong explanatory depth

## Goals

- Restructure `README.md` into a clearer GitHub landing page.
- Add static SVG diagrams that explain the lifecycle, repo contract, and before/after operational value.
- Surface more technical detail directly in the README instead of burying everything in secondary docs.
- Add explicit, credible self-critique to reduce overclaiming.
- Keep the README GitHub-safe, lightweight, and maintainable.
- Preserve the existing docs/examples as supporting depth rather than forcing the README to carry everything alone.

## Non-Goals

- Build a marketing-heavy animated landing page inside GitHub.
- Introduce fragile README dependencies on GIFs, video, or client-side interactivity.
- Claim that this project solves general agent memory.
- Replace the architecture/examples docs with long README duplication.

## Chosen Approach

### README Strategy

Use a balanced technical README with inline SVG diagrams.

This approach was chosen because it best satisfies two competing needs:

- a new user should be able to understand the product and try it quickly
- an experienced developer should be able to inspect the mechanism and trust that the project is intellectually honest

### Visual Strategy

Use static SVG diagrams as the primary repo visuals.

This approach was chosen because SVGs are:

- lightweight
- sharp on GitHub
- versionable in git
- reusable across README, docs, and social assets
- maintainable as technical artifacts instead of throwaway media

## README Information Architecture

The README should be rewritten into this exact sequence:

1. Hero
2. Why This Exists
3. How It Works
4. Repo Contract
5. Before / After
6. What `install` Actually Does
7. Technical Details
8. Honest Critique
9. Examples
10. Development
11. License

## README Section Design

### 1. Hero

The hero should include:

- project name
- one-line pitch
- a short explanation paragraph
- primary install command
- compatibility alias commands

The hero should optimize for immediate comprehension, not brand theater.

### 2. Why This Exists

This section should explain the concrete failure modes:

- session re-discovery
- tactical context loss during compaction
- next-work drift
- issue/context decay across handoffs

The tone should frame this as a continuity problem, not a vague "LLMs forget things" complaint.

### 3. How It Works

This section should summarize the lifecycle model and embed `lifecycle-flow.svg`.

It should explain:

- what each hook phase does
- why those phases are enough to preserve useful continuity
- how the repo remains the source of truth

### 4. Repo Contract

This section should embed `repo-contract.svg` and explain:

- `README.md` as user-facing product intent
- `specs/README.md` as engineering memory and next-work state
- hooks and skills as the mechanism connecting those layers

### 5. Before / After

This section should embed `before-after-continuity.svg`.

Its purpose is to help readers understand the operational shift:

- before: rediscovery and context drift
- after: deterministic startup context and clearer handoffs

### 6. What `install` Actually Does

This section should be more exact than the current version.

It should explicitly describe:

- what skill directories receive installed content
- what scripts are copied into `.claude/scripts`
- how `.claude/settings.json` is merged
- what repo-local expectations exist for the contract to be useful

### 7. Technical Details

This section should include:

- supported platforms
- primary CLI and compatibility aliases
- expected repo layout
- links to architecture and example docs

It should be concise, but specific enough that skeptical developers do not need to guess.

### 8. Honest Critique

This section is mandatory.

It should explicitly state:

- this is not a vector memory layer
- this is not a hosted platform
- this does not replace repo discipline
- poor `specs/README.md` hygiene reduces the value quickly
- teams needing cross-repo semantic memory may still want another tool alongside this one

### 9. Examples

This section should point readers toward:

- `examples/minimal-repo/`
- `examples/multi-project/`
- `docs/architecture.md`

The README should link outward here rather than duplicating example detail in full.

### 10. Development

This section should keep the current editable-install and test commands, but add a slightly clearer invitation for contributors.

## Visual Asset Plan

The repo should add these SVG assets:

- `assets/diagrams/lifecycle-flow.svg`
- `assets/diagrams/repo-contract.svg`
- `assets/diagrams/before-after-continuity.svg`

### SVG 1: Lifecycle Flow

Purpose:

- explain the lifecycle model quickly
- make the hook phases memorable

Content:

- `SessionStart`
- `PreCompact`
- `PostCompact`
- `SessionEnd`
- a short caption beneath each phase

### SVG 2: Repo Contract

Purpose:

- explain the core operating model

Content:

- `README.md`
- `specs/README.md`
- hooks/skills connecting those files

### SVG 3: Before / After Continuity

Purpose:

- communicate value quickly for readers and social sharing

Content:

- "before" state: rediscovery, drift, unclear next work
- "after" state: loaded context, checkpoints, deterministic handoff

## Animation Policy

The README should remain static-SVG-first.

If animation is added later, it should follow these constraints:

- derive from the same SVG source assets
- live in docs/demo assets rather than becoming a README dependency
- clarify flow rather than merely decorate
- avoid implying capabilities the project does not actually automate

The repo may later add:

- `docs/demo/animation-plan.md`

That document can describe how short motion assets would be generated from the SVG source for launch posts and demos.

## Technical Depth To Surface Inline

The README should not stop at pitch-level language.

It should explicitly answer these developer questions:

- what files does install write?
- where do the skills go?
- how does settings merge work?
- what exact repo contract does this tool assume?
- where does this stop helping?

The answer should not be exhaustive implementation documentation, but it should remove ambiguity.

## Tone And Writing Guidance

The README should sound:

- precise
- direct
- technically respectful
- honest about scope

It should avoid:

- inflated AI-product language
- vague claims about memory
- overly abstract theory before installation

## Self-Critique

This README/visual pass has its own risks:

### Risk 1: The README can become too long

A stronger README is useful, but if too much documentation is pulled upward from `docs/`, the landing page becomes heavy and harder to scan. The fix is to keep deeper material linked, not duplicated.

### Risk 2: The visuals can oversimplify

The SVGs should clarify the model without pretending the project is more automatic or more intelligent than it is. They should visualize the actual mechanism, not a fantasy workflow.

### Risk 3: The critique section can scare away casual users

That is acceptable. The project should optimize for credibility over hype. A smaller number of better-fit adopters is preferable to shallow interest followed by disappointment.

### Risk 4: Static SVGs are less immediately flashy than GIFs

This is an intentional tradeoff. The repo should prioritize clarity, performance, and maintainability over novelty.

## Acceptance Criteria

- A new visitor can understand the product from the README without opening secondary docs.
- The README includes all three SVG diagrams inline.
- The README explains installation side effects and repo expectations with more specificity than today.
- The README includes an explicit honest-critique section.
- The visual layer is static-SVG-first and GitHub-safe.
- The repo remains credible to experienced engineers while still being approachable to first-time users.

## Open Questions

No blocking product questions remain for the README/visual pass.

The remaining implementation judgment calls are editorial:

- how much technical detail belongs directly in `README.md` versus linked docs
- how much whitespace and sectioning is needed to keep the README scannable
- whether to add optional badges or keep the top matter minimal
