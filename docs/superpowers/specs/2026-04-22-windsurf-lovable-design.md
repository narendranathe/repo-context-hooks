# Windsurf And Lovable Design

Date: 2026-04-22
Status: Proposed
Author: Narendranath Edara

## Summary

This spec defines the next product phase for `repo-context-hooks`: add `partial` support for Windsurf and Lovable without weakening the repo-native continuity claim.

The two platforms use different integration shapes:

- Windsurf is a repo-native `partial` integration built around root `AGENTS.md` and `.windsurf/rules/`.
- Lovable is a hybrid `partial` integration built around checked-in repo docs plus manual UI knowledge steps for Project Knowledge and Workspace Knowledge.

The repo remains the source of truth in both cases.

## Verified Platform Surfaces

### Windsurf

Official Windsurf docs state:

- root `AGENTS.md` files are treated as always-on rules
- subdirectory `AGENTS.md` files are scoped automatically
- `.windsurf/rules/` is a first-class rule surface
- durable knowledge should live in Rules or `AGENTS.md`, not only in auto-generated Memories

This makes Windsurf a strong repo-native `partial` candidate.

### Lovable

Official Lovable docs state:

- GitHub sync is bidirectional on the default branch
- root repo instruction files such as `AGENTS.md` or `CLAUDE.md` can guide the Lovable agent
- Project Knowledge and Workspace Knowledge are persistent UI-managed instruction surfaces

This makes Lovable a credible hybrid `partial` candidate, but not a hook-based one.

## Problem

The current roadmap still leaves Windsurf and Lovable out of the live support matrix, even though both platforms now expose documented continuity surfaces.

If we leave them as planned-only:

- we underclaim real support opportunities
- we miss two different product proof points:
  - repo-native rules-driven continuity in Windsurf
  - repo-plus-UI knowledge continuity in Lovable

If we overclaim:

- we dilute the product’s strongest differentiator: honest support boundaries

## Goals

- Add a real `WindsurfAdapter` as `partial` support.
- Add a real `LovableAdapter` as `partial` support.
- Keep the repo as the canonical continuity source in both cases.
- Extend `doctor` so it validates local repo artifacts for both platforms.
- Update the public support matrix and positioning docs to include both platforms honestly.
- Preserve the claim boundary: no fake lifecycle hooks, no fake compact automation, no hosted-memory overclaim.

## Non-Goals

- Do not claim native lifecycle hooks for Windsurf or Lovable.
- Do not claim compact-event checkpoint automation on either platform.
- Do not attempt to verify remote Lovable UI state locally.
- Do not replace checked-in repo docs with hosted knowledge fields.

## Chosen Approach

### Windsurf

Tier: `partial`

Install shape:

- `AGENTS.md`
- `.windsurf/rules/repo-context-continuity.md`

Behavior:

- keep root `AGENTS.md` focused on repo contract and operating instructions
- use a Windsurf rule file for durable, repo-visible continuity guidance
- warn clearly that support is rules-driven, not hook-driven

### Lovable

Tier: `partial`

Install shape:

- `AGENTS.md`
- `.lovable/project-knowledge.md`
- `.lovable/workspace-knowledge.md`

Behavior:

- treat the `.lovable/*.md` files as canonical exports owned by the repo
- print manual install steps telling the user to paste them into Lovable’s Project Knowledge and Workspace Knowledge UI
- require GitHub sync on the default branch as part of the truthful support story

## Architecture Impact

### Windsurf

Add:

- `repo_context_hooks/platforms/windsurf.py`
- `repo_context_hooks/bundle/templates/windsurf-rule.md`

Update:

- `repo_context_hooks/platforms/__init__.py`
- `repo_context_hooks/doctor.py`

### Lovable

Add:

- `repo_context_hooks/platforms/lovable.py`
- `repo_context_hooks/bundle/templates/lovable-project-knowledge.md`
- `repo_context_hooks/bundle/templates/lovable-workspace-knowledge.md`

Update:

- `repo_context_hooks/platforms/__init__.py`
- `repo_context_hooks/doctor.py`

## Validation Strategy

### Windsurf

`doctor` should validate:

- `AGENTS.md`
- `.windsurf/rules/repo-context-continuity.md`

The Windsurf rule file should include clear markers referencing:

- `README.md`
- `specs/README.md`
- `AGENTS.md`

### Lovable

`doctor` should validate:

- `AGENTS.md`
- `.lovable/project-knowledge.md`
- `.lovable/workspace-knowledge.md`

It should also emit a warning that Lovable UI knowledge cannot be verified locally.

## Documentation Impact

Public docs should distinguish two support shapes:

- repo-consumed platforms:
  - Claude
  - Cursor
  - Codex
  - Replit
  - Windsurf
- repo-plus-manual-platform-UI platforms:
  - Lovable

The README and platform matrix should explain that the repo is still canonical, while some platforms consume the repo directly and others require a repo-owned export to be pasted into a platform UI.

## Risks

- Windsurf support could become redundant if the rule file duplicates `AGENTS.md` too closely.
- Lovable support could be overclaimed if the docs blur installed repo files with actual UI state.
- The support matrix could drift because the product story now spans more than one integration shape.

## Mitigations

- Keep Windsurf rule content complementary to `AGENTS.md`, not duplicative.
- Make Lovable install output explicit about what is local versus what remains manual.
- Update tests, docs, and CLI output in the same phase so support claims stay aligned.

## Success Criteria

This phase is successful if:

- `repo-context-hooks install --platform windsurf` writes the expected repo files
- `repo-context-hooks doctor --platform windsurf` validates them correctly
- `repo-context-hooks install --platform lovable` writes canonical repo-owned knowledge exports and prints manual UI steps
- `repo-context-hooks doctor --platform lovable` validates the local export files and warns about unverifiable UI state
- public docs describe both platforms as `partial` without implying hook parity
