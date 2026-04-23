# OpenClaw Adapter Design

Date: 2026-04-22
Status: Proposed
Author: Narendranath Edara

## Summary

This spec defines the next platform phase for `repo-context-hooks`: graduate OpenClaw from planned discovery to current `partial` support by mapping the repo contract into OpenClaw workspace files.

OpenClaw is not a hook-parity platform. Its useful surface is a workspace model where Markdown files such as `AGENTS.md`, `SOUL.md`, `USER.md`, and `TOOLS.md` are loaded as durable agent context. That makes it a credible `partial` integration if we keep the support boundary explicit.

## Verified Platform Surface

OpenClaw documentation describes:

- a single configured agent workspace as the default working directory
- `agents.defaults.workspace` as the configurable workspace path
- `AGENTS.md` as operating instructions loaded at session start
- `SOUL.md` as persona, tone, and boundaries loaded every session
- `USER.md` as user context loaded every session
- `TOOLS.md` as local tool and convention notes

The docs also warn that the workspace is private memory and should avoid secrets. `repo-context-hooks` should therefore install sanitized, repo-safe OpenClaw workspace guidance and avoid personal or credential-bearing content.

## Problem

The current roadmap treats OpenClaw as planned-only even though it exposes a documented, file-based continuity surface. Leaving it planned-only underclaims the product. Overclaiming it as hook-native would weaken trust.

## Goals

- Add a real `OpenClawAdapter` as `partial` support.
- Install repo-safe OpenClaw workspace files:
  - `AGENTS.md`
  - `SOUL.md`
  - `USER.md`
  - `TOOLS.md`
- Keep the repo contract canonical:
  - `README.md`
  - `specs/README.md`
  - `AGENTS.md`
- Print manual steps explaining how to point OpenClaw at the repo root or copy the generated files into the active OpenClaw workspace.
- Extend `doctor` so it validates local OpenClaw files but does not pretend to verify active OpenClaw runtime configuration.
- Update docs and support matrix honestly.

## Non-Goals

- Do not claim native lifecycle hooks.
- Do not claim compact checkpoint automation.
- Do not edit `~/.openclaw/openclaw.json` automatically in this phase.
- Do not write secrets, personal credentials, or private memory into generated files.
- Do not treat Ollama as a platform adapter in this phase.

## Chosen Approach

Tier: `partial`

Install shape:

- `AGENTS.md`
- `SOUL.md`
- `USER.md`
- `TOOLS.md`

Behavior:

- reuse the shared repo `AGENTS.md` contract for operating instructions
- add OpenClaw-specific sanitized context files at the repo root
- warn that OpenClaw workspace activation is manual
- tell the user to either configure OpenClaw's workspace to the repo root or copy the generated files into the active OpenClaw workspace

## Architecture Impact

Add:

- `repo_context_hooks/platforms/openclaw.py`
- `repo_context_hooks/bundle/templates/openclaw-soul.md`
- `repo_context_hooks/bundle/templates/openclaw-user.md`
- `repo_context_hooks/bundle/templates/openclaw-tools.md`

Update:

- `repo_context_hooks/platforms/__init__.py`
- `repo_context_hooks/doctor.py`
- platform registry, install-plan, artifact, doctor, CLI, bundle, README, and docs contract tests
- public docs and roadmap files

## Validation Strategy

`doctor` should validate:

- `AGENTS.md`
- `SOUL.md`
- `USER.md`
- `TOOLS.md`

The OpenClaw files should contain markers that prove they are repo-context files, not placeholders:

- `README.md`
- `specs/README.md`
- `AGENTS.md`
- `repo as the continuity source of truth`

`doctor` should warn that local checks do not verify the active OpenClaw workspace path.

## Documentation Impact

Public docs should say:

- OpenClaw is current `partial` support.
- The integration is workspace-file-driven, not hook-driven.
- The installer writes repo-safe files.
- OpenClaw runtime configuration remains manual.
- OpenClaw support does not imply lifecycle hooks or compact automation.

## Risks

- Adding `SOUL.md`, `USER.md`, and `TOOLS.md` at repo root can surprise users who expect fewer root files.
- OpenClaw workspaces are often private memory; public repos should not include personal details.
- A user could install the files but forget to point OpenClaw at the repo root, then assume support is broken.

## Mitigations

- Keep generated OpenClaw files sanitized and generic.
- Print clear manual steps after install.
- Keep `doctor` honest: validate local repo artifacts only and warn about runtime configuration.
- Explain in docs why this is `partial`, not `native`.

## Self-Critique Pass 1

The first tempting design was to create `.openclaw/workspace/` exports. That would keep root cleaner, but it would also make the project files live outside OpenClaw's active workspace unless the user changed the workspace path to that nested directory. That weakens the actual developer workflow.

The better tradeoff is root workspace files because OpenClaw's workspace is the working directory. The cost is root-file visibility, so the templates must be minimal, sanitized, and clearly tied to the repo contract.

## Self-Critique Pass 2

This phase still does not make OpenClaw "native." It does not configure `~/.openclaw/openclaw.json`, verify the active workspace, or automate lifecycle events. Calling it native would be marketing debt. `partial` is the honest tier because the installer creates useful workspace context, but the user still connects that context to OpenClaw manually.

## Success Criteria

This phase is successful if:

- `repo-context-hooks install --platform openclaw` writes OpenClaw workspace files
- `repo-context-hooks doctor --platform openclaw` validates them correctly
- install output includes manual OpenClaw workspace activation steps
- public docs describe OpenClaw as `partial`
- tests enforce the support tier and local validation boundary
