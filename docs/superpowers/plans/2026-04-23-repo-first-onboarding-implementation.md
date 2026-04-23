# Repo-First Onboarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make repo-first onboarding real by adding `init`, adding repo-wide `doctor`, and updating docs/tests so the CLI matches the product story.

**Architecture:** Add a small repo-contract runtime layer used by both `init` and repo-wide `doctor`, then thread the new behavior through the CLI without changing the existing platform adapter model. Keep platform-specific install and diagnose flows as opt-in step 2.

**Tech Stack:** Python, argparse, pytest, Markdown docs

---

### Task 1: Add repo-contract runtime helpers

**Files:**
- Create: `repo_context_hooks/repo_contract.py`
- Modify: `repo_context_hooks/installer.py`

- [ ] Add helper functions to create or normalize `README.md`, `specs/README.md`, `UBIQUITOUS_LANGUAGE.md`, and `AGENTS.md`.
- [ ] Reuse existing bundle templates and memory bootstrap behavior where possible.
- [ ] Keep default behavior safe: only create missing files unless `force=True`.

### Task 2: Add repo-wide doctor support

**Files:**
- Modify: `repo_context_hooks/doctor.py`
- Modify: `repo_context_hooks/cli.py`

- [ ] Add a repo-contract report type and render path.
- [ ] Make `repo-context-hooks doctor` validate the repo contract when no platform is supplied.
- [ ] Keep `doctor --platform <id>` working exactly as the platform-specific path.

### Task 3: Add `init` CLI command

**Files:**
- Modify: `repo_context_hooks/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_doctor.py`
- Create: `tests/test_repo_contract_runtime.py`

- [ ] Add parser support for `init`.
- [ ] Implement `init` so it prints statuses for created or skipped files.
- [ ] Add tests covering `init`, repo-wide doctor, and the safe-by-default non-clobber behavior.

### Task 4: Update docs

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/platform-playbooks.md`

- [ ] Update quickstart to start with `init`, then repo-wide `doctor`, then platform install.
- [ ] Explain the repo-first onboarding model in the docs.
- [ ] Keep public platform claims unchanged.

### Task 5: Verify and publish

**Files:**
- Modify only files from Tasks 1-4

- [ ] Run `python -m pytest -q --basetemp .pytest-tmp-repo-first-onboarding`.
- [ ] Review `git diff --stat` and `git status --short`.
- [ ] Commit, push, and open a PR once verification is green.
