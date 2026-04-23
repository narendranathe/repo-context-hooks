# Ollama Runtime Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add honest `partial` Ollama support through a repo-owned `Modelfile.repo-context` template and explicit local-model runtime caveats.

**Architecture:** Extend the platform adapter registry with a repo-only Ollama adapter that writes `AGENTS.md` plus `Modelfile.repo-context`. Validate only local files with `doctor`; keep model creation and repo access manual.

**Tech Stack:** Python 3.9+, setuptools CLI package, pytest, Markdown, git

---

## File Map

### Create

- `repo_context_hooks/platforms/ollama.py`
- `repo_context_hooks/bundle/templates/ollama-modelfile`

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

## Task 1: Add Ollama Tests First

- [ ] Add registry tests expecting `ollama`.
- [ ] Add install-plan tests expecting `AGENTS.md` and `Modelfile.repo-context`.
- [ ] Add artifact tests expecting the Modelfile to include `FROM`, `SYSTEM`, `README.md`, `specs/README.md`, and `AGENTS.md`.
- [ ] Add doctor tests for missing, installed, and placeholder Modelfile states.
- [ ] Add installer and CLI tests expecting Ollama manual model-creation steps.
- [ ] Run the focused test slice and confirm it fails because Ollama is not implemented yet.

## Task 2: Implement Ollama Adapter

- [ ] Create `OllamaAdapter` with `partial` tier metadata.
- [ ] Add `ollama-modelfile` template.
- [ ] Reuse the shared `AGENTS.md` template.
- [ ] Add warnings that Ollama is a local model runtime, not a repo-aware lifecycle platform.
- [ ] Add manual steps for editing `FROM`, running `ollama create`, and supplying repo context through an agent wrapper or prompt.
- [ ] Register the adapter.
- [ ] Teach `doctor.py` to validate the Modelfile markers.
- [ ] Run the focused test slice and make it pass.

## Task 3: Update Public Docs And Roadmap

- [ ] Update README quickstart and support wording to include Ollama as `partial`.
- [ ] Update `docs/platforms.md` with the Ollama row and caveat.
- [ ] Update architecture and positioning docs to include local-model template support.
- [ ] Convert Ollama roadmap text from discovery-only to current-support plus follow-up.
- [ ] Keep issue #4 as the follow-up tracker and retitle it if needed.
- [ ] Run docs contract tests.

## Task 4: Full Verification And Publish

- [ ] Run the full test suite with a fresh temp directory.
- [ ] Refresh the editable install.
- [ ] Smoke test:
  - `repo-context-hooks platforms`
  - `repo-context-hooks install --platform ollama`
  - `repo-context-hooks doctor --platform ollama`
- [ ] Commit the Ollama phase in a coherent commit.
- [ ] Push the branch so PR #7 reflects the new platform support.

## Self-Review

- Spec coverage: covered adapter, template, doctor, docs, roadmap, and verification.
- Placeholder scan: no placeholders remain.
- Type consistency: uses the existing adapter terms and repo-only install pattern.
