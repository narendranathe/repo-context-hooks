# README Install Flow and JSON Output Design

## Problem

The README made the platform install step look like a sequence of commands to run all at once. That is not how users adopt the tool: they initialize the repo once, inspect readiness, then choose the one platform they actually use.

The public README also linked directly to deeper operator docs such as platform playbooks. Those docs can remain useful for maintainers, but they should not be part of the first GitHub landing path.

Finally, the new readiness commands are still human-readable only. Agent wrappers, CI jobs, and shell scripts need structured output if this project is going to be useful as a building block.

## Goals

- Make the README onboarding path easy to scan and copy.
- Split platform install commands by platform.
- Remove internal-heavy docs from the README primary link path.
- Add `--json` output for:
  - `platforms`
  - `doctor`
  - `doctor --all-platforms`
  - `recommend`

## Non-Goals

- Add new platform adapters.
- Change support tiers.
- Remove maintainer docs from the repository.
- Add JSON output to `install` in this phase.

## Design

The README should show the workflow as:

1. install the package
2. initialize the repo contract
3. run doctor/readiness/recommendation checks
4. choose one platform-specific install command

The CLI should keep human-readable output as the default and add `--json` as an opt-in flag. The JSON contract should use stable field names based on the existing model objects:

- `DoctorReport.to_dict()`
- `AllPlatformsReport.to_dict()`
- `RecommendationReport.to_dict()`
- platform registry metadata for `platforms --json`

## Self-Critique

This is intentionally a small JSON contract. It does not try to become a full schema registry yet. That keeps the change easy to review and avoids prematurely freezing fields that future users may not need.

The README still links to `docs/platforms.md`, which is public and detailed. That is appropriate because support claims should stay easy to audit. The deeper playbook and positioning docs should not be pushed from the landing page.
