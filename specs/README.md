# Engineering Memory

This file is the persistent project context for agents and maintainers.


## Repo Context Index

<!-- AUTO:REPO_CONTEXT_START -->
### Canonical Context Sources

- User-facing overview: `README.md`
- Engineering memory: `specs/README.md`
- Glossary: `UBIQUITOUS_LANGUAGE.md`
- Source of truth: checked-in repo docs, not chat-only summaries

### Repo Summary

- Repo-native continuity for coding agents. `repo-context-hooks` keeps interrupted work, next-step context, and handoff notes in the repository instead of leaving them trapped in chat history. The goal is simple: a new session should be able to reopen the repo, understand the work in progress, and continue without rediscovering everything from scratch.
<!-- AUTO:REPO_CONTEXT_END -->

## Architecture and Design Constraints

- Keep the public claim boundary honest. Claude is the native path; the other shipped platforms are partial integrations with documented caveats.
- Favor repo-native continuity over hosted memory claims. This product should remain inspectable in git and understandable without a separate memory backend.
- Treat `README.md`, `specs/README.md`, and `UBIQUITOUS_LANGUAGE.md` as durable source-of-truth files, not disposable bootstrap output.
- Prefer platform-specific adapters and playbooks over generic “supports every agent” language.

## Built So Far

- `v0.2.0` is live with native Claude support plus partial support for Cursor, Codex, Replit, Windsurf, Lovable, OpenClaw, Ollama, and Kimi.
- The repo ships platform templates, install flows, doctor checks, playbooks, diagrams, and launch docs.
- The support matrix is now backed by tests so README claims, platform docs, and templates stay aligned.

## Design Decisions

- Position the product as repo-native continuity, not as a generic AI memory database.
- Keep the public README outcome-focused and move operator-heavy details into docs and playbooks.
- Model platform support with explicit tiers (`native`, `partial`, `planned`) instead of broad compatibility claims.
- Track compatibility aliases (`repo-context-hooks`, `repohandoff`, `graphify`) while keeping the product language centered on `repo-context-hooks`.

## What Worked

- Tight claim boundaries improved trust: each platform is documented according to its real integration surface.
- Platform-specific adapters plus playbooks made the product more useful without pretending every tool has Claude-style hooks.
- Contract tests on README, docs, templates, and visuals helped keep product positioning and implementation in sync.

## What Failed or Was Reverted

- Overly internal README sections hurt the public GitHub landing page and had to be removed.
- Broad “all agents” wording created avoidable trust gaps because the runtime support was narrower than the marketing language.
- Leaving repo memory files untracked caused repeated worktree noise and made the contract feel optional instead of canonical.

## Open Issues and Next Work

- Keep the repo memory contract canonical and low-noise so future worktrees stop accumulating untracked bootstrap files.
- Continue raising platform quality through real support surfaces, not expanded marketing copy.
- Improve launch assets and public examples only when they stay faithful to the implementation boundary.

## How To Work in This Repo

- Read `README.md` first for user-facing behavior and contribution flow.
- Read this `specs/README.md` before implementation.
- Read `UBIQUITOUS_LANGUAGE.md` before renaming core concepts or adding new public terms.
- Keep support claims narrow unless docs, tests, and install behavior all support widening them.
- Update this file before `compact` and at session end.

## Session Checkpoints

