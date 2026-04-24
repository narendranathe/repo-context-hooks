# Platform Readiness Design

## Problem

`repo-context-hooks` now has a repo-first onboarding flow, but after `init` and repo-wide `doctor`, users still have to manually inspect the platform matrix and infer what to do next. That leaves two gaps:

- no single command shows repo-contract health plus platform readiness across the full support matrix
- no command explains which platform path is the best fit for the current repo and why

## Goals

- Add `repo-context-hooks doctor --all-platforms` to show a concise readiness matrix.
- Add `repo-context-hooks recommend` to suggest the best next setup path for the current repo.
- Keep recommendations transparent and grounded in visible repo signals.
- Keep support claims unchanged.

## Non-Goals

- Auto-install a platform.
- Add new platform adapters in this phase.
- Claim that all supported platforms are equally capable.

## Approaches

### Approach 1: Readiness matrix plus separate recommend command

Add:

- `repo-context-hooks doctor --all-platforms`
- `repo-context-hooks recommend`

Pros:
- clear separation between verification and advice
- easy to keep output compact
- strongest fit for the repo-first onboarding story

Cons:
- one more command to teach

### Approach 2: Put recommendations into `doctor`

Extend `doctor` to both diagnose and suggest next steps.

Pros:
- fewer commands

Cons:
- mixed responsibilities
- harder to keep output scannable

### Approach 3: Recommendation-only

Skip the matrix and only give ranked suggestions.

Pros:
- fastest to implement

Cons:
- hides platform-by-platform state
- weaker debugging value

## Recommendation

Use **Approach 1**.

The matrix answers “what is ready?” The recommendation answers “what should I do next?” Those are related but not identical questions, and separating them keeps both outputs useful.

## Design

### `doctor --all-platforms`

Add an optional flag to the existing doctor command:

```bash
repo-context-hooks doctor --all-platforms
```

Behavior:

- show repo-contract status first
- evaluate every currently supported platform
- print one compact line per platform

Each row should include:

- platform id
- support tier
- overall readiness state
- one concise detail field for the first missing or invalid artifact

The readiness states should be:

- `ready`: no missing or invalid artifacts
- `missing`: one or more required artifacts are absent
- `invalid`: required artifacts exist but fail marker validation

Warnings should stay visible but compact.

### `recommend`

Add:

```bash
repo-context-hooks recommend
```

Behavior:

- inspect repo signals such as:
  - `.claude/settings.json`
  - `.windsurf/rules/`
  - `replit.md`
  - `.lovable/`
  - `SOUL.md`, `USER.md`, `TOOLS.md`
  - `Modelfile.repo-context`
  - `AGENTS.md`
- weight support tier and explicit repo signals
- print the top recommendations with reasons and exact next commands

If the repo contract is missing or invalid, the command should recommend:

1. `repo-context-hooks init`
2. `repo-context-hooks doctor`

before platform-specific actions.

If the repo contract is valid and no platform-specific signals are present, the command should prefer the strongest default path:

1. Claude
2. Cursor or Codex as repo-contract-friendly partial paths

### Transparency

Recommendations must include:

- why the platform ranked where it did
- which repo signals contributed
- the next exact command to run

## Self-Critique

### Critique 1

`doctor --all-platforms` can become noisy if it prints full report bodies for every platform. The safe version is a matrix summary plus concise warning text, not a repeated full doctor block.

### Critique 2

`recommend` will feel arbitrary if it only prints rankings. The reasons and signals need to be explicit so developers can disagree intelligently instead of treating the command like opaque magic.
