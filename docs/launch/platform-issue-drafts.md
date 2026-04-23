# Platform Issue Drafts

These issue bodies were used to create the initial planned-platform backlog. They remain here as editable source text for future issue revisions.

Replit has since graduated to current partial support via `replit.md`, so its draft below should be read as follow-up notes rather than roadmap-only discovery.

Windsurf has also graduated to current partial support via root `AGENTS.md` and `.windsurf/rules`, so it no longer belongs in roadmap-only discovery.

Lovable has also graduated to current partial support via repo-owned Project Knowledge and Workspace Knowledge exports, so its draft below should be read as follow-up notes rather than roadmap-only discovery.

OpenClaw has also graduated to current partial support via repo-root workspace files, so its draft below should be read as follow-up notes rather than roadmap-only discovery.

Ollama has also graduated to current partial support via `Modelfile.repo-context`, so its draft below should be read as follow-up notes rather than roadmap-only discovery.

Kimi has also graduated to current partial support via root `AGENTS.md` for Kimi Code CLI workflows, so its draft below should be read as follow-up notes rather than roadmap-only discovery.

Created issues:

- Replit: [#2](https://github.com/narendranathe/repo-context-hooks/issues/2)
- Windsurf: [#8](https://github.com/narendranathe/repo-context-hooks/issues/8)
- Lovable: [#3](https://github.com/narendranathe/repo-context-hooks/issues/3)
- Ollama: [#4](https://github.com/narendranathe/repo-context-hooks/issues/4)
- OpenClaw: [#5](https://github.com/narendranathe/repo-context-hooks/issues/5)
- Kimi: [#6](https://github.com/narendranathe/repo-context-hooks/issues/6)

## Platform: Replit partial-support notes

```md
## Summary
Replit now has current partial support via `replit.md`, which gives the agent a checked-in repo-root continuity surface without claiming Claude-style lifecycle parity.

## Continuity Surface To Evaluate
- root-level `replit.md`
- repo-visible contract files (`README.md`, `specs/README.md`, `AGENTS.md`)
- manual restart-from-repo workflows after agent interruption

## Tier
Partial support, with no claim of native lifecycle hooks.

## Acceptance Criteria
- Keep `replit.md` concise and repo-contract-focused.
- Keep the public claim boundary honest: no native lifecycle hooks, no compact automation parity.
- Preserve issue #2 as a follow-up tracker for incremental improvements rather than discovery.

## Open Questions
- Which repo-root guidance is most useful inside `replit.md`?
- What future automation, if any, is actually exposed by Replit beyond the checked-in contract?
- Which follow-up improvements belong in the issue thread versus the docs?
```

## Platform: Windsurf partial-support notes

```md
## Summary
Windsurf now has current partial support through root `AGENTS.md`, `.windsurf/rules/repo-context-continuity.md`, and the repo contract.

## Continuity Surface To Evaluate
- root `AGENTS.md`
- `.windsurf/rules/repo-context-continuity.md`
- rules-driven restart-from-repo workflows

## Tier
Partial support, with no claim of native lifecycle hooks.

## Acceptance Criteria
- Keep the Windsurf rule concise and repo-contract-focused.
- Explain how root `AGENTS.md` and `.windsurf/rules` work together without duplicating each other.
- Keep the public claim boundary honest: no native lifecycle hooks and no compact automation parity.
- Preserve issue #8 as a follow-up tracker for incremental improvements rather than discovery.

## Open Questions
- Which Windsurf-specific rule composition examples are useful enough to document?
- Should future docs explain personal rules versus workspace rules?
- What future official Windsurf surface, if any, could make this stronger than partial support?
```

## Platform: Lovable partial-support notes

```md
## Summary
Lovable now has current partial support through repo-owned Project Knowledge and Workspace Knowledge exports, plus `AGENTS.md` inside the synced repository.

## Continuity Surface To Evaluate
- GitHub sync on the default branch
- checked-in continuity contract files
- manual Project Knowledge and Workspace Knowledge paste steps in the Lovable UI

## Tier
Partial support, with no claim of native lifecycle hooks.

## Acceptance Criteria
- Keep `.lovable/project-knowledge.md` and `.lovable/workspace-knowledge.md` as canonical repo-owned exports.
- Keep the public claim boundary honest: no native lifecycle hooks, no compact automation parity, and no claim that hosted UI state is verified locally.
- Preserve issue #3 as a follow-up tracker for incremental improvements rather than discovery.

## Open Questions
- What additional repo-owned exports would help users keep Lovable project knowledge aligned with their repo?
- Which manual Lovable UI steps are worth automating later, if Lovable ever exposes them?
- How should future docs distinguish hybrid repo-plus-UI knowledge from fully repo-consumed platforms?
```

## Platform: Ollama partial-support notes

```md
## Summary
Ollama now has current partial support through `AGENTS.md`, `Modelfile.repo-context`, and a manual `ollama create` flow.

## Continuity Surface To Evaluate
- Ollama `Modelfile`
- checked-in repo contract files
- agent wrappers or manual prompts that can supply repo file contents

## Tier
Partial support, with no claim of native lifecycle hooks.

## Acceptance Criteria
- Keep `Modelfile.repo-context` focused on the repo contract and local-model limitations.
- Keep public claims honest: no native lifecycle hooks, no compact automation, and no claim that Ollama reads repo files automatically.
- Preserve issue #4 as a follow-up tracker for incremental improvements rather than discovery.

## Open Questions
- Should a later phase add platform-specific CLI options such as `--ollama-base-model`?
- Should we add examples for common local-agent wrappers that call Ollama?
- What minimum smoke test is safe without requiring Ollama to be installed in CI?
```

## Platform: OpenClaw partial-support notes

```md
## Summary
OpenClaw now has current partial support through repo-root `AGENTS.md`, `SOUL.md`, `USER.md`, and `TOOLS.md` workspace files.

## Continuity Surface To Evaluate
- configured OpenClaw workspace path
- repo-root workspace files
- handoff/resume behavior grounded in `README.md`, `specs/README.md`, and `AGENTS.md`

## Tier
Partial support, with no claim of native lifecycle hooks.

## Acceptance Criteria
- Keep `SOUL.md`, `USER.md`, and `TOOLS.md` sanitized and repo-safe.
- Keep public claims honest: no native lifecycle hooks, no compact automation parity, and no local verification of active OpenClaw runtime configuration.
- Preserve issue #5 as a follow-up tracker for incremental improvements rather than discovery.

## Open Questions
- Should future automation edit `~/.openclaw/openclaw.json`, or should runtime configuration stay manual?
- Which workspace-file examples help developers without encouraging secrets in public repos?
- Should a later phase support private OpenClaw memory repos separately from public project repos?
```

## Platform: Kimi partial-support notes

```md
## Summary
Kimi now has current partial support through root `AGENTS.md` for Kimi Code CLI workflows.

## Continuity Surface To Evaluate
- Kimi Code CLI `/init`
- root `AGENTS.md`
- repo-visible continuity contract files

## Tier
Partial support, with no claim of native lifecycle hooks.

## Acceptance Criteria
- Keep Kimi support scoped to Kimi Code CLI project context.
- Keep generic Kimi API configuration out of scope.
- Preserve issue #6 as a follow-up tracker for incremental improvements rather than discovery.

## Open Questions
- Does Kimi Code publish a stable rules-file path that could make this stronger than `AGENTS.md`-only support?
- Should future docs include a Kimi Code `/init` merge example?
- What minimum smoke test is safe without requiring Kimi Code CLI to be installed in CI?
```
