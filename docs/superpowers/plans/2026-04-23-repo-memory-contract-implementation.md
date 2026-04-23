# Repo Memory Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `specs/README.md` and `UBIQUITOUS_LANGUAGE.md` first-class tracked files, reduce noisy auto-generated repo context metadata, and add regression tests for the repo memory contract.

**Architecture:** Promote the repo memory scaffolding into checked-in docs, then adjust the bundled memory sync script so the top-level repo context index stays stable across worktrees. Protect the behavior with small focused tests instead of relying on manual inspection.

**Tech Stack:** Python, pytest, Markdown docs

---

### Task 1: Add canonical repo memory files

**Files:**
- Create: `UBIQUITOUS_LANGUAGE.md`
- Create: `specs/README.md`
- Modify: `README.md`

- [ ] Replace the generated glossary placeholder with real product vocabulary.
- [ ] Replace the generated engineering-memory placeholder with real `v0.2.0` repo context and next-work guidance.
- [ ] Update `README.md` so the public repo contract explicitly mentions `UBIQUITOUS_LANGUAGE.md`.

### Task 2: Reduce top-level memory sync noise

**Files:**
- Modify: `repo_context_hooks/bundle/scripts/repo_specs_memory.py`
- Modify: `repo_context_hooks/bundle/skills/context-handoff-hooks/scripts/repo_specs_memory.py`

- [ ] Remove branch snapshot and last-commit fields from the top-level auto context block.
- [ ] Keep explicit checkpoint entries unchanged so compact and session-end events still record tactical state.
- [ ] Keep the two bundled script copies in sync.

### Task 3: Add regression tests

**Files:**
- Create: `tests/test_repo_memory_contract.py`
- Modify: `tests/test_readme_contract.py`

- [ ] Add a contract test for tracked repo memory files and required sections.
- [ ] Add a script-behavior test proving `session-start` bootstrap does not inject branch/commit noise into the top-level context block.
- [ ] Extend README contract coverage so the glossary file is treated as part of the public repo contract.

### Task 4: Verify and prepare for publish

**Files:**
- Modify only files from Tasks 1-3

- [ ] Run `python -m pytest -q --basetemp .pytest-tmp-memory-contract`.
- [ ] Review `git diff --stat` and `git status --short` to confirm only intended files changed.
- [ ] Commit with a docs/contract-oriented message once verification is green.
