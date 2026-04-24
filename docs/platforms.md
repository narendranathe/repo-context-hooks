# Platform Support

`repo-context-hooks` uses three public support tiers:

- `native`: the platform exposes enough lifecycle or automation surface to support the full repo-native continuity loop.
- `partial`: the platform can use the repo contract and continuity docs, but some lifecycle steps stay manual or platform-specific.
- `planned`: the platform is on the roadmap, but not yet implemented as a credible support claim.

## Support Matrix

| Platform | Tier | What works in this phase | What does not | Notes |
| --- | --- | --- | --- | --- |
| Claude | `native` | Repo hooks, bundled skills, session-start through session-end continuity, repo checkpointing | Not a replacement for broader memory tooling | Claude is the reference implementation for the continuity loop. |
| Cursor | `partial` | Repo contract, checked-in instructions, handoff notes, restart-from-repo workflows | no Claude-style hook parity | Cursor can benefit from the same continuity contract even when the lifecycle automation differs. |
| Codex | `partial` | Repo contract, `AGENTS.md`, manual or command-driven resume flows | no native lifecycle hooks and no bundled lifecycle skills | Codex can re-enter with repo context, but it should not be described as hook-equivalent to Claude. |
| Replit | `partial` | Repo contract, `replit.md`, manual resume from the repo root | no native lifecycle hooks or compact automation | Replit Agent reads `replit.md` from the repo root, so the support claim is current partial support rather than roadmap-only. |
| Windsurf | `partial` | Repo contract, root `AGENTS.md`, `.windsurf/rules`, rules-driven restart-from-repo workflows | no native lifecycle hooks or compact automation | Windsurf Cascade treats repo instructions as rule inputs, so the support story is repo-native but rules-driven. |
| Lovable | `partial` | Repo contract, `AGENTS.md`, `.lovable/project-knowledge.md`, `.lovable/workspace-knowledge.md`, manual Project Knowledge and Workspace Knowledge setup | no native lifecycle hooks, no compact automation, and no local verification of hosted UI knowledge | Lovable is a hybrid integration: the repo owns the canonical exports, and the user pastes them into Lovable's UI knowledge fields. |
| OpenClaw | `partial` | Repo contract, `AGENTS.md`, `SOUL.md`, `USER.md`, `TOOLS.md`, manual OpenClaw workspace configuration | no native lifecycle hooks, no compact automation, and no local verification of the active OpenClaw workspace path | OpenClaw is workspace-file-driven: the repo can provide sanitized workspace guidance, but runtime configuration remains manual. |
| Ollama | `partial` | Repo contract, `AGENTS.md`, `Modelfile.repo-context`, manual `ollama create` flow | no repo file access, no native lifecycle hooks, no compact automation, and no local-model runtime verification | Ollama is a model runtime, so this is local-model-template support rather than agent-runtime support. |
| Kimi | `partial` | Repo contract, root `AGENTS.md`, Kimi Code CLI `/init` merge guidance | no generic Kimi API setup, no native lifecycle hooks, and no compact automation | Kimi support is intentionally narrow: it targets Kimi Code CLI project context, not Kimi as a model provider. |

## Claim Boundary

Use the matrix above as the public boundary for support claims:

- do not claim universal agent support
- do not claim hook parity for Cursor or Codex
- do not describe planned platforms as implemented
- do not claim native lifecycle hooks or compact automation on partial platforms unless the platform actually exposes them

For step-by-step post-install guidance, use [docs/platform-playbooks.md](platform-playbooks.md).

## Readiness Commands

Use the platform support matrix with the new CLI surface:

```bash
repo-context-hooks doctor --all-platforms
repo-context-hooks recommend
```

- `doctor --all-platforms` verifies the repo contract first, then prints one compact readiness row per supported platform.
- `recommend` inspects visible repo signals and ranks the strongest next setup paths without auto-installing anything.

These commands are complementary:

- use `doctor --all-platforms` when you want a support-wide verification snapshot
- use `recommend` when you want the shortest credible next step for the current repo

## How To Read The Matrix

A platform can still be valuable at `partial` tier. The product promise is not "every agent exposes the same primitives." The promise is that the repo can remain the continuity boundary even when the automation surface changes.

That is why the current support story is intentionally narrow:

- Claude proves the strongest native path.
- Cursor proves the repo contract matters even without full hook parity.
- Codex proves repo-native continuity still helps when the workflow is driven by checked-in instructions, `AGENTS.md`, and manual resume steps.
- Replit proves the repo contract still matters when the platform reads `replit.md` from the repo root instead of exposing native lifecycle hooks.
- Windsurf proves repo-native continuity also works when a platform consumes root `AGENTS.md` and `.windsurf/rules` through a rules engine instead of hooks.
- Lovable proves the repo can remain canonical even when the platform also requires manual Project Knowledge and Workspace Knowledge in a hosted UI.
- OpenClaw proves repo-native continuity can also map into workspace-loaded Markdown files such as `SOUL.md`, `USER.md`, and `TOOLS.md` without pretending the tool can verify active runtime configuration.
- Ollama proves local-model users can still get a repeatable repo-context prompt through `Modelfile.repo-context`, without claiming Ollama can inspect the repo or manage lifecycle events by itself.
- Kimi proves the repo contract can support Kimi Code CLI project context through root `AGENTS.md`, while keeping generic Kimi API support out of scope.
