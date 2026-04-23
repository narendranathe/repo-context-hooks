# Platform Issue Drafts

These issue bodies were used to create the initial planned-platform backlog. They remain here as editable source text for future issue revisions.

Replit has since graduated to current partial support via `replit.md`, so its draft below should be read as follow-up notes rather than roadmap-only discovery.

Created issues:

- Replit: [#2](https://github.com/narendranathe/repo-context-hooks/issues/2)
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

## Platform: Lovable adapter discovery

```md
## Summary
Investigate a credible Lovable adapter strategy that keeps repo-native continuity reviewable even when orchestration happens through a hosted builder workflow.

## Continuity Surface To Evaluate
- GitHub sync workflow
- checked-in continuity contract files
- how Lovable can consume or preserve repo guidance during regenerate/edit loops

## Tier
Provisional until the exposed continuity surface is verified.

## Acceptance Criteria
- Identify which repo files Lovable can reliably use as continuity inputs.
- Decide whether an adapter is honest or whether this should remain roadmap-only.
- Define the minimum useful workflow that preserves the repo as the source of truth.
- Document claims that must stay out of the public README until this is real.

## Open Questions
- How much continuity can remain repo-native when orchestration is product-hosted?
- Can GitHub sync preserve `AGENTS.md` and `specs/README.md` as active continuity surfaces?
- Is the right output an adapter, a template export, or docs-only guidance?
```

## Platform: Ollama adapter strategy

```md
## Summary
Investigate how `repo-context-hooks` should support local-model workflows around Ollama without overcommitting on automation.

## Continuity Surface To Evaluate
- local runtime workflows
- checked-in repo contract files
- templates or helper commands for restart-from-repo continuity

## Tier
Provisional until the exposed continuity surface is verified.

## Acceptance Criteria
- Define whether Ollama support is an adapter, template pack, or docs-only workflow.
- Decide the honest support tier after evaluating actual install and runtime surfaces.
- Identify what continuity can be automated and what remains manual.
- Document unsupported claims clearly.

## Open Questions
- What is the right install surface for local-model setups that do not expose agent lifecycle hooks?
- Should Ollama support target generic local-agent wrappers instead of Ollama directly?
- How do we keep the repo as the continuity boundary without pretending there is a native hook model?
```

## Platform: OpenClaw adapter strategy

```md
## Summary
Investigate whether OpenClaw exposes a credible continuity surface for `repo-context-hooks` beyond a naming-level integration.

## Continuity Surface To Evaluate
- orchestration model
- checked-in instruction files
- handoff/resume behavior grounded in repo state

## Tier
Provisional until the exposed continuity surface is verified.

## Acceptance Criteria
- Identify the actual instruction and continuity surfaces OpenClaw exposes.
- Decide whether an adapter is honest or whether this stays in discovery.
- Define what a minimum useful integration would look like.
- Record the README claims that must remain out-of-bounds.

## Open Questions
- Does OpenClaw have a stable repo-facing instruction model?
- Can it consume `README.md`, `specs/README.md`, and `AGENTS.md` in a meaningful way?
- Is the right scope a platform adapter, a compatibility note, or no integration at all?
```

## Platform: Kimi adapter discovery

```md
## Summary
Investigate whether Kimi exposes enough coding-workflow surface to support repo-native continuity honestly.

## Continuity Surface To Evaluate
- instruction surfaces for coding workflows
- repo-visible continuity contract files
- handoff and restart behavior after interruption

## Tier
Provisional until the exposed continuity surface is verified.

## Acceptance Criteria
- Identify what Kimi actually exposes for repo or session continuity.
- Decide the honest support tier after the workflow surface is verified.
- Define what could be automated and what would remain manual.
- Document claims that must stay out of the public README until this is proven.

## Open Questions
- Does Kimi expose repo-facing instruction or session surfaces suitable for continuity?
- Is the right outcome an adapter, guidance doc, or continued roadmap-only status?
- What would a minimum credible integration look like?
```
