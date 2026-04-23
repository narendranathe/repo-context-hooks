# Replit Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add honest `partial` Replit support using `replit.md`, update validation and docs, and keep public product claims aligned with the actual platform surface.

**Architecture:** Add one new adapter plus one new repo template, then thread Replit through the existing registry, doctor checks, tests, and public docs. Treat `replit.md` as the platform-specific entry point and keep the repo contract anchored in `README.md`, `specs/README.md`, and `AGENTS.md`.

**Tech Stack:** Python 3.9+, setuptools CLI package, pytest, Markdown, git

---

### Task 1: Add The Replit Adapter And Template

**Files:**
- Create: `repo_context_hooks/platforms/replit.py`
- Create: `repo_context_hooks/bundle/templates/replit.md`
- Modify: `repo_context_hooks/platforms/__init__.py`
- Modify: `tests/test_platform_registry.py`
- Modify: `tests/test_platform_install_plans.py`
- Modify: `tests/test_platform_artifacts.py`

- [ ] Add `ReplitAdapter` with `partial` tier metadata and install surfaces `("replit-md", "repo-contract")`.
- [ ] Have the install plan point at repo-root `replit.md` and `AGENTS.md`, with no home paths.
- [ ] Add warnings that Replit does not expose native lifecycle hooks.
- [ ] Add a manual step telling users to start a fresh Replit Agent conversation after `replit.md` changes.
- [ ] Create a concise `replit.md` template that points Replit Agent back to `README.md`, `specs/README.md`, and `AGENTS.md`.
- [ ] Update registry and adapter-plan tests to include Replit.

### Task 2: Extend Validation And CLI Expectations

**Files:**
- Modify: `repo_context_hooks/doctor.py`
- Modify: `tests/test_doctor.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_installer.py`
- Modify: `tests/test_bundle_integrity.py`

- [ ] Teach `doctor.py` to validate required markers inside `replit.md`.
- [ ] Add install and doctor tests for Replit missing/present/invalid states.
- [ ] Update CLI expectations so `platforms` output includes Replit.
- [ ] Update installer tests for the new supported platform list.
- [ ] Extend bundle-integrity coverage to protect the new template.

### Task 3: Update Public Docs And Roadmap Language

**Files:**
- Modify: `README.md`
- Modify: `docs/platforms.md`
- Modify: `docs/architecture.md`
- Modify: `docs/positioning.md`
- Modify: `docs/launch/platform-roadmap.md`
- Modify: `docs/launch/platform-issue-drafts.md`
- Modify: `tests/test_readme_contract.py`
- Modify: `tests/test_platform_docs.py`
- Modify: `tests/test_visual_contract.py`

- [ ] Move the public README from a “Phase 1 only” framing to a current-support framing.
- [ ] Describe Replit as `partial` support without claiming hook parity.
- [ ] Update platform docs, positioning, and architecture notes to mention Replit honestly.
- [ ] Remove Replit from the planned-only roadmap language and mark it as implemented in the current branch.
- [ ] Update README/docs contract tests so they protect the new support story.

### Task 4: Verify, Commit, And Push

**Files:**
- Modify: any files above as needed for final consistency

- [ ] Run the full test suite with a fresh temp directory.
- [ ] Confirm git status only includes intended tracked changes plus the user-owned untracked files.
- [ ] Commit the adapter and doc changes separately if the diff naturally splits cleanly; otherwise use one coherent feature commit.
- [ ] Push the branch so PR #7 reflects the new Replit phase work.
