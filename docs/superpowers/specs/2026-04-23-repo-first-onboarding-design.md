# Repo-First Onboarding Design

## Problem

`repo-context-hooks` is positioned as a repo-native continuity product, but the CLI still starts from platform installation. A new user currently has to infer the right order:

1. understand the repo contract
2. bootstrap the contract files
3. choose a platform
4. validate the result

That means the public product story is stronger than the first-run CLI story.

## Goals

- Add a repo-first onboarding command that bootstraps the canonical repo contract.
- Add a repo-wide diagnostic path that validates the repo contract before platform-specific setup.
- Keep platform-specific installation and diagnosis intact.
- Make the docs reflect the new onboarding sequence.

## Non-Goals

- Redesign the platform adapter model.
- Add new platforms in this phase.
- Auto-detect and install every possible platform.

## Approaches

### Approach 1: Repo-first onboarding layer

Add a new `init` command and make `doctor` work without a platform argument.

Pros:
- strongest alignment with the product USP
- low-risk CLI expansion
- improves first-run experience without destabilizing platform adapters

Cons:
- adds one more command to maintain

### Approach 2: Make `install` do everything

Keep a single install command and overload it to bootstrap the repo contract plus platform setup.

Pros:
- fewer commands

Cons:
- weak separation between repo setup and platform setup
- harder to explain and harder to verify

### Approach 3: Docs-only onboarding

Leave the CLI alone and rely on README/playbooks to teach the order of operations.

Pros:
- smallest code change

Cons:
- leaves the product gap in place
- does not make the repo-first story operational

## Recommendation

Use **Approach 1**.

The product promise is repo-native continuity, so the CLI should let users set up the repo contract before they think about adapter choice. Platform installation should become step 2, not step 1.

## Design

### `repo-context-hooks init`

Add a new top-level CLI command:

```bash
repo-context-hooks init
```

Behavior:

- create `README.md` if missing
- create or normalize `specs/README.md`
- create or normalize `UBIQUITOUS_LANGUAGE.md`
- create `AGENTS.md` if missing
- avoid overwriting existing user-authored files unless `--force` is passed

This command should use the same bundle templates and repo-memory bootstrap logic already used elsewhere, but without requiring a Claude-specific hooks install.

### Repo-wide `doctor`

Add a repo-contract diagnosis path:

```bash
repo-context-hooks doctor
```

Behavior:

- validate `README.md`
- validate `specs/README.md`
- validate `UBIQUITOUS_LANGUAGE.md`
- warn if `AGENTS.md` is missing
- return nonzero if the core repo contract is missing or invalid

Platform-specific doctor remains:

```bash
repo-context-hooks doctor --platform claude
```

### Docs and quickstart

Update the README quickstart so the onboarding path is:

1. `repo-context-hooks init`
2. `repo-context-hooks doctor`
3. `repo-context-hooks install --platform <platform>`

## Self-Critique

### Critique 1

If `init` becomes too aggressive about modifying `README.md`, it will feel like a template generator rather than a continuity tool. This phase should keep `README.md` creation minimal and only fill it in when missing.

### Critique 2

If repo-wide `doctor` tries to infer and validate every platform automatically, it will become noisy and unpredictable. It should stay focused on the repo contract, with platform checks remaining explicit.
