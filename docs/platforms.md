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
| Lovable | `planned` | Roadmap only | not implemented | Candidate issue seed in `docs/launch/platform-roadmap.md`. |
| Ollama | `planned` | Roadmap only | not implemented | Candidate issue seed in `docs/launch/platform-roadmap.md`. |
| OpenClaw | `planned` | Roadmap only | not implemented | Candidate issue seed in `docs/launch/platform-roadmap.md`. |
| Kimi | `planned` | Roadmap only | not implemented | Candidate issue seed in `docs/launch/platform-roadmap.md`. |

## Claim Boundary

Use the matrix above as the public boundary for support claims:

- do not claim universal agent support
- do not claim hook parity for Cursor or Codex
- do not describe planned platforms as implemented
- do not claim native lifecycle hooks or compact automation on partial platforms unless the platform actually exposes them

## How To Read The Matrix

A platform can still be valuable at `partial` tier. The product promise is not "every agent exposes the same primitives." The promise is that the repo can remain the continuity boundary even when the automation surface changes.

That is why the current support story is intentionally narrow:

- Claude proves the strongest native path.
- Cursor proves the repo contract matters even without full hook parity.
- Codex proves repo-native continuity still helps when the workflow is driven by checked-in instructions, `AGENTS.md`, and manual resume steps.
- Replit proves the repo contract still matters when the platform reads `replit.md` from the repo root instead of exposing native lifecycle hooks.
