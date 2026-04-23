# Replit Adapter Design

Date: 2026-04-22
Status: Proposed
Author: Narendranath Edara

## Summary

This spec defines the next platform phase for `repo-context-hooks`: add honest `partial` support for Replit by using `replit.md` as the checked-in continuity surface for Replit Agent.

The important constraint is to map onto a real Replit primitive instead of inventing Claude-style hook parity. Replit documents `replit.md` as a root-level file that Agent reads automatically for project context, coding style, and preferences. That makes it a credible repo-native entry point for continuity, even though it does not provide native lifecycle hooks equivalent to Claude.

## Verified Platform Surface

Official Replit docs describe `replit.md` as:

- a file stored at the project root
- automatically read by Replit Agent
- editable by users to customize project context and behavior
- required to live at the root to work properly

The same docs also distinguish `.replit` as app/runtime configuration, not the primary Agent continuity surface.

This means the honest support surface for Replit is:

- `replit.md` for Replit Agent context
- `AGENTS.md` for repo-contract continuity
- `README.md` and `specs/README.md` as the durable source-of-truth docs the adapter points back to

## Problem

The current roadmap still treats Replit as planned, even though the platform now exposes a documented repo-root file designed for project context. Leaving Replit as backlog-only creates two problems:

- the support matrix underclaims a platform we can now integrate credibly
- the product misses a practical example of repo-native continuity outside Claude/Cursor/Codex

## Goals

- Add a real `ReplitAdapter` to the platform registry.
- Ship Replit at `partial` tier.
- Install `replit.md` and `AGENTS.md` into the repo when requested.
- Add `doctor` coverage for Replit continuity artifacts.
- Update public docs so Replit is described as implemented rather than planned.
- Keep the public claim boundary honest: no lifecycle hook parity, no automation claims Replit does not expose.

## Non-Goals

- Do not add fake lifecycle hooks to Replit support.
- Do not use `.replit` as the continuity contract unless a future phase requires runtime setup.
- Do not claim that `replit.md` replaces `README.md` or `specs/README.md`.
- Do not remove issue `#2` in this phase; it can remain as the historical backlog artifact until merge and follow-up cleanup.

## Chosen Approach

### Support Tier

Replit should ship as `partial`.

Why:

- the platform has a real checked-in context file that Agent consumes
- the install path is repo-local and testable
- continuity is manual-or-resume-driven rather than hook-driven

### Repo Artifacts

The adapter should install:

- `replit.md`
- `AGENTS.md`

`replit.md` should point Replit Agent back to the repo contract:

- read `README.md` for product intent
- read `specs/README.md` for constraints, decisions, failures, and next work
- read `AGENTS.md` for operating instructions
- preserve continuity back into repo files instead of chat-only state

### Manual Guidance

The adapter should emit manual steps explaining the practical limitation:

- after creating or updating `replit.md`, reopen or start a fresh Replit Agent conversation so the root-file context is reloaded cleanly

This is a feature, not a weakness, as long as it is stated plainly.

## Architecture Impact

The implementation should stay narrow:

- add `repo_context_hooks/platforms/replit.py`
- register it in `repo_context_hooks/platforms/__init__.py`
- add a `replit.md` template to the bundle
- teach `doctor.py` how to validate the required markers in `replit.md`

No installer-core redesign should be required beyond the registry picking up one more adapter.

## Documentation Impact

The public docs should shift from a three-platform story to a current-support story:

- README should describe Replit as current `partial` support
- `docs/platforms.md` should move Replit from `planned` to `partial`
- positioning and architecture docs should mention Replit alongside Cursor and Codex as a repo-surface-driven path
- roadmap docs should stop describing Replit as purely planned

## Risks

- The `replit.md` template could become too long or generic, reducing usefulness.
- Public docs could overstate what “partial” means if they imply lifecycle automation.
- Tests may hard-code the old three-platform world and drift if not updated consistently.

## Mitigations

- Keep `replit.md` concise and repo-contract-focused.
- Add explicit warnings and manual steps in install output.
- Update registry, installer, doctor, docs, and README contract tests together.

## Success Criteria

This phase is successful if:

- `repo-context-hooks install --platform replit` writes `replit.md` and `AGENTS.md`
- `repo-context-hooks doctor --platform replit` can detect missing or invalid Replit continuity files
- public docs show Replit as `partial`, not `planned`
- no docs claim lifecycle hooks or automated compact handling on Replit
