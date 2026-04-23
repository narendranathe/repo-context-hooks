# Windsurf And Lovable Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add honest `partial` support for Windsurf and Lovable, with Windsurf implemented first as a repo-native rules integration and Lovable second as a hybrid repo-plus-UI knowledge integration.

**Architecture:** Extend the existing adapter registry with one repo-native adapter and one hybrid adapter. Keep all continuity artifacts checked into the repo, validate what can be verified locally, and make manual platform steps explicit in install output and public docs.

**Tech Stack:** Python 3.9+, setuptools CLI package, pytest, Markdown, git

---

## File Map

### Create

- `repo_context_hooks/platforms/windsurf.py`
- `repo_context_hooks/platforms/lovable.py`
- `repo_context_hooks/bundle/templates/windsurf-rule.md`
- `repo_context_hooks/bundle/templates/lovable-project-knowledge.md`
- `repo_context_hooks/bundle/templates/lovable-workspace-knowledge.md`

### Modify

- `repo_context_hooks/platforms/__init__.py`
- `repo_context_hooks/doctor.py`
- `README.md`
- `docs/platforms.md`
- `docs/architecture.md`
- `docs/positioning.md`
- `docs/launch/platform-roadmap.md`
- `docs/launch/platform-issue-drafts.md`
- `tests/test_platform_registry.py`
- `tests/test_platform_install_plans.py`
- `tests/test_platform_artifacts.py`
- `tests/test_doctor.py`
- `tests/test_cli.py`
- `tests/test_installer.py`
- `tests/test_bundle_integrity.py`
- `tests/test_platform_docs.py`
- `tests/test_readme_contract.py`
- `tests/test_visual_contract.py`

### Leave Untouched

- `UBIQUITOUS_LANGUAGE.md`
- `specs/`

## Task 1: Implement Windsurf Partial Support

**Files:**
- Create: `repo_context_hooks/platforms/windsurf.py`
- Create: `repo_context_hooks/bundle/templates/windsurf-rule.md`
- Modify: `repo_context_hooks/platforms/__init__.py`
- Modify: `repo_context_hooks/doctor.py`
- Test: `tests/test_platform_registry.py`
- Test: `tests/test_platform_install_plans.py`
- Test: `tests/test_platform_artifacts.py`
- Test: `tests/test_doctor.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_installer.py`
- Test: `tests/test_bundle_integrity.py`

- [ ] Add failing tests for a new `windsurf` platform id and metadata.
- [ ] Run the focused test slice and confirm the new Windsurf expectations fail.
- [ ] Implement `WindsurfAdapter` with repo-only artifacts:
  - `AGENTS.md`
  - `.windsurf/rules/repo-context-continuity.md`
- [ ] Teach `doctor.py` to validate the Windsurf rule markers.
- [ ] Update CLI/installer tests to expect `windsurf` in the supported platform list.
- [ ] Re-run the focused Windsurf slice until it passes.

## Task 2: Update Public Docs For Windsurf

**Files:**
- Modify: `README.md`
- Modify: `docs/platforms.md`
- Modify: `docs/architecture.md`
- Modify: `docs/positioning.md`
- Modify: `docs/launch/platform-roadmap.md`
- Modify: `docs/launch/platform-issue-drafts.md`
- Test: `tests/test_platform_docs.py`
- Test: `tests/test_readme_contract.py`
- Test: `tests/test_visual_contract.py`

- [ ] Rewrite the support story so Windsurf appears as current `partial` support.
- [ ] Keep the claim boundary explicit: rules-driven continuity, no native lifecycle hooks, no compact automation claim.
- [ ] Convert Windsurf roadmap text from discovery framing to current-support plus follow-up framing.
- [ ] Run the docs contract tests and confirm they pass before moving to Lovable.

## Task 3: Implement Lovable Hybrid Partial Support

**Files:**
- Create: `repo_context_hooks/platforms/lovable.py`
- Create: `repo_context_hooks/bundle/templates/lovable-project-knowledge.md`
- Create: `repo_context_hooks/bundle/templates/lovable-workspace-knowledge.md`
- Modify: `repo_context_hooks/platforms/__init__.py`
- Modify: `repo_context_hooks/doctor.py`
- Test: `tests/test_platform_registry.py`
- Test: `tests/test_platform_install_plans.py`
- Test: `tests/test_platform_artifacts.py`
- Test: `tests/test_doctor.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_installer.py`
- Test: `tests/test_bundle_integrity.py`

- [ ] Add failing tests for a new `lovable` platform id and metadata.
- [ ] Run the focused test slice and confirm the new Lovable expectations fail.
- [ ] Implement `LovableAdapter` with repo-owned exports:
  - `AGENTS.md`
  - `.lovable/project-knowledge.md`
  - `.lovable/workspace-knowledge.md`
- [ ] Include manual install steps in the adapter result:
  - connect Lovable to the GitHub repo
  - sync on the default branch
  - paste the project and workspace knowledge exports into the Lovable UI
- [ ] Teach `doctor.py` to validate the local export files and warn that UI state cannot be verified locally.
- [ ] Re-run the focused Lovable slice until it passes.

## Task 4: Update Public Docs For Lovable

**Files:**
- Modify: `README.md`
- Modify: `docs/platforms.md`
- Modify: `docs/architecture.md`
- Modify: `docs/positioning.md`
- Modify: `docs/launch/platform-roadmap.md`
- Modify: `docs/launch/platform-issue-drafts.md`
- Test: `tests/test_platform_docs.py`
- Test: `tests/test_readme_contract.py`
- Test: `tests/test_visual_contract.py`

- [ ] Rewrite the support story so Lovable appears as current `partial` support with a hybrid repo-plus-UI integration model.
- [ ] Make the manual UI steps visible in docs without implying the tool can verify or sync hosted knowledge automatically.
- [ ] Convert Lovable roadmap text from discovery framing to current-support plus follow-up framing.
- [ ] Re-run the docs contract tests and confirm they pass.

## Task 5: Full Verification And Publish

**Files:**
- Modify: any files above if verification reveals a mismatch

- [ ] Run the full test suite with a fresh temp directory.
- [ ] Refresh the editable install.
- [ ] Run CLI smoke checks for:
  - `repo-context-hooks platforms`
  - `repo-context-hooks install --platform windsurf`
  - `repo-context-hooks doctor --platform windsurf`
  - `repo-context-hooks install --platform lovable`
  - `repo-context-hooks doctor --platform lovable`
- [ ] Confirm `git status --short` only shows intended tracked changes plus the existing user-owned untracked files.
- [ ] Commit the phase in coherent chunks if the diff splits naturally; otherwise use one feature commit.
- [ ] Push the branch so the active PR reflects the new platform support.
