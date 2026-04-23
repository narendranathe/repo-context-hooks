# Kimi Code Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add narrow `partial` Kimi Code CLI support through root `AGENTS.md` only.

**Architecture:** Extend the platform adapter registry with a repo-only Kimi adapter that writes the shared `AGENTS.md` contract. Keep all Kimi-specific behavior in warnings/manual steps because there is no stable Kimi-specific rules path or lifecycle hook surface to automate.

**Tech Stack:** Python 3.9+, setuptools CLI package, pytest, Markdown, git

---

## File Map

### Create

- `repo_context_hooks/platforms/kimi.py`

### Modify

- `repo_context_hooks/platforms/__init__.py`
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
- `tests/test_platform_docs.py`
- `tests/test_readme_contract.py`

## Task 1: Add Kimi Tests First

- [ ] Add registry tests expecting `kimi`.
- [ ] Add install-plan tests expecting `AGENTS.md` only.
- [ ] Add artifact tests expecting installed `AGENTS.md` and Kimi manual steps.
- [ ] Add doctor tests for missing, installed, and placeholder `AGENTS.md`.
- [ ] Add installer and CLI tests expecting Kimi output.
- [ ] Run the focused test slice and confirm it fails because Kimi is not implemented yet.

## Task 2: Implement Kimi Adapter

- [ ] Create `KimiAdapter` with `partial` tier metadata.
- [ ] Reuse the shared `AGENTS.md` template.
- [ ] Add warnings that this targets Kimi Code CLI project context, not generic Kimi API support.
- [ ] Add manual steps for running/reviewing Kimi Code `/init` and merging with the repo contract.
- [ ] Register the adapter.
- [ ] Run the focused test slice and make it pass.

## Task 3: Update Public Docs And Roadmap

- [ ] Update README quickstart and support wording to include Kimi as `partial`.
- [ ] Update `docs/platforms.md` with the Kimi row and caveat.
- [ ] Update architecture and positioning docs to include Kimi Code CLI `AGENTS.md` support.
- [ ] Convert Kimi roadmap text from discovery-only to current-support plus follow-up.
- [ ] Keep issue #6 as the follow-up tracker and retitle it if needed.
- [ ] Run docs contract tests.

## Task 4: Full Verification And Publish

- [ ] Run the full test suite with a fresh temp directory.
- [ ] Refresh the editable install.
- [ ] Smoke test:
  - `repo-context-hooks platforms`
  - `repo-context-hooks install --platform kimi`
  - `repo-context-hooks doctor --platform kimi`
- [ ] Commit the Kimi phase in a coherent commit.
- [ ] Push the branch so PR #7 reflects the new platform support.

## Self-Review

- Spec coverage: covered adapter, warnings, doctor, docs, roadmap, and verification.
- Placeholder scan: no placeholders remain.
- Type consistency: uses the existing adapter terms and repo-only install pattern.
