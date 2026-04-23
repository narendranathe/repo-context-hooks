# Ollama Runtime Template Design

Date: 2026-04-22
Status: Proposed
Author: Narendranath Edara

## Summary

This spec defines an honest Ollama integration for `repo-context-hooks`: add `partial` support through a repo-owned `Modelfile.repo-context` template, not fake agent lifecycle hooks.

Ollama is a model runtime. Its documented customization surface is a `Modelfile` with instructions such as `FROM`, `PARAMETER`, and `SYSTEM`, plus an API for running model prompts. It does not, by itself, provide a repo-aware coding agent, file-reading lifecycle, compact hooks, or handoff automation.

That means the useful support claim is narrow:

- generate a repo-context-aware `Modelfile.repo-context`
- install `AGENTS.md`
- tell developers how to create a local model from the Modelfile
- warn that direct `ollama run` cannot read the repo unless an agent wrapper or user prompt provides the files

## Verified Platform Surface

Official Ollama docs describe:

- `Modelfile` as the blueprint for customized models
- `FROM` as the required base-model instruction
- `PARAMETER` for runtime settings such as context window size
- `SYSTEM` for the system message used by the model
- `ollama create <name> -f <Modelfile>` as the way to build the customized model
- the Ollama API as a model interaction API, not an agent lifecycle or repo instruction system

## Problem

The roadmap currently treats Ollama as planned because it is unclear whether it should be an adapter, template pack, or docs-only workflow.

If we implement an adapter that claims lifecycle continuity, we overclaim. If we leave Ollama planned-only, we miss a useful developer workflow: local model users still need a repeatable repo-context prompt that points back to `README.md`, `specs/README.md`, and `AGENTS.md`.

## Goals

- Add an `OllamaAdapter` as `partial` support.
- Install:
  - `AGENTS.md`
  - `Modelfile.repo-context`
- Include manual steps:
  - edit the `FROM` line if the user prefers a different local model
  - run `ollama create repo-context-helper -f Modelfile.repo-context`
  - use the resulting model through an agent wrapper or paste repo context manually when using direct `ollama run`
- Extend `doctor` to validate the local Modelfile.
- Update docs without calling Ollama an agent runtime.

## Non-Goals

- Do not claim Ollama reads repo files automatically.
- Do not claim native lifecycle hooks.
- Do not claim compact checkpoint automation.
- Do not install or run Ollama.
- Do not choose the user's production model stack.
- Do not call this support equivalent to Claude, Cursor, Replit, Windsurf, Lovable, or OpenClaw.

## Chosen Approach

Tier: `partial`

Install shape:

- `AGENTS.md`
- `Modelfile.repo-context`

Behavior:

- create a runnable default `Modelfile.repo-context` using `FROM llama3.2`
- set a larger context window with `PARAMETER num_ctx 8192`
- use `SYSTEM` to carry the repo continuity contract into a local model
- make direct-runtime limitations visible in warnings and docs

## Architecture Impact

Add:

- `repo_context_hooks/platforms/ollama.py`
- `repo_context_hooks/bundle/templates/ollama-modelfile`

Update:

- `repo_context_hooks/platforms/__init__.py`
- `repo_context_hooks/doctor.py`
- platform registry, install-plan, artifact, doctor, CLI, bundle, README, and docs contract tests
- public docs and roadmap files

## Validation Strategy

`doctor` should validate:

- `AGENTS.md`
- `Modelfile.repo-context`

The Modelfile should contain markers:

- `FROM`
- `SYSTEM`
- `README.md`
- `specs/README.md`
- `AGENTS.md`
- `repo as the continuity source of truth`

`doctor` should warn that Ollama cannot verify repo access or lifecycle automation locally.

## Self-Critique Pass 1

The risky version of this feature is pretending Ollama is an agent platform. It is not. A local model runtime can carry a system prompt, but it cannot independently inspect the repo, update `specs/README.md`, or handle compact events unless another wrapper supplies those capabilities.

The feature is still worth shipping if we call it what it is: a repo-context model template for local-model workflows.

## Self-Critique Pass 2

Hardcoding `FROM llama3.2` is imperfect because developers may prefer a different installed local model. A CLI option such as `--ollama-base-model` would be cleaner, but the current installer architecture does not support platform-specific options. The pragmatic Phase 1 choice is to generate a working default and tell developers to edit the `FROM` line.

## Success Criteria

This phase is successful if:

- `repo-context-hooks install --platform ollama` writes `Modelfile.repo-context`
- `repo-context-hooks doctor --platform ollama` validates it
- public docs describe Ollama as local-model-template `partial` support
- docs explicitly say Ollama is not hook-native and does not read repo files automatically
- tests protect the support boundary
