# Platform Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a readiness matrix with `doctor --all-platforms` and a transparent `recommend` command that suggests the next best setup path for the current repo.

**Architecture:** Extend the doctor layer with a multi-platform summary report, then add a small recommendation module that scores visible repo signals and prints transparent next-step guidance. Keep the platform adapter model unchanged and reuse the existing repo-contract and platform doctor behavior as the source of truth.

**Tech Stack:** Python, argparse, pytest, Markdown docs

---

### Task 1: Add failing tests for the new CLI surface

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `tests/test_doctor.py`
- Create: `tests/test_recommend.py`

- [ ] Add parser tests for `doctor --all-platforms` and `recommend`.
- [ ] Add CLI behavior tests for the matrix summary output.
- [ ] Add recommendation tests for missing repo contract, repo-contract-only repos, and repos with platform-specific signals.

### Task 2: Add multi-platform doctor support

**Files:**
- Modify: `repo_context_hooks/doctor.py`
- Modify: `repo_context_hooks/cli.py`

- [ ] Add report models for platform readiness rows and multi-platform summaries.
- [ ] Build `doctor --all-platforms` from the existing repo-contract and platform doctor checks.
- [ ] Keep the existing single-platform doctor path intact.

### Task 3: Add recommendation runtime

**Files:**
- Create: `repo_context_hooks/recommend.py`
- Modify: `repo_context_hooks/cli.py`

- [ ] Detect explicit repo signals for each supported platform.
- [ ] Score platforms based on support tier plus detected repo signals.
- [ ] Print ranked recommendations with reasons and exact next commands.

### Task 4: Update docs

**Files:**
- Modify: `README.md`
- Modify: `docs/platforms.md`

- [ ] Add the new commands to the public onboarding flow.
- [ ] Explain the difference between readiness checks and recommendations.
- [ ] Keep the support matrix and claim boundary unchanged.

### Task 5: Verify and publish

**Files:**
- Modify only files from Tasks 1-4

- [ ] Run `python -m pytest -q --basetemp .pytest-tmp-platform-readiness`.
- [ ] Smoke-test `repo-context-hooks doctor --all-platforms` and `repo-context-hooks recommend` against a temp repo.
- [ ] Commit, push, and open a PR once verification is green.
