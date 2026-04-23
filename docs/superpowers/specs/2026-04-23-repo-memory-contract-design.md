# Repo Memory Contract Design

## Problem

`repo-context-hooks` treats `README.md`, `specs/README.md`, and `UBIQUITOUS_LANGUAGE.md` as the core repo contract, but this repository does not currently track the latter two files. As a result, fresh worktrees keep accumulating the same generated memory scaffolding as untracked files. The shipped memory sync script also injects branch-specific metadata into the top-level context block, which makes the file feel like disposable session output instead of canonical repo context.

## Goals

- Track `specs/README.md` and `UBIQUITOUS_LANGUAGE.md` in the repository as canonical files.
- Replace the generic generated memory scaffold with real `repo-context-hooks` project context.
- Remove branch-specific noise from the script-generated repo context index while preserving checkpoint writes for compact and session-end events.
- Add tests that protect the repo memory contract and the bundled sync script behavior.

## Non-Goals

- Redesign the broader hook lifecycle.
- Remove checkpoint logging for `pre-compact`, `post-compact`, or `session-end`.
- Add new platforms or widen support claims.

## Design

### Canonical repo memory files

Add tracked root files:

- `UBIQUITOUS_LANGUAGE.md`
- `specs/README.md`

These should stop being empty bootstrap placeholders and instead describe the actual product:

- the repo-native continuity positioning
- the support-tier model
- the design constraints that keep public claims honest
- what shipped in `v0.2.0`
- what should happen next

### Less noisy auto context block

The auto-generated context block in `repo_specs_memory.py` should stay useful, but it should not include:

- branch snapshot
- last commit

Those values are session-local and worktree-local. They are still appropriate in explicit checkpoint entries, but not in the top-level canonical context index.

### Test coverage

Add tests for:

- the presence and structure of the tracked repo memory files
- the README linking the repo contract files explicitly
- the bundled sync script creating a repo context index without branch/commit noise on `session-start`

## Self-Critique

### Critique 1

If we only track the missing files and leave the bundle script unchanged, we trade untracked noise for noisy tracked diffs. That would look cleaner at first glance but make the repo contract less stable over time.

### Critique 2

If we remove all dynamic metadata, we risk losing useful tactical history. Keeping branch/commit details in explicit checkpoints but not in the top-level context index preserves the operational value without polluting the canonical repo contract.
