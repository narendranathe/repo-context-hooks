# Competitive Analysis

## Adjacent Projects

### `thedotmack/claude-mem`

- Focus: session capture, compression, and retrieval
- Difference: stronger on memory archive behavior than repo-operating workflow

### `mem0ai/mem0` and OpenMemory

- Focus: long-term memory infrastructure
- Difference: stronger on cross-session memory systems than repo-local hook workflows

### Claude Code Hooks

- Focus: lifecycle primitives provided by the platform
- Difference: capability only, not a packaged workflow

## Honest Take

This project is not novel because hooks exist or because memory tools exist.

Its value is packaging the workflow many teams actually need:

- load project state on session start
- checkpoint tactical context before compact
- restore continuity after compact
- keep the source of truth in the repo

## Positioning Rule

Describe `repo-context-hooks` as a deterministic repo workflow, not as a universal memory solution.
