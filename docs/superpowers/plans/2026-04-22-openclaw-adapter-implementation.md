# OpenClaw Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add honest `partial` OpenClaw support through repo-root workspace files and manual runtime activation steps.

**Architecture:** Extend the platform adapter registry with an OpenClaw adapter that writes sanitized workspace files into the repo root. Validate the local files with `doctor`, but keep active OpenClaw runtime configuration manual and clearly warned.

**Tech Stack:** Python 3.9+, setuptools CLI package, pytest, Markdown, git

---

## File Map

### Create

- `repo_context_hooks/platforms/openclaw.py`
- `repo_context_hooks/bundle/templates/openclaw-soul.md`
- `repo_context_hooks/bundle/templates/openclaw-user.md`
- `repo_context_hooks/bundle/templates/openclaw-tools.md`

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

## Task 1: Add OpenClaw Tests First

- [ ] Add registry tests expecting `openclaw` after `lovable`.
- [ ] Add install-plan tests expecting `AGENTS.md`, `SOUL.md`, `USER.md`, and `TOOLS.md`.
- [ ] Add artifact tests expecting installed OpenClaw files to contain repo-contract markers.
- [ ] Add doctor tests for missing, installed, and placeholder OpenClaw files.
- [ ] Add installer and CLI tests expecting OpenClaw manual workspace steps and platform output.
- [ ] Run the focused test slice and confirm it fails because OpenClaw does not exist yet.

## Task 2: Implement OpenClaw Adapter

- [ ] Create `OpenClawAdapter` with `partial` tier metadata.
- [ ] Add templates for `SOUL.md`, `USER.md`, and `TOOLS.md`.
- [ ] Reuse the shared `AGENTS.md` template.
- [ ] Add manual steps:
  - configure OpenClaw `agents.defaults.workspace` to the repo root, or copy the generated files into the active OpenClaw workspace
  - keep secrets and private memory out of public repos
  - run OpenClaw's own doctor/setup commands after changing workspace configuration
- [ ] Register the adapter.
- [ ] Teach `doctor.py` to validate OpenClaw markers.
- [ ] Run the focused test slice and make it pass.

## Task 3: Update Public Docs And Roadmap

- [ ] Update README quickstart and support wording to include OpenClaw as `partial`.
- [ ] Update `docs/platforms.md` with the OpenClaw row and caveat.
- [ ] Update architecture and positioning docs to include workspace-file-driven support.
- [ ] Convert OpenClaw roadmap text from discovery-only to current-support plus follow-up.
- [ ] Link Windsurf issue `#8`, reuse Lovable issue `#3`, and keep OpenClaw issue `#5` as the follow-up tracker.
- [ ] Run docs contract tests.

## Task 4: Full Verification And Publish

- [ ] Run the full test suite with a fresh temp directory.
- [ ] Refresh the editable install.
- [ ] Smoke test:
  - `repo-context-hooks platforms`
  - `repo-context-hooks install --platform openclaw`
  - `repo-context-hooks doctor --platform openclaw`
- [ ] Confirm `git status --short` only shows intended tracked changes plus existing user-owned untracked files.
- [ ] Commit the OpenClaw phase in a coherent commit.
- [ ] Push the branch so PR #7 reflects the new platform support.

## Self-Review

- Spec coverage: covered registry, installer, templates, doctor, docs, roadmap, and verification.
- Placeholder scan: no `TBD` or ambiguous future-only tasks remain.
- Type consistency: uses the existing adapter terms `InstallPlan`, `InstallResult`, `SupportTier.PARTIAL`, and `build_install_plan`.
